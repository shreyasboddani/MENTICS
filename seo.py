"""Search metadata: canonical URLs, robots, sitemap, and structured data.

Everything indexable is declared in PUBLIC_PAGES. Pages absent from that table
are treated as private and are served with a noindex directive, so the signed-in
product surface can never leak into search results.
"""

import os
from datetime import date

SITE_NAME = "Mentics"
DEFAULT_DESCRIPTION = (
    "Mentics is an AI-powered SAT and ACT prep platform that turns real scores, "
    "skill mastery, and mistakes into a personalized study path, with college planning too."
)

# Only these routes are indexable. Each entry drives the canonical tag, the
# sitemap, the per-page description, and the social preview.
PUBLIC_PAGES = {
    "landing": {
        "path": "/",
        "title": "Mentics — Personalized AI SAT & ACT Prep",
        "description": DEFAULT_DESCRIPTION,
        "priority": "1.0",
        "changefreq": "weekly",
    },
    "ai-sat-prep": {
        "path": "/ai-sat-prep",
        "title": "AI SAT Prep That Adapts to You | Mentics",
        "description": (
            "Use AI SAT prep that learns from your scores, skill mastery, and mistakes to build "
            "a focused five-step study path with lessons, practice, and measurable progress."
        ),
        "priority": "0.9",
        "changefreq": "weekly",
    },
    "sat-prep": {
        "path": "/sat-prep",
        "title": "Personalized SAT Prep, Practice & Progress | Mentics",
        "description": (
            "Prepare for SAT Math and Reading and Writing with personalized study paths, "
            "original SAT-style practice, skill tracking, and competitive timed battles."
        ),
        "priority": "0.9",
        "changefreq": "weekly",
    },
    "act-prep": {
        "path": "/act-prep",
        "title": "Personalized ACT Prep & Study Planning | Mentics",
        "description": (
            "Turn your ACT scores, target, schedule, and weaknesses into a focused study plan "
            "that updates as you complete work and log new results."
        ),
        "priority": "0.8",
        "changefreq": "weekly",
    },
    "college-planning": {
        "path": "/college-planning",
        "title": "AI College Planning, Essays & Application Tasks | Mentics",
        "description": (
            "Get a personalized college planning path with short lessons, real application tasks, "
            "essay guidance, deadlines, and AI coaching that remembers your progress."
        ),
        "priority": "0.8",
        "changefreq": "weekly",
    },
    "login": {
        "path": "/login",
        "title": "Sign In | Mentics",
        "description": "Sign in to Mentics to continue your personalized SAT, ACT, and college plan.",
        "priority": "0.5",
        "changefreq": "monthly",
    },
    "signup": {
        "path": "/signup",
        "title": "Create Account | Mentics",
        "description": (
            "Create a free Mentics account and get a personalized study path built around "
            "your scores, your schedule, and your target colleges."
        ),
        "priority": "0.8",
        "changefreq": "monthly",
    },
    "privacy": {
        "path": "/privacy",
        "title": "Privacy Policy | Mentics",
        "description": "How Mentics collects, uses, and protects student data.",
        "priority": "0.3",
        "changefreq": "yearly",
    },
    "terms": {
        "path": "/terms",
        "title": "Terms of Service | Mentics",
        "description": "The terms governing your use of Mentics.",
        "priority": "0.3",
        "changefreq": "yearly",
    },
}

# Never crawl these; they are per-account, need a session, or are machine-only.
DISALLOWED_PREFIXES = [
    "/api/",
    "/dashboard",
    "/account",
    "/onboarding",
    "/forum",
    "/leaderboard",
    "/strategy_article",
    "/authorize",
    "/google-login",
    "/logout",
    "/set-timezone",
]


def site_url():
    """Absolute origin for canonical URLs, without a trailing slash.

    Preview deployments get a unique hostname; canonicals must still point at the
    production domain so previews cannot compete with it in the index.
    """
    configured = os.getenv("PUBLIC_APP_URL")
    if configured:
        return configured.rstrip("/")
    vercel_host = os.getenv("VERCEL_PROJECT_PRODUCTION_URL") or os.getenv("VERCEL_URL")
    if vercel_host:
        return f"https://{vercel_host}".rstrip("/")
    return "https://mentics.vercel.app"


def is_production_host():
    """True only on the live production deployment."""
    env = os.getenv("VERCEL_ENV")
    return env is None or env == "production"


def page_meta(page, title=None):
    """Resolve the search metadata for a rendered page."""
    entry = PUBLIC_PAGES.get(page)
    base = site_url()
    if entry:
        return {
            "indexable": is_production_host(),
            "canonical": base + entry["path"],
            "description": entry["description"],
            "title": title or entry["title"],
        }
    return {
        "indexable": False,
        "canonical": None,
        "description": DEFAULT_DESCRIPTION,
        "title": title or SITE_NAME,
    }


def robots_txt():
    lines = ["User-agent: *"]
    lines += [f"Disallow: {prefix}" for prefix in DISALLOWED_PREFIXES]
    if not is_production_host():
        # Preview and development deployments must never be indexed.
        return "User-agent: *\nDisallow: /\n"
    lines.append("Allow: /")
    lines.append("")
    lines.append(f"Sitemap: {site_url()}/sitemap.xml")
    return "\n".join(lines) + "\n"


def sitemap_xml():
    today = date.today().isoformat()
    base = site_url()
    entries = []
    for entry in PUBLIC_PAGES.values():
        entries.append(
            "  <url>\n"
            f"    <loc>{base}{entry['path']}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>{entry['changefreq']}</changefreq>\n"
            f"    <priority>{entry['priority']}</priority>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def structured_data(page="landing"):
    """Accurate JSON-LD for the public product and its indexable pages."""
    base = site_url()
    graph = [
        {
            "@type": "Organization",
            "@id": f"{base}/#organization",
            "name": SITE_NAME,
            "url": base,
            "logo": f"{base}/static/favicon.svg",
            "description": DEFAULT_DESCRIPTION,
        },
        {
            "@type": "WebSite",
            "@id": f"{base}/#website",
            "url": base,
            "name": SITE_NAME,
            "description": DEFAULT_DESCRIPTION,
            "publisher": {"@id": f"{base}/#organization"},
            "inLanguage": "en-US",
        },
    ]
    if page == "landing":
        graph.append({
            "@type": "SoftwareApplication",
            "name": SITE_NAME,
            "applicationCategory": "EducationalApplication",
            "operatingSystem": "Web",
            "url": base,
            "description": DEFAULT_DESCRIPTION,
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
            },
        })
    elif page in PUBLIC_PAGES:
        entry = PUBLIC_PAGES[page]
        graph.extend([
            {
                "@type": "WebPage",
                "@id": f"{base}{entry['path']}#webpage",
                "url": f"{base}{entry['path']}",
                "name": entry["title"],
                "description": entry["description"],
                "isPartOf": {"@id": f"{base}/#website"},
                "about": {"@id": f"{base}/#organization"},
                "inLanguage": "en-US",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Mentics", "item": base},
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": entry["title"].split(" | ")[0],
                        "item": f"{base}{entry['path']}",
                    },
                ],
            },
        ])
    return {
        "@context": "https://schema.org",
        "@graph": graph,
    }
