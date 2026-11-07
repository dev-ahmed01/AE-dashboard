"""The original Accom master must expose every section as prefilled page fields."""
from bs4 import BeautifulSoup
from test_flow import client, sign_in, draft


def test_fifteen_visual_areas_prefilled_and_editable_without_touching_master(client):
    auth = sign_in(client)
    property_record = draft(client, auth, name="Map Test Residence")
    url = f"/api/admin/properties/{property_record['id']}"
    mapping = client.get(url + "/content-map", headers=auth)
    assert mapping.status_code == 200, mapping.text
    result = mapping.json()
    assert result["total_sections"] == 15
    assert [part["id"] for part in result["sections"]] == [
        "top", "gallery", "overview", "about", "tours", "amenities", "rooms",
        "rules", "payments", "floorplan", "neighbourhood", "faqs", "location",
        "reviews", "enquiry"
    ]
    assert all(part["fields"] for part in result["sections"] if part["id"] not in ("top", "gallery")), [
        (part["id"], len(part["fields"])) for part in result["sections"]
    ]
    assert next(part for part in result["sections"] if part["id"] == "gallery")["fields"] == []
    assert next(part for part in result["sections"] if part["id"] == "top")["fields"] == []
    # No incidental navigation, logo, breadcrumb or gallery UI labels are editable.
    all_fields = [field for part in result["sections"] for field in part["fields"]]
    assert all("group" in field and field["label"] for field in all_fields)
    assert len(all_fields) < 75, "The editor must not dump arbitrary DOM text nodes"
    assert not any("logo" in f["label"].lower() or "link destination" in f["label"].lower()
                   for f in all_fields)
    assert all(f["key"] in __import__("page_content").FIELD_BY_KEY for f in all_fields)
    assert all(f["key"].startswith(("about.","neighbourhood.","location."))
               for f in all_fields if f["kind"] == "cta_link")
    assert not any(f["kind"] == "cta_link" for f in result["sections"][0]["fields"])
    assert {f["key"] for f in result["sections"][-1]["fields"]} >= {"hero.room_cta","hero.enquiry_cta"}
    payment = next(part for part in result["sections"] if part["id"] == "payments")
    assert sum(f["key"].startswith("payments.card_") for f in payment["fields"]) == 8
    about = next(part for part in result["sections"] if part["id"] == "about")
    heading = next(field for field in about["fields"] if field["kind"] == "text"
                   and "Living at" in field["value"])
    assert heading["value"] == "Living at Map Test Residence"

    updated_copy = {heading["key"]: "Your next home near campus"}
    preview = client.post(url + "/preview-draft", headers=auth,
                          json={"content_overrides": updated_copy})
    assert preview.status_code == 200, preview.text
    html = BeautifulSoup(preview.text, "html.parser")
    assert "Your next home near campus" in html.select_one("#about h2").get_text(" ", strip=True)

    # An unsaved preview cannot alter persisted page copy.
    saved = client.get("/api/admin/properties", headers=auth).json()
    record = next(p for p in saved if p["id"] == property_record["id"])
    assert record["content_overrides"] == {}

    data = {**record, "content_overrides": updated_copy}
    patch = client.patch(url, headers=auth, json=data)
    assert patch.status_code == 200, patch.text
    assert patch.json()["content_overrides"] == updated_copy
    new_map = client.get(url + "/content-map", headers=auth).json()
    current_about = next(part for part in new_map["sections"] if part["id"] == "about")
    assert any(field["key"] == heading["key"] and field["value"] == "Your next home near campus"
               for field in current_about["fields"])


def test_page_copy_rejects_script_urls_and_html_is_escaped(client):
    auth = sign_in(client)
    p = draft(client, auth, name="Link Safety Residence")
    url = f"/api/admin/properties/{p['id']}"
    fields = [field for part in client.get(url + "/content-map", headers=auth).json()["sections"]
              for field in part["fields"]]
    link = next(field for field in fields if field["kind"] == "cta_link")
    invalid = client.patch(url, headers=auth,
                           json={**p, "content_overrides": {link["key"]: "javascript:alert(1)"}})
    assert invalid.status_code == 422

    text_field = next(field for field in fields if field["kind"] == "text")
    preview = client.post(url + "/preview-draft", headers=auth,
                          json={"content_overrides": {text_field["key"]: "<script>alert(1)</script>"}})
    assert preview.status_code == 200
    assert "<script>alert(1)</script>" not in preview.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in preview.text



def test_highlight_description_repeater_is_preloaded_in_original_card(client):
    auth = sign_in(client)
    p = draft(client, auth, name="Card Description Residence")
    url = f"/api/admin/properties/{p['id']}"
    preview = client.post(url + "/preview-draft", headers=auth, json={
        "highlights": ["Quiet individual rooms", "Close to campus"],
        "highlight_descriptions": ["Focus-ready space in every room", "Walkable university neighbourhood"],
    })
    assert preview.status_code == 200, preview.text
    html = BeautifulSoup(preview.text, "html.parser")
    cards = html.select("#overview .overview-facts > div")
    assert len(cards) >= 2
    assert cards[0].select_one("strong").get_text(strip=True) == "Quiet individual rooms"
    assert cards[0].select_one("p").get_text(strip=True) == "Focus-ready space in every room"
    assert cards[1].select_one("p").get_text(strip=True) == "Walkable university neighbourhood"
