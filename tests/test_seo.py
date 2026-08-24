import json

import app as app_module
import seo


PRODUCT_PAGES = {
    "ai-sat-prep": "/ai-sat-prep",
    "sat-prep": "/sat-prep",
    "act-prep": "/act-prep",
    "college-planning": "/college-planning",
}


def test_product_pages_have_unique_search_metadata():
    titles = []
    descriptions = []
    for page, path in PRODUCT_PAGES.items():
        entry = seo.PUBLIC_PAGES[page]
        assert entry["path"] == path
        assert len(entry["title"]) >= 25
        assert len(entry["description"]) >= 90
        titles.append(entry["title"])
        descriptions.append(entry["description"])

    assert len(titles) == len(set(titles))
    assert len(descriptions) == len(set(descriptions))


def test_sitemap_includes_every_product_page(monkeypatch):
    monkeypatch.setenv("PUBLIC_APP_URL", "https://www.mentics.app")
    sitemap = seo.sitemap_xml()

    for path in PRODUCT_PAGES.values():
        assert f"<loc>https://www.mentics.app{path}</loc>" in sitemap


def test_product_pages_render_indexable_semantic_content(monkeypatch):
    monkeypatch.setenv("PUBLIC_APP_URL", "https://www.mentics.app")
    monkeypatch.setenv("VERCEL_ENV", "production")
    client = app_module.app.test_client()

    expected_headings = {
        "/ai-sat-prep": "SAT prep that gets smarter",
        "/sat-prep": "Prepare for the SAT",
        "/act-prep": "Turn your ACT goal",
        "/college-planning": "Learn the strategy",
    }
    for path, heading in expected_headings.items():
        response = client.get(path)
        html = response.get_data(as_text=True)
        assert response.status_code == 200
        assert heading in html
        assert f'<link rel="canonical" href="https://www.mentics.app{path}">' in html
        assert '<meta name="robots" content="index, follow' in html
        assert 'application/ld+json' in html


def test_product_structured_data_describes_the_canonical_page(monkeypatch):
    monkeypatch.setenv("PUBLIC_APP_URL", "https://www.mentics.app")
    payload = seo.structured_data("sat-prep")
    encoded = json.dumps(payload)

    assert '"@type": "WebPage"' in encoded
    assert "https://www.mentics.app/sat-prep" in encoded
    assert '"@type": "BreadcrumbList"' in encoded
