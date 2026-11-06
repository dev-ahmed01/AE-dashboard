"""Regression checks for the approved property template on non-demo listings.

These tests avoid the database so they also catch SSR and empty-preview defects.
"""
from types import SimpleNamespace
from bs4 import BeautifulSoup
from property_runtime import render_property


def make_property(gallery, **overrides):
    fields = dict(
        name="Birmingham Riverside Residence",
        slug="birmingham-riverside-residence",
        city="Birmingham",
        country="United Kingdom",
        address="10 Example Street",
        postcode="B1 1AA",
        description="A sample Birmingham property with editable details from the Category dashboard.",
        seo_title="Birmingham Residence | Accom by Emlen",
        meta_description="An accommodation listing in Birmingham with editable property content.",
        noindex=True,
        is_demo=False,
        highlights=["Quiet study area", "Modern common areas", "Convenient local transport"],
        amenities=["Wi-Fi", "Study room", "Laundry"],
        landmarks=[{"name": "New Street Station", "detail": "Check the current route"}],
        gallery=gallery,
        review_source_url="",
    )
    fields.update(overrides)
    return SimpleNamespace(**fields)


def photo(i):
    return {
        "url": "https://example.org/accom-" + str(i) + ".webp",
        "alt": "Property view " + str(i),
        "layout": "large" if i == 0 else "regular",
    }


def render(p, **payload):
    values = dict(from_price=None, currency="GBP", price_period="week",
                  rooms=[], highlights=p.highlights, gallery=p.gallery)
    values.update(payload)
    return BeautifulSoup(render_property(p, values, "https://accombyemlen.example", preview=True),
                         "html.parser")


def test_other_property_has_no_kingston_specific_public_facts():
    p = make_property([photo(0), photo(1)])
    dom = render(p, from_price=415, currency="GBP", price_period="week")
    text = dom.body.get_text(" ", strip=True)
    assert "Birmingham Riverside Residence" in text
    assert p.description in text
    assert "Kingston University" not in text
    assert "Kingston Town Centre" not in text
    assert "Other Kingston options" not in text
    assert "15 min walk" not in text
    assert not dom.select("#house-rules")
    assert not dom.select('.section-nav a[href="#house-rules"]')
    assert not dom.select(".related-section")
    assert dom.select_one(".cta-google-map")["title"] == "Map showing " + p.name
    assert "10%20Example%20Street" in dom.select_one(".cta-google-map")["src"]
    assert dom.select_one("#cta-from-price").get_text(strip=True) == "£415"
    assert dom.select_one(".cta-price-hero .cta-overview-value span").get_text(strip=True) == "/ week"
    assert dom.select_one('meta[name="robots"]')["content"] == "noindex,nofollow"


def test_gallery_supports_more_than_four_images_and_preserves_labels():
    p = make_property([photo(i) for i in range(7)])
    dom = render(p)
    tiles = dom.select(".gallery-grid .gallery-tile")
    assert len(tiles) == 7
    assert [x["data-gallery-index"] for x in tiles] == [str(i) for i in range(7)]
    assert tiles[0].get("aria-label") == "Open Property view 0 in gallery"
    assert tiles[6].find("img")["src"] == photo(6)["url"]
    assert "gallery-main" in tiles[0].get("class", [])
    assert "gallery-main" not in tiles[6].get("class", [])
    assert dom.select_one("#view-gallery").get_text(strip=True) == "View all 7 photos"


def test_small_and_empty_draft_gallery_can_be_previewed_without_fake_images():
    one = render(make_property([photo(0)]))
    assert len(one.select(".gallery-grid .gallery-tile")) == 1
    assert "single-photo" in one.select_one(".gallery-grid").get("class", [])
    empty = render(make_property([]))
    assert not empty.select(".gallery-grid .gallery-tile")
    assert empty.select_one("#view-gallery").has_attr("disabled")
    assert not empty.select_one("#lightbox-image").get("src")
    assert empty.select_one("#cta-from-price").get_text(strip=True) == "Price on request"
    assert empty.select_one(".cta-price-hero .cta-overview-value span").get_text(strip=True) == ""


def test_price_indicator_uses_backend_currency_and_billing_period():
    dom = render(make_property([photo(0)]), from_price=750, currency="EUR", price_period="month")
    assert dom.select_one("#cta-from-price").get_text(strip=True) == "€750"
    assert dom.select_one(".cta-price-hero .cta-overview-value span").get_text(strip=True) == "/ month"
    assert dom.select_one("#mobile-price").get_text(strip=True) == "From €750/mo"
