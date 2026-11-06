"""Real request-level checks: demo seed, private preview and enquiry lifecycle."""
from bs4 import BeautifulSoup
from test_flow import client, sign_in, draft, room
import app as api
from demo_seed import seed_kingston

def test_kingston_demo_preloaded_once_with_multiple_contracts(client):
    a=sign_in(client)
    with api.SessionLocal() as db:
        seed_kingston(db,api.Property,api.Room)
        seed_kingston(db,api.Property,api.Room)
    rows=client.get('/api/admin/properties',headers=a).json()
    demo=[x for x in rows if x['slug']=='iq-kingston']
    assert len(demo)==1
    p=demo[0]
    assert p['is_demo'] and not p['published']
    assert len(p['gallery'])==4 and len(p['rooms'])==3
    assert len(p['rooms'][0]['tenancies'])==2
    assert client.get('/property/iq-kingston').status_code==404
    assert client.post('/api/admin/properties/'+str(p['id'])+'/publish',headers=a).status_code==422
    preview=client.post('/api/admin/properties/'+str(p['id'])+'/preview-link',headers=a)
    assert preview.status_code==200
    page=client.get(preview.json()['url'])
    assert page.status_code==200
    assert 'noindex,nofollow' in page.text
    assert '/accom-template/app.js' in page.text
    assert '/accom-template/bridge.js' in page.text
    assert '/accom-template/assets/' in page.text
    assert 'accom-property-data' in page.text
    assert page.headers['cache-control']=='no-store'
    assert client.get('/property/iq-kingston?preview_token=invalid').status_code==404

def test_approved_template_uses_new_property_identity_and_saves_enquiries(client):
    a=sign_in(client)
    p=draft(client,a,name='Manor House')
    r=room(client,a,p)
    current=client.get('/api/admin/properties',headers=a).json()
    p=next(x for x in current if x['id']==p['id'])
    published=client.post('/api/admin/properties/'+str(p['id'])+'/publish',headers=a)
    assert published.status_code==200,published.text
    page=client.get('/property/'+p['slug'])
    assert page.status_code==200
    dom=BeautifulSoup(page.text,'html.parser')
    assert dom.select_one('#property-title').get_text(strip=True)=='Manor House'
    assert 'iQ Kingston' not in dom.body.get_text(' ',strip=True)
    assert dom.select_one('script#accom-property-data')
    assert dom.select_one('link[href="/accom-template/site.css"]')
    assert dom.select_one('link[href="/accom-template/rail-refinement.css"]')
    submitted=client.post('/api/enquiries',json={'property_id':p['id'],'room_id':r['id'],
        'name':'Jordan Example','email':'jordan@example.org','consent':True,
        'message':'Please check my preferred contract'})
    assert submitted.status_code==201,submitted.text
    enquiries=client.get('/api/admin/enquiries',headers=a).json()
    assert any(x['id']==submitted.json()['id'] for x in enquiries)
