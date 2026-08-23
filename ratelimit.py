"""Fixed-window rate limiting that survives serverless cold starts.

Vercel gives every request its own process, so an in-process counter would reset
constantly and enforce nothing. Counters therefore live in the same database the
rest of the app uses, keyed by (rule, caller, window). An in-process dictionary
is kept only as a degraded fallback for when the database is unreachable, so a
transient outage cannot turn a limited endpoint into an unlimited one.
"""

import re
import threading
import time
from collections import defaultdict
from functools import wraps

from flask import g, jsonify, request, session

_PERIODS = {
    'second': 1,
    'minute': 60,
    'hour': 3600,
    'day': 86400,
}

_RULE_PATTERN = re.compile(r'^\s*(\d+)\s*(?:/|\s+per\s+)\s*(\d*)\s*(second|minute|hour|day)s?\s*$', re.I)

# Fallback store used only when the database errors. Bounded so a hostile caller
# cannot grow it without limit.
_MEMORY_LOCK = threading.Lock()
_MEMORY_HITS = defaultdict(int)
_MEMORY_MAX_KEYS = 20000

_db = None
_enabled = True
_table_ready = False


def init_app(app, database, *, enabled=True):
    """Wire the limiter to the app's database handler."""
    global _db, _enabled
    _db = database
    _enabled = enabled
    app.extensions.setdefault('ratelimit', {})['db'] = database


def ensure_table(database=None):
    """Create the counter table. Safe to call repeatedly."""
    global _table_ready
    target = database or _db
    if target is None:
        return
    target.create_table('rate_limits', {
        'bucket': 'TEXT PRIMARY KEY',
        'window_start': 'BIGINT NOT NULL',
        'hits': 'INTEGER NOT NULL',
    })
    _table_ready = True


def parse_rule(rule):
    """'5/minute' or '30 per 10 minutes' -> (limit, window_seconds)."""
    match = _RULE_PATTERN.match(str(rule))
    if not match:
        raise ValueError(f'Unparseable rate limit rule: {rule!r}')
    limit, multiple, period = match.groups()
    window = _PERIODS[period.lower()] * int(multiple or 1)
    return int(limit), window


def caller_identity():
    """Identify the caller: the account when signed in, otherwise the client IP.

    Keying authenticated traffic by user id means one account cannot multiply its
    allowance by rotating IPs, and shared-NAT users are not punished for each
    other's usage.
    """
    user_id = session.get('user_id')
    if user_id:
        return f'u{user_id}'
    # ProxyFix has already resolved X-Forwarded-For into remote_addr.
    return f'ip{request.remote_addr or "unknown"}'


def _memory_hit(bucket, window_start, window):
    with _MEMORY_LOCK:
        if len(_MEMORY_HITS) > _MEMORY_MAX_KEYS:
            cutoff = window_start - window
            for key in [k for k in _MEMORY_HITS if k[1] < cutoff]:
                del _MEMORY_HITS[key]
            if len(_MEMORY_HITS) > _MEMORY_MAX_KEYS:
                _MEMORY_HITS.clear()
        key = (bucket, window_start)
        _MEMORY_HITS[key] += 1
        return _MEMORY_HITS[key]


def _record_hit(bucket, window_start, window):
    """Atomically increment and read the counter for this bucket."""
    if _db is None:
        return _memory_hit(bucket, window_start, window)
    try:
        if not _table_ready:
            ensure_table()
        row = _db.execute_returning_one(
            'INSERT INTO rate_limits (bucket, window_start, hits) VALUES (?, ?, 1) '
            'ON CONFLICT (bucket) DO UPDATE SET hits = rate_limits.hits + 1 '
            'RETURNING hits',
            (bucket, window_start),
        )
        if row and row.get('hits') is not None:
            return int(row['hits'])
        return _memory_hit(bucket, window_start, window)
    except Exception:
        # Never let limiter infrastructure take down a working endpoint, but do
        # keep counting in-process so the limit still bites within this worker.
        return _memory_hit(bucket, window_start, window)


def sweep(older_than_seconds=86400, probability_denominator=200):
    """Occasionally drop expired counter rows so the table stays small."""
    if _db is None:
        return
    # Cheap deterministic sampling: only sweep on ~1 in N requests.
    if int(time.time() * 1000) % probability_denominator:
        return
    try:
        _db.execute_write(
            'DELETE FROM rate_limits WHERE window_start < ?',
            (int(time.time()) - older_than_seconds,),
        )
    except Exception:
        pass


def check(rule, *, key=None, name=None, cost=1):
    """Consume `cost` from a bucket. Returns (allowed, retry_after_seconds)."""
    if not _enabled:
        return True, 0
    limit, window = parse_rule(rule)
    identity = key or caller_identity()
    label = name or 'default'
    now = int(time.time())
    window_start = now - (now % window)
    bucket = f'{label}:{identity}:{window_start}'

    hits = 0
    for _ in range(max(1, cost)):
        hits = _record_hit(bucket, window_start, window)
    retry_after = max(1, (window_start + window) - now)
    return hits <= limit, retry_after


def rate_limit(rule, *, name=None, key=None, cost=1, message=None, methods=None):
    """Decorator enforcing `rule` on a view.

    Applied below @login_required so the session is already resolved and the
    bucket can be keyed by account rather than by IP.

    `methods` restricts enforcement to specific HTTP verbs. Routes that serve a
    form on GET and process it on POST must pass methods={'POST'}, otherwise
    merely opening the page repeatedly would exhaust the allowance.
    """
    limit, window = parse_rule(rule)
    limited_methods = {m.upper() for m in methods} if methods else None

    def decorator(view):
        label = name or view.__name__

        def wrapper(*args, **kwargs):
            if limited_methods is not None and request.method.upper() not in limited_methods:
                return view(*args, **kwargs)
            identity = key() if callable(key) else key
            allowed, retry_after = check(rule, key=identity, name=label, cost=cost)
            sweep()
            if allowed:
                g.rate_limit_rule = (limit, window)
                return view(*args, **kwargs)
            return too_many(retry_after, message)

        return wraps(view)(wrapper)

    return decorator


def too_many(retry_after, message=None):
    """Build the 429 response for a caller that exceeded its allowance."""
    text = message or 'Too many requests. Please wait a moment and try again.'
    wants_json = (
        request.path.startswith('/api/')
        or request.accept_mimetypes.best == 'application/json'
        or request.is_json
    )
    if wants_json:
        response = jsonify({'error': text, 'retry_after': retry_after})
    else:
        response = _plain(text, retry_after)
    response.status_code = 429
    response.headers['Retry-After'] = str(retry_after)
    return response


def _plain(text, retry_after):
    from flask import make_response
    body = (
        '<!doctype html><meta charset="utf-8"><title>Slow down</title>'
        '<style>body{font:16px/1.6 system-ui,sans-serif;max-width:34rem;margin:18vh auto;padding:0 6vw;color:#1f2937}'
        'h1{font-size:1.4rem;letter-spacing:-.02em}a{color:#6d38c6}</style>'
        f'<h1>Slow down for a moment</h1><p>{text}</p>'
        f'<p>Try again in about {retry_after} second(s). <a href="/">Return to Mentics</a></p>'
    )
    return make_response(body)
