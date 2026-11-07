"""Live Category preview must be secure, reflect unsaved fields, and never persist them."""
from bs4 import BeautifulSoup
from test_flow import client, sign_in, draft


def test_staff_preview_renders_unsaved_content_without_updating_database(client):
    admin = sign_in(client)
    p = draft(client, admin, name='Old Listing Name')
    body = {
        'name': 'New Preview Name',
        'description': 'Updated preview only, should not save',
        'city': 'Birmingham',
        'highlights': ['Private study space', 'Gym'],
        'gallery': [
            {'url': 'https://images.example.com/approved.webp', 'alt': 'New lounge', 'layout': 'large'},
            {'url': 'javascript:alert(1)', 'alt': 'Untrusted source'},
        ],
    }
    unauthenticated = client.post(f"/api/admin/properties/{p['id']}/preview-draft", json=body)
    assert unauthenticated.status_code == 401
    result = client.post(f"/api/admin/properties/{p['id']}/preview-draft", headers=admin, json=body)
    assert result.status_code == 200, result.text
    assert result.headers['cache-control'] == 'no-store'
    assert result.headers['x-robots-tag'] == 'noindex, nofollow'
    page = BeautifulSoup(result.text, 'html.parser')
    assert page.select_one('.property-heading h1').get_text(strip=True) == 'New Preview Name'
    assert page.select_one('meta[name=robots]')['content'] == 'noindex,nofollow'
    assert len(page.select('section.gallery > .gallery-tile')) == 1
    assert page.select_one('.gallery-tile img')['alt'] == 'New lounge'
    assert 'javascript:alert' not in str(page)
    assert 'Private study space' in page.get_text(' ', strip=True)
    stored = client.get('/api/admin/properties',headers=admin).json()
    assert next(x for x in stored if x['id'] == p['id'])['name'] == 'Old Listing Name'
    assert stored[0]['gallery'][0]['url'] != 'https://images.example.com/approved.webp'


def test_draft_previews_empty_data_without_required_field_errors(client):
    admin = sign_in(client)
    created = client.post('/api/admin/properties/draft', headers=admin, json={'name':'Fresh Draft'})
    assert created.status_code == 201, created.text
    p = created.json()
    result = client.post(f"/api/admin/properties/{p['id']}/preview-draft",
                         headers=admin,
                         json={'name':'Fresh Draft','city':'','gallery':[],'faq':[{'question':'','answer':''}]})
    assert result.status_code == 200, result.text
    page = BeautifulSoup(result.text,'html.parser')
    assert page.select_one('.property-heading h1').get_text(strip=True) == 'Fresh Draft'
    assert page.select_one('.accom-master-preview-note') is not None
    assert page.select_one('script#accom-property-data') is not None
