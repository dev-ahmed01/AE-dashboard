"""Independent SEO fields must persist and reach the original HTML renderer."""
from bs4 import BeautifulSoup
from test_flow import client, sign_in, draft, published


def _meta(html):
    soup = BeautifulSoup(html, "html.parser")
    robots = soup.select_one('meta[name="robots"]')
    canonical = soup.select_one('link[rel="canonical"]')
    return robots["content"], canonical["href"]


def test_index_follow_canonical_can_be_edited_independently(client):
    auth = sign_in(client)
    p, _ = published(client, auth)
    path = f"/api/admin/properties/{p['id']}"
    assert _meta(client.get("/property/" + p["slug"]).text)[0] == "index,follow"

    next_data = {**p, "nofollow": True, "noindex": False,
                 "canonical_override": "https://example.org/stays/verified-room"}
    result = client.patch(path, headers=auth, json=next_data)
    assert result.status_code == 200, result.text
    state = result.json()
    assert state["nofollow"] is True
    assert state["noindex"] is False
    assert state["canonical_override"] == "https://example.org/stays/verified-room"
    robots, canonical = _meta(client.get("/property/" + p["slug"]).text)
    assert robots == "index,nofollow"
    assert canonical == "https://example.org/stays/verified-room"

    result = client.patch(path, headers=auth,
                          json={**state, "noindex": True, "nofollow": False,
                                "canonical_override": ""})
    assert result.status_code == 200, result.text
    robots, canonical = _meta(client.get("/property/" + p["slug"]).text)
    assert robots == "noindex,follow"
    assert canonical.endswith("/property/" + p["slug"])


def test_invalid_canonical_is_rejected_and_preview_is_always_noindex(client):
    auth = sign_in(client)
    p = draft(client, auth, name="SEO Sandbox Residence")
    path = f"/api/admin/properties/{p['id']}"
    for invalid in ("javascript:alert(1)", "http://insecure.example/stays",
                    "https://example.org/<script>", "https://"):
        response = client.patch(path, headers=auth, json={**p, "canonical_override": invalid})
        assert response.status_code == 422, invalid

    preview = client.post(path + "/preview-draft", headers=auth,
                          json={"noindex": False, "nofollow": False,
                                "canonical_override": "https://example.org/rooms/test"})
    assert preview.status_code == 200, preview.text
    robots, canonical = _meta(preview.text)
    assert robots == "noindex,nofollow", "Editor previews may never be indexable"
    assert canonical == "https://example.org/rooms/test"
    assert client.get('/api/admin/properties', headers=auth).status_code == 200
