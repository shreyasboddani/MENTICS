# Deployment

## Environment variables

### Required in production
| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Session signing. The app refuses to boot in production without it. |
| `DATABASE_URL` | Postgres connection string. The app refuses to boot in production without it, because local SQLite is not persistent on serverless. |

### Recommended
| Variable | Default | Purpose |
| --- | --- | --- |
| `PUBLIC_APP_URL` | `https://mentics.vercel.app` | Canonical origin. Used for `<link rel="canonical">`, `sitemap.xml`, and Open Graph URLs. Set this to your real domain so preview deployments never compete with production in search. |
| `GOOGLE_SITE_VERIFICATION` | *(unset)* | Paste the token from Google Search Console → *Verify ownership → HTML tag*. Renders as `<meta name="google-site-verification">`. |
| `GEMINI_API_KEY` | *(unset)* | AI coaching, essay feedback, and path generation. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | *(unset)* | Google sign-in. |

### Operator-only
| Variable | Default | Purpose |
| --- | --- | --- |
| `IMPORT_API_TOKEN` | *(unset)* | Enables `POST /api/import_official_questions`. **While unset the endpoint returns 404 and cannot write anything.** Only set it when you are actively importing, and send it as the `X-Import-Token` header. Use a long random value (`python -c "import secrets;print(secrets.token_urlsafe(32))"`). |

### Rate limits
Counters live in the `rate_limits` table so they hold across serverless
invocations. Overriding these is rarely necessary.

| Variable | Default |
| --- | --- |
| `RATE_LIMIT_WRITES` | `120/minute` — ceiling on all state-changing requests per caller |
| `RATE_LIMIT_LOGIN_IP` | `10/minute` |
| `RATE_LIMIT_LOGIN_IP_HOURLY` | `50/hour` |
| `RATE_LIMIT_LOGIN_ACCOUNT` | `8/hour` — per target account, which is what stops credential stuffing across rotating IPs |
| `RATE_LIMIT_SIGNUP` | `5/hour` |
| `RATE_LIMITS_ENABLED` | `1` — set to `0` only for local load testing |

Per-endpoint limits (AI coaching, essay review, path generation, forum posts,
and so on) are declared inline with `@rate_limit(...)` in `app.py`.

## Build

`npm run build` runs three steps in order:

1. `build:client` — Vite bundles the browser app into `static/react/`.
2. `build:ssr` — Vite builds a server bundle into `.ssr-build/` (gitignored).
3. `prerender` — `prerender.mjs` renders the public pages to `templates/ssr/*.html`.

Flask injects the prerendered markup into `#root` and React hydrates it, so
crawlers and first paint get real HTML. Signed-in pages are intentionally not
prerendered and are served `noindex`.

**When you add a public page, update both** `PUBLIC_PAGES` in `seo.py` and
`PAGES` in `prerender.mjs`. The prerender step fails the build if a page throws
or renders suspiciously little markup.

## Search Console

1. Deploy with `PUBLIC_APP_URL` set to the live domain.
2. Add the property in Google Search Console, choosing the *HTML tag* method.
3. Put the token in `GOOGLE_SITE_VERIFICATION` and redeploy.
4. Verify, then submit `https://<domain>/sitemap.xml`.
5. Spot-check with *URL Inspection → View crawled page* — the rendered HTML
   should contain the real page copy, not an empty `<div id="root">`.

## Regenerating the social preview

`static/og-cover.png` is committed. Regenerate it only when the brand changes:

```
pip install Pillow        # build-time only, deliberately not in requirements.txt
python tools/make_og_image.py
```
