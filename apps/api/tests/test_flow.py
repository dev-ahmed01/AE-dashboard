"""Regressions from the 6 Nov multi-admin audit: test real API contracts."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

os.environ.update({
 'DATABASE_URL':'sqlite:///:memory:',
 'JWT_SECRET':'test-secret-with-32-plus-characters-for-ci-only',
 'ADMIN_EMAIL':'admin@example.com',
 'ADMIN_PASSWORD':'not-a-real-admin-password',
 'APP_ENVIRONMENT':'testing',
 'DEV_AUTO_VERIFY_EMAIL':'1',
})
import app as api

PHOTO={'url':'https://images.example.com/room.jpg','alt':'Approved room photo','category':'Rooms','layout':'large'}
DESC='A fully furnished student accommodation offering dedicated study spaces near campus.'

@pytest.fixture
def client():
    api.Base.metadata.drop_all(api.engine)
    with TestClient(api.app) as c:
        yield c

def sign_in(client,email='admin@example.com',password='not-a-real-admin-password'):
    r=client.post('/api/auth/login',json={'email':email,'password':password})
    assert r.status_code==200,r.text
    return {'Authorization':'Bearer '+r.json()['token']}

def draft(client,auth,**values):
    data={'name':'iQ Kingston','city':'Kingston upon Thames','address':'15 Wood Street, Kingston, KT1','description':DESC,'gallery':[PHOTO]}
    data.update(values)
    r=client.post('/api/admin/properties',json=data,headers=auth)
    assert r.status_code==201,r.text
    return r.json()

def room(client,auth,p,**values):
    data={'name':'Silver En Suite','room_type':'En suite','price':315,'currency':'GBP','price_period':'week','availability':'available','rate_checked_at':'2026-11-01','parent_edit_version':p['edit_version']}
    data.update(values)
    r=client.post(f"/api/admin/properties/{p['id']}/rooms",json=data,headers=auth)
    assert r.status_code==201,r.text
    return r.json()

def getprop(client,auth,id):
    return next(p for p in client.get('/api/admin/properties',headers=auth).json() if p['id']==id)

def published(client,auth):
    p=draft(client,auth)
    r=room(client,auth,p)
    status=client.post(f"/api/admin/properties/{p['id']}/publish",headers=auth)
    assert status.status_code==200,status.text
    return status.json(),r

def editor(client,auth,email='editor@example.com'):
    res=client.post('/api/admin/staff',headers=auth,json={'name':'Editor Tester','email':email,'password':'long-pass-editor-01','role':'editor'})
    assert res.status_code==201,res.text
    return sign_in(client,email,'long-pass-editor-01')

def test_directory_enquiry_portal_and_cashback(client):
    admin=sign_in(client);p,r=published(client,admin)
    assert client.get('/api/properties?q=Kingston').json()[0]['from_price']==315
    assert client.get('/api/properties?max_price=300').json()==[]
    assert client.get('/api/properties/'+p['slug']).json()['rooms'][0]['name']=='Silver En Suite'
    student=client.post('/api/auth/register',json={'name':'Student Tester','email':'student@example.com','password':'long-enough-password'})
    assert student.status_code==201,student.text
    hs={'Authorization':'Bearer '+student.json()['token']}
    assert client.patch(f"/api/admin/properties/{p['id']}",json=p,headers=hs).status_code==403
    assert client.post(f"/api/me/saved/{p['id']}",headers=hs).status_code==201
    payload={'property_id':p['id'],'room_id':r['id'],'name':'Student Tester','email':'student@example.com','consent':True}
    assert client.post('/api/enquiries',json={**payload,'consent':False}).status_code==422
    lead=client.post('/api/enquiries',json=payload,headers=hs)
    assert lead.status_code==201,lead.text
    assert client.get('/api/me/overview',headers=hs).json()['enquiries'][0]['status']=='new'
    assert client.patch('/api/admin/enquiries/'+str(lead.json()['id']),json={'status':'contacted'},headers=admin).status_code==200
    assert client.get('/api/me/overview',headers=hs).json()['enquiries'][0]['status']=='contacted'
    c=client.post('/api/admin/cashback',headers=admin,json={'enquiry_id':lead.json()['id'],'amount':40,'currency':'GBP','status':'eligible'})
    assert c.status_code==201,c.text
    assert client.get('/api/me/overview',headers=hs).json()['cashback'][0]['status']=='eligible'

def test_repeaters_gallery_roundtrip_and_validation(client):
    a=sign_in(client)
    p=draft(client,a,highlights=['Bills','Study','Security'],gallery=[PHOTO,{'url':'https://images.example.com/second.jpg','alt':'Exterior','layout':'regular'}],faq=[{'question':'Are bills included?','answer':'Yes, standard utilities are included.'}],floorplans=[PHOTO],offers=[{'title':'Welcome offer','description':'Eligibility to confirm','valid_until':'2027-01-01'}])
    assert p['gallery'][0]['layout']=='large'
    amended={**p,'highlights':['Security','Study','Bills'],'gallery':list(reversed(p['gallery']))}
    saved=client.patch('/api/admin/properties/'+str(p['id']),json=amended,headers=a)
    assert saved.status_code==200,saved.text
    after=getprop(client,a,p['id'])
    assert [x['layout'] for x in after['gallery']]==['regular','large']
    assert after['highlights'][0]=='Security'
    bad={**after,'faq':[{}]}
    assert client.patch('/api/admin/properties/'+str(p['id']),json=bad,headers=a).status_code==422
    assert client.patch('/api/admin/properties/'+str(p['id']),json={**after,'gallery':[{'url':'javascript:alert(1)'}]},headers=a).status_code==422

def test_multi_admin_conflict_returns_409_and_preserves_new_data(client):
    a=sign_in(client);p=draft(client,a)
    initial=getprop(client,a,p['id']);stale=dict(initial)
    newer=client.patch('/api/admin/properties/'+str(p['id']),json={**initial,'highlights':['first admin']},headers=a)
    assert newer.status_code==200,newer.text
    second=client.patch('/api/admin/properties/'+str(p['id']),json={**stale,'description':'Stale editor overwrites first admin'},headers=a)
    assert second.status_code==409,second.text
    assert getprop(client,a,p['id'])['highlights']==['first admin']

def test_editor_cannot_change_published_room_but_admin_can(client):
    a=sign_in(client);p,r=published(client,a);he=editor(client,a)
    new=client.post('/api/admin/properties/'+str(p['id'])+'/rooms',headers=he,json={'name':'Hidden price','parent_edit_version':p['edit_version']})
    assert new.status_code==403,new.text
    change=client.patch('/api/admin/rooms/'+str(r['id']),headers=he,json={**r,'price':1,'parent_edit_version':p['edit_version']})
    assert change.status_code==403,change.text
    ok=client.patch('/api/admin/rooms/'+str(r['id']),headers=a,json={**r,'price':333,'parent_edit_version':p['edit_version']})
    assert ok.status_code==200,ok.text
    assert ok.json()['price']==333

def test_filters_same_room_and_only_available_rates(client):
    a=sign_in(client);p=draft(client,a)
    room(client,a,p,name='Expensive en suite',room_type='En suite',price=900)
    p=getprop(client,a,p['id']);room(client,a,p,name='Cheap studio',room_type='Studio',price=200)
    p=client.post('/api/admin/properties/'+str(p['id'])+'/publish',headers=a).json()
    assert client.get('/api/properties?room_type=En%20suite&max_price=300').json()==[]
    assert client.get('/api/properties?room_type=Studio&max_price=300').json()[0]['id']==p['id']
    p2=draft(client,a,name='No Availability',city='London');room(client,a,p2,name='Unavailable room',price=1,availability='unavailable')
    p2=client.post('/api/admin/properties/'+str(p2['id'])+'/publish',headers=a).json()
    assert next(x for x in client.get('/api/properties').json() if x['id']==p2['id'])['from_price'] is None

def test_mixed_currency_and_period_do_not_fake_lowest_price(client):
    a=sign_in(client);p=draft(client,a)
    room(client,a,p,name='Room GBP',currency='GBP',price_period='month',price=150)
    p=getprop(client,a,p['id']);room(client,a,p,name='Room EUR',currency='EUR',price_period='week',price=200)
    pub=client.post('/api/admin/properties/'+str(p['id'])+'/publish',headers=a)
    assert pub.status_code==200
    assert pub.json()['from_price'] is None
    assert 'currency' in pub.json()['price_note']

def test_publication_checklist_empty_and_archiving(client):
    a=sign_in(client)
    p=draft(client,a,description='',gallery=[])
    assert client.post('/api/admin/properties/'+str(p['id'])+'/publish',headers=a).status_code==422
    assert client.post('/api/admin/properties',headers=a,json={'name':'Blank','city':'London','published':True}).status_code==422
    p2=draft(client,a,name='Different Property')
    room(client,a,p2)
    p2=client.post('/api/admin/properties/'+str(p2['id'])+'/publish',headers=a).json()
    archived=client.post('/api/admin/properties/'+str(p2['id'])+'/archive',headers=a)
    assert archived.status_code==200
    assert client.get('/api/properties/'+p2['slug']).status_code==404
    assert client.post('/api/admin/properties/'+str(p2['id'])+'/restore',headers=a).status_code==200
    assert client.get('/api/properties/'+p2['slug']).status_code==404  # restore stays draft

def test_inactive_room_visible_to_staff_and_restore(client):
    a=sign_in(client);p,r=published(client,a)
    inactive=client.patch('/api/admin/rooms/'+str(r['id']),headers=a,json={**r,'active':False,'parent_edit_version':p['edit_version']})
    assert inactive.status_code==200,inactive.text
    record=getprop(client,a,p['id']);inactive_room=record['rooms'][0]
    assert inactive_room['active'] is False
    assert client.get('/api/properties/'+p['slug']).json()['rooms']==[]
    active=client.patch('/api/admin/rooms/'+str(r['id']),headers=a,json={**inactive_room,'active':True,'parent_edit_version':record['edit_version']})
    assert active.status_code==200,active.text

def test_unassign_consultant_and_booking_requires_reference(client):
    a=sign_in(client);p,_=published(client,a);e=editor(client,a)
    student=client.post('/api/enquiries',json={'property_id':p['id'],'name':'Visitor','email':'visitor@example.com','consent':True}).json()
    staff=client.get('/api/admin/staff',headers=a).json();editor_id=next(x['id'] for x in staff if x['role']=='editor')
    assert client.patch('/api/admin/enquiries/'+str(student['id']),headers=a,json={'assigned_to_id':editor_id}).json()['assigned_to_id']==editor_id
    assert client.patch('/api/admin/enquiries/'+str(student['id']),headers=a,json={'assigned_to_id':None}).json()['assigned_to_id'] is None
    assert client.patch('/api/admin/enquiries/'+str(student['id']),headers=e,json={'status':'booked'}).status_code==403
    assert client.patch('/api/admin/enquiries/'+str(student['id']),headers=a,json={'status':'booked'}).status_code==403
    assert client.patch('/api/admin/enquiries/'+str(student['id']),headers=a,json={'status':'booked','booking_reference':'PROVIDER-123'}).status_code==200
    assert client.post('/api/admin/enquiries/'+str(student['id'])+'/notes',headers=e,json={'message':'Spoke to the student'}).status_code==201
    assert len(client.get('/api/admin/enquiries/'+str(student['id'])+'/notes',headers=a).json())==1

def test_guest_enquiry_claim_and_dedup(client):
    a=sign_in(client);p,_=published(client,a)
    data={'property_id':p['id'],'name':'Alex Student','email':'alex@example.com','consent':True,'message':'Would like to know availability'}
    first=client.post('/api/enquiries',json=data);same=client.post('/api/enquiries',json=data)
    assert first.status_code==201 and same.status_code==201
    assert first.json()['id']==same.json()['id']
    member=client.post('/api/auth/register',json={'name':'Alex Student','email':'alex@example.com','password':'long-enough-password'})
    assert member.status_code==201,member.text
    hs={'Authorization':'Bearer '+member.json()['token']}
    assert len(client.get('/api/me/overview',headers=hs).json()['enquiries'])==1

def test_staff_revocation_and_cashback_permissions(client):
    a=sign_in(client);h=editor(client,a)
    p,_=published(client,a)
    assert client.post('/api/admin/cashback',headers=h,json={'enquiry_id':123}).status_code==403
    member_id=next(x['id'] for x in client.get('/api/admin/staff',headers=a).json() if x['role']=='editor')
    assert client.patch('/api/admin/staff/'+str(member_id),headers=a,json={'active':False}).status_code==200
    assert client.get('/api/admin/properties',headers=h).status_code==401

def test_property_seo_meta_and_sitemap(client):
    a=sign_in(client);p,_=published(client,a)
    html=client.get('/property/'+p['slug']).text
    assert 'name="robots" content="index,follow"' in html
    assert 'rel="canonical"' in html and 'application/ld+json' in html
    assert p['slug'] in client.get('/sitemap.xml').text
    changed=client.patch('/api/admin/properties/'+str(p['id']),headers=a,json={**p,'noindex':True})
    assert changed.status_code==200,changed.text
    assert 'noindex,nofollow' in client.get('/property/'+p['slug']).text
    assert p['slug'] not in client.get('/sitemap.xml').text

def test_template_import_mapping_editorial_page_publish_and_script_removal(client):
    a=sign_in(client)
    html=b'<html><body><section><h1>City guide</h1><p>Find student accommodation in Manchester.</p><script>alert(1)</script><a href="javascript:alert(1)">Dangerous link</a></section><section><h2>Universities</h2><p>Find a campus.</p></section></body></html>'
    imported=client.post('/api/admin/templates',headers=a,data={'name':'City guide'},files={'file':('guide.html',html,'text/html')})
    assert imported.status_code==201,imported.text
    t=imported.json();assert len(t['sections'])==2
    assert '<script' not in client.get('/api/admin/templates/'+str(t['id'])+'/preview',headers=a).text
    t['fields'][0]['mode']='static'
    approved=client.patch('/api/admin/templates/'+str(t['id']),headers=a,json={'fields':t['fields'],'approved':True})
    assert approved.status_code==200,approved.text
    page=client.post('/api/admin/pages',headers=a,json={'template_id':t['id'],'title':'Manchester accommodation guide','seo_title':'Manchester accommodation | Accom','meta_description':'Discover selected accommodation near campuses in Manchester, with information for student enquiries.'})
    assert page.status_code==201,page.text
    newpage=page.json();assert client.get('/site/'+newpage['slug']).status_code==404
    assert client.post('/api/admin/pages/'+str(newpage['id'])+'/publish',headers=a).status_code==200
    assert 'City guide' in client.get('/site/'+newpage['slug']).text
    current=client.get('/api/admin/pages',headers=a).json()[0]
    assert client.patch('/api/admin/pages/'+str(newpage['id']),headers=a,json={**current,'values':{t['fields'][0]['key']:'tampered'}}).status_code==422

def test_public_registration_requires_email_ownership(client,monkeypatch):
    monkeypatch.setenv('DEV_AUTO_VERIFY_EMAIL','0')
    monkeypatch.setattr(api,'SMTP_HOST','smtp.example.net')
    monkeypatch.setattr(api,'SMTP_FROM','support@example.net')
    captured=[]
    monkeypatch.setattr(api,'_send_verification',lambda email,raw: captured.append((email,raw)))
    registration=client.post('/api/auth/register',json={'name':'Verified Student','email':'realstudent@example.net','password':'long-password-for-student'})
    assert registration.status_code==201,registration.text
    assert registration.json()['verification_required'] is True
    assert 'token' not in registration.json()
    assert client.post('/api/auth/login',json={'email':'realstudent@example.net','password':'long-password-for-student'}).status_code==403
    assert captured and captured[0][0]=='realstudent@example.net'
    verification=client.post('/api/auth/verify-email',json={'token':captured[0][1]})
    assert verification.status_code==200,verification.text
    assert client.post('/api/auth/login',json={'email':'realstudent@example.net','password':'long-password-for-student'}).status_code==200
    monkeypatch.setenv('DEV_AUTO_VERIFY_EMAIL','1')

def test_rate_limited_login_and_media_file_validation(client,monkeypatch):
    a=sign_in(client)
    for i in range(9):
        assert client.post('/api/auth/login',json={'email':'missing@example.com','password':'wrong'}).status_code==401
    assert client.post('/api/auth/login',json={'email':'missing@example.com','password':'wrong'}).status_code==429
    bad=client.post('/api/admin/media',headers=a,data={'alt':'Should not upload'},files={'file':('false.png',b'not a real picture','image/png')})
    assert bad.status_code==422,bad.text
    from PIL import Image
    import io
    image=Image.new('RGB',(120,90),'white');stream=io.BytesIO();image.save(stream,format='PNG')
    class FakeS3:
        def head_bucket(self,**kw):return {}
        def put_object(self,**kw):assert kw['ContentType']=='image/jpeg'
        def get_object(self,**kw):return {'Body':io.BytesIO(b'hello')}
    monkeypatch.setattr(api,'_s3',lambda:FakeS3())
    good=client.post('/api/admin/media',headers=a,data={'alt':'Sample verified photo'},files={'file':('photo.png',stream.getvalue(),'image/png')})
    assert good.status_code==201,good.text
    assert good.json()['url'].startswith('/api/media/')
    assert client.get(good.json()['url']).status_code==200

def test_add_page_native_template_creates_unpublished_draft(client):
    login=client.post('/api/auth/login',json={'email':'admin@example.com','password':'not-a-real-admin-password'})
    assert login.status_code==200,login.text
    headers={'Authorization':'Bearer '+login.json()['token']}
    first=client.post('/api/admin/properties/draft',headers=headers,json={'name':'Kingston Student Residence'})
    assert first.status_code==201,first.text
    assert first.json()['published'] is False and first.json()['city']=='' and first.json()['noindex'] is True
    second=client.post('/api/admin/properties/draft',headers=headers,json={'name':'Kingston Student Residence'})
    assert second.status_code==201 and second.json()['slug']!=first.json()['slug']
