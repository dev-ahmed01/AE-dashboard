"""The public property and staff draft MUST share the deployed Accom visual master."""
from types import SimpleNamespace
from bs4 import BeautifulSoup
from original_runtime import render_property


SECTIONS = (
    "overview", "about", "tours", "amenities", "rooms", "rules", "payments",
    "floorplan", "neighbourhood", "faqs", "location", "reviews"
)


def make_property(**changes):
    model = dict(name="Test Residence", slug="test-residence", city="Birmingham",
                 country="United Kingdom", address="100 Example Road", postcode="B1 1AA",
                 description="A genuine editable property description.",
                 gallery=[], highlights=[], amenities=[], policies=[], faq=[],
                 landmarks=[], reviews=[], offers=[], floorplans=[],
                 review_score=None, review_source_url="", noindex=True,
                 seo_title="", meta_description="", is_demo=False)
    model.update(changes)
    return SimpleNamespace(**model)


def render(prop, preview=True, rooms=None):
    return BeautifulSoup(render_property(
        prop, {"rooms": rooms or [], "from_price": None, "currency": "GBP",
               "price_period": "week"}, "https://accombyemlen.example", preview=preview
    ), "html.parser")


def test_draft_is_original_master_not_the_old_simplified_template():
    dom = render(make_property())
    assert all(dom.select_one("#" + section) for section in SECTIONS)
    assert dom.select_one("section.gallery")
    assert dom.select_one(".cta-sticky .booking-card")
    assert dom.select_one("#galleryDialog")
    assert dom.select_one("#compareDialog")
    assert dom.select_one("#enquiryForm")
    assert dom.select_one("#billInputs")
    assert dom.select_one("#roomList")
    assert dom.select_one('script[src="/accom-template/original-master.js"]')
    assert dom.select_one('script[src="/accom-template/original-integration.js"]')
    assert dom.select_one('script#accom-property-data')
    assert len(dom.select("section.gallery > .gallery-tile")) == 5
    assert dom.select_one(".accom-master-preview-note")
    assert dom.select_one(".property-heading h1").get_text(strip=True) == "Test Residence"


def test_property_edits_keep_layout_and_are_server_rendered():
    photo = {"url": "https://cdn.example.org/bedroom.webp",
             "alt": "Real bedroom", "layout": "regular", "category": "Rooms"}
    dom = render(make_property(
        name="Birmingham Quays", description="See the waterside from your room.",
        gallery=[photo], highlights=["Private workspace"],
        amenities=["Wi-Fi", "Laundry"],
        landmarks=[{"name": "Station", "detail": "Distance to confirm"}],
        faq=[{"question": "Can I visit?", "answer": "Ask for a viewing."}],
    ))
    assert dom.select_one(".property-heading h1").get_text(strip=True) == "Birmingham Quays"
    assert "See the waterside from your room." in dom.select_one("#overview").get_text(" ", strip=True)
    assert "Wi-Fi" in dom.select_one("#amenities").get_text(" ", strip=True)
    assert "Station" in dom.select_one("#location").get_text(" ", strip=True)
    assert "Can I visit?" in dom.select_one("#faqs").get_text(" ", strip=True)
    tile = dom.select_one("section.gallery > .gallery-tile")
    assert tile.img["src"] == "https://cdn.example.org/bedroom.webp"
    assert "gallery-large" not in tile.get("class", [])
    assert tile.img["alt"] == "Real bedroom"


def test_public_missing_images_never_uses_sample_kingston_photography():
    dom = render(make_property(), preview=False)
    assert not dom.select("section.gallery > .gallery-tile")
    assert not dom.select("[data-asset]")
    assert dom.select_one(".accom-master-photo-placeholder")
    assert not dom.select_one(".accom-master-preview-note")
    assert "iQ Kingston" not in dom.body.get_text(" ", strip=True)
    assert dom.select_one("meta[name=robots]")["content"] == "noindex,nofollow"


def test_original_large_photo_switch_is_respected():
    dom = render(make_property(gallery=[{
        "url": "https://cdn.example.org/real.webp", "alt": "Bedroom",
        "category": "Rooms", "layout": "large"
    }]))
    assert "gallery-large" in dom.select_one("section.gallery > .gallery-tile").get("class", [])
