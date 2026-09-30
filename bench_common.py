"""Helpers shared by the full-length benchmark banks.

Math questions are generated from templates: every answer is computed, never
typed, and every template can be re-run with a new seed for fresh numbers.
Reading and writing questions are hand-authored with the correct choice first;
the bank shuffles them deterministically.
"""
import random
import re
from fractions import Fraction

SUP = {2: '²', 3: '³', 4: '⁴'}


class Retry(Exception):
    """A generator raises this when its random numbers make a poor question."""


def num(v):
    if isinstance(v, Fraction):
        if v.denominator == 1:
            v = v.numerator
        else:
            return ('−' if v < 0 else '') + f'{abs(v.numerator)}/{v.denominator}'
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            v = int(round(v))
        else:
            return ('−' if v < 0 else '') + f'{abs(v):.4f}'.rstrip('0').rstrip('.')
    return str(v).replace('-', '−')


def txt(v):
    return v if isinstance(v, str) else num(v)


def money(v):
    return f'${float(v):,.2f}'


def poly(cs, var='x'):
    """Format {power: coefficient} as a readable polynomial."""
    out = ''
    for p in sorted(cs, reverse=True):
        c = cs[p]
        if c == 0:
            continue
        a = abs(c)
        if p == 0:
            body = num(a)
        else:
            body = ('' if a == 1 else num(a)) + var + SUP.get(p, '' if p == 1 else f'^{p}')
        if not out:
            out = ('−' if c < 0 else '') + body
        else:
            out += (' − ' if c < 0 else ' + ') + body
    return out or '0'


def sub(var, v):
    """'x − 3' or 'x + 3' without a doubled sign."""
    return f'{var} − {num(v)}' if v >= 0 else f'{var} + {num(-v)}'


def fac(a, b, var='x'):
    return '(' + poly({1: a, 0: b}, var) + ')'


def pi_form(v):
    """Format a rational multiple of π."""
    v = Fraction(v)
    lead = '' if v.numerator == 1 else str(v.numerator)
    return f'{lead}π' if v.denominator == 1 else f'{lead}π/{v.denominator}'


def spec(question, correct, wrong, why, hints, *, source='', sub=None):
    """Bundle one generated question. `wrong` is [(value, misconception), ...]."""
    options, notes = [txt(correct)], ['']
    for value, note in wrong:
        shown = txt(value)
        if shown not in options:
            options.append(shown)
            notes.append(note)
        if len(options) == 4:
            break
    if len(options) != 4:
        raise Retry
    return {'question': question, 'source': source, 'options': options, 'why': why,
            'hints': hints, 'misconceptions': notes, 'sub': sub}


def register(registry, module, skill, difficulty, sub=None):
    def decorate(fn):
        registry.append({'id': len(registry) + 1, 'fn': fn, 'module': module, 'skill': skill,
                         'difficulty': difficulty, 'sub': sub or skill})
        return fn
    return decorate


def tidy(text):
    """Write 'a − −b' as 'a + b' and 'a + −b' as 'a − b'."""
    return text.replace(' − −', ' + ').replace(' + −', ' − ') if isinstance(text, str) else text


def realize(entry, seed):
    for attempt in range(80):
        rng = random.Random(seed * 7919 + attempt * 104729 + entry['id'] * 31)
        try:
            built = entry['fn'](rng)
            break
        except Retry:
            continue
    else:
        raise RuntimeError(f"Could not build benchmark template {entry['fn'].__name__} ({entry['skill']})")
    hints = built['hints']
    built['why'] = tidy(built['why'])
    built['question'] = tidy(built['question'])
    built['source'] = tidy(built['source'])
    built['options'] = [tidy(o) for o in built['options']]
    return {'skill_key': entry['skill'], 'subskill': built['sub'] or entry['sub'], 'difficulty': entry['difficulty'],
            'module': entry['module'], 'question_text': built['question'], 'source_or_prompt': built['source'],
            'options': built['options'], 'correct_option': 0, 'explanation': built['why'],
            'hints': hints, 'strategy': hints[1], 'fastest_method': hints[2],
            'misconceptions': built['misconceptions'], 'validation': 'reviewed_bank'}


def words(text):
    return len(re.findall(r"[A-Za-z0-9$%'’\-]+", text or ''))
