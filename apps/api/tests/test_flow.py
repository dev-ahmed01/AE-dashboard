import importlib
import os

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['JWT_SECRET'] = 'test-secret-with-32-plus-characters-for-ci-only'
os.environ['ADMIN_EMAIL'] = 'admin@example.com'
os.environ['ADMIN_PASSWORD'] = 'not-a-real-admin-password'

from fastapi.testclient import TestClient
import app as api


def test_directory_to_enquiry_to_portal_and_admin():
    with TestClient(api.app) as client:
        admin=client.post('/api/auth/login',json={'email':'admin@example.com','password':'not-a-real-admin-password'})
        assert admin.status_code==200,admin.text
        ha={'Authorization':'Bearer '+admin.json()['token']}
        draft=client.post('/api/admin/properties',json={'name':'iQ Kingston','city':'Kingston upon Thames','address':'15 Wood Street','description':'A student residence','university':'Kingston University','amenities':['Wi-Fi','Study spaces'],'published':False},headers=ha)
        assert draft.status_code==201,draft.text
        property_id=draft.json()['id']; slug=draft.json()['slug']
        assert client.get('/api/properties').json()==[]
        data=draft.json(); data.update({'published':True})
        edited=client.patch(f'/api/admin/properties/{property_id}',json=data,headers=ha)
        assert edited.status_code==200,edited.text
        room=client.post(f'/api/admin/properties/{property_id}/rooms',json={'name':'Silver En Suite','room_type':'En suite','price':315,'currency':'GBP','price_period':'week','rate_checked_at':'2026-10-28'},headers=ha)
        assert room.status_code==201,room.text
        assert client.get('/api/properties?q=Kingston').json()[0]['from_price']==315
        assert len(client.get('/api/properties?max_price=300').json())==0
        assert client.get(f'/api/properties/{slug}').json()['rooms'][0]['name']=='Silver En Suite'
        newuser=client.post('/api/auth/register',json={'name':'Student Tester','email':'student@example.com','password':'long-enough-password'})
        assert newuser.status_code==201,newuser.text
        hs={'Authorization':'Bearer '+newuser.json()['token']}
        assert client.patch(f'/api/admin/properties/{property_id}',json=data,headers=hs).status_code==403
        assert client.post(f'/api/me/saved/{property_id}',headers=hs).status_code==201
        payload={'property_id':property_id,'room_id':room.json()['id'],'name':'Student Tester','email':'student@example.com','consent':True}
        assert client.post('/api/enquiries',json={**payload,'consent':False}).status_code==422
        inquiry=client.post('/api/enquiries',json=payload,headers=hs)
        assert inquiry.status_code==201,inquiry.text
        eid=inquiry.json()['id']
        assert len(client.get('/api/me/overview',headers=hs).json()['enquiries'])==1
        assert client.patch(f'/api/admin/enquiries/{eid}',json={'status':'contacted'},headers=ha).status_code==200
        assert client.get('/api/me/overview',headers=hs).json()['enquiries'][0]['status']=='contacted'
        cb=client.post('/api/admin/cashback',json={'enquiry_id':eid,'amount':40,'currency':'GBP','status':'eligible'},headers=ha)
        assert cb.status_code==201,cb.text
        assert client.get('/api/me/overview',headers=hs).json()['cashback'][0]['status']=='eligible'
        assert client.get('/api/admin/enquiries').status_code==401
        assert client.get('/api/admin/summary',headers=ha).json()['properties']==1


def test_repeatable_listing_groups_and_picture_layout_roundtrip():
    with TestClient(api.app) as client:
        admin = client.post('/api/auth/login', json={'email':'admin@example.com','password':'not-a-real-admin-password'})
        ha = {'Authorization':'Bearer '+admin.json()['token']}
        property_json = {
            'name':'Student Residence Repeatable Example', 'city':'Manchester', 'published':True,
            'highlights':['All bills included','On-site study area','Security'],
            'amenities':['Wi-Fi','Bike storage','Common room','Laundry'],
            'faq':[{'question':'Are bills included?','answer':'Yes'},{'question':'Is there bike storage?','answer':'Yes'}],
            'gallery':[
                {'url':'https://example.com/room-a.jpg','alt':'En suite bedroom','category':'Rooms','layout':'regular'},
                {'url':'https://example.com/building.jpg','alt':'Building exterior','category':'Exterior','layout':'large'},
                {'url':'https://example.com/lounge.jpg','alt':'Common lounge','category':'Shared spaces','layout':'regular'},
            ],
            'floorplans':[{'url':'https://example.com/floorplan.jpg','alt':'Floor 2','layout':'large'}],
            'offers':[{'title':'Welcome offer','description':'Eligibility to confirm'}],
            'landmarks':[{'name':'Campus','detail':'Nearby'}],
        }
        created=client.post('/api/admin/properties',json=property_json,headers=ha)
        assert created.status_code==201,created.text
        record=created.json()
        assert record['gallery'][1]['layout']=='large'
        assert record['gallery'][1]['alt']=='Building exterior'
        assert record['floorplans'][0]['layout']=='large'
        assert len(record['highlights'])==3
        public=client.get('/api/properties/'+record['slug'])
        assert public.status_code==200,public.text
        assert public.json()['gallery'][1]['layout']=='large'
        assert public.json()['faq'][1]['question']=='Is there bike storage?'
        updated={**property_json,'highlights':list(reversed(property_json['highlights'])),
                 'gallery':[property_json['gallery'][1],property_json['gallery'][0]]}
        saved=client.patch('/api/admin/properties/'+str(record['id']),json=updated,headers=ha)
        assert saved.status_code==200,saved.text
        after=client.get('/api/properties/'+record['slug']).json()
        assert after['highlights'][0]=='Security'
        assert [p['layout'] for p in after['gallery']]==['large','regular']
        assert after['gallery'][0]['category']=='Exterior'
        rejected=client.patch('/api/admin/properties/'+str(record['id']),json={**updated,
            'gallery':[{'url':'https://example.com/a.jpg','layout':'ultra-large'}]},headers=ha)
        assert rejected.status_code==422
        rejected_url=client.patch('/api/admin/properties/'+str(record['id']),json={**updated,
            'gallery':[{'url':'javascript:alert(1)','layout':'large'}]},headers=ha)
        assert rejected_url.status_code==422
        assert client.get('/api/properties/'+record['slug']).json()['gallery'][0]['layout']=='large'
