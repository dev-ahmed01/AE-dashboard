"""New blank demo drafts can use the approved page's sample copy safely."""
from test_flow import client, sign_in
from template_sample import template_sample


def test_template_examples_are_extracted_from_master_not_invented():
    sample = template_sample()
    assert sample["city"] == "Kingston upon Thames"
    assert sample["address"] == "15 Wood Street"
    assert sample["postcode"] == "KT1 1TY"
    assert sample["university"] == "Kingston University"
    assert "en suite" in sample["description"].lower()
    assert len(sample["gallery"]) == 4
    assert all(image["alt"].startswith("Illustrative ") for image in sample["gallery"])
    assert len(sample["highlights"]) == len(sample["highlight_descriptions"]) == 4
    assert len(sample["policies"]) == 4
    assert len(sample["faq"]) == 5
    assert len(sample["landmarks"]) >= 8
    assert sample.get("reviews") is None, "Never import fictional review examples as genuine testimonials"


def test_draft_content_map_prefills_illustrative_demo_without_writing(client):
    auth = sign_in(client)
    response = client.post("/api/admin/properties/draft",
                           headers=auth, json={"name": "Demo_11"})
    assert response.status_code == 201, response.text
    draft = response.json()
    assert not draft["published"]
    assert not draft["city"]
    path = f"/api/admin/properties/{draft['id']}/content-map"
    result = client.get(path, headers=auth)
    assert result.status_code == 200, result.text
    content = result.json()
    assert content["total_sections"] == 15
    assert content["auto_prefill_template"] is True
    assert content["template_sample_unverified"] is True
    assert content["template_sample"]["city"] == "Kingston upon Thames"
    assert content["template_sample"]["gallery"][0]["layout"] == "large"
    # Reading the editor's suggestions must not write sample data to the DB.
    saved = next(p for p in client.get("/api/admin/properties", headers=auth).json()
                 if p["id"] == draft["id"])
    assert saved["city"] == "" and saved["gallery"] == []
    assert not saved["is_demo"]

    # A user can explicitly save the sample, but it must remain unpublished.
    values = {**saved, **content["template_sample"], "is_demo": True, "noindex": True}
    patched = client.patch(f"/api/admin/properties/{draft['id']}",
                           headers=auth, json=values)
    assert patched.status_code == 200, patched.text
    assert patched.json()["is_demo"] is True
    assert patched.json()["published"] is False
    denied = client.post(f"/api/admin/properties/{draft['id']}/publish", headers=auth)
    assert denied.status_code == 422
    assert "demonstration" in denied.json()["detail"].lower()


def test_populated_listing_is_not_automatically_replaced_with_template_data(client):
    auth = sign_in(client)
    response = client.post("/api/admin/properties", headers=auth, json={
        "name": "Demo_12", "city": "Birmingham", "address": "Verified Street",
        "description": "A real existing description belonging to the draft.",
    })
    assert response.status_code == 201, response.text
    page_id = response.json()["id"]
    result = client.get(f"/api/admin/properties/{page_id}/content-map", headers=auth)
    assert result.status_code == 200
    assert result.json()["auto_prefill_template"] is False
    assert result.json()["template_sample"] is not None
