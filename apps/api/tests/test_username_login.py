"""Username and local-only demo authentication regressions."""
import os
os.environ.update({
  'DATABASE_URL':'sqlite:///:memory:',
  'JWT_SECRET':'ci-secret-with-more-than-32-characters',
  'ADMIN_EMAIL':'admin@example.com',
  'ADMIN_PASSWORD':'not-a-real-admin-password',
  'APP_ENVIRONMENT':'testing',
  'DEV_AUTO_VERIFY_EMAIL':'1',
})
from fastapi.testclient import TestClient
import pytest
import app as api

@pytest.fixture
def client():
    api.Base.metadata.drop_all(api.engine)
    with TestClient(api.app) as c:yield c

def test_legacy_email_login_and_username_login(client):
    r=client.post('/api/auth/login',json={'email':'admin@example.com','password':'not-a-real-admin-password'})
    assert r.status_code==200,r.text
    reg=client.post('/api/auth/register',json={'name':'Student Demo','email':'student@example.com','username':'Student_01','password':'long-student-password'})
    assert reg.status_code==201,reg.text
    assert client.post('/api/auth/login',json={'identifier':'STUDENT_01','password':'long-student-password'}).status_code==200
    assert client.post('/api/auth/login',json={'identifier':'student@example.com','password':'long-student-password'}).status_code==200

def test_username_conflict_and_reserved_username(client):
    data={'name':'Student Demo','email':'one@example.com','username':'repeat-user','password':'long-student-password'}
    assert client.post('/api/auth/register',json=data).status_code==201
    data['email']='two@example.com';data['username']='REPEAT-USER'
    assert client.post('/api/auth/register',json=data).status_code==409
    data['email']='three@example.com';data['username']='Admin'
    assert client.post('/api/auth/register',json=data).status_code==422

def test_exact_local_demo_and_production_disable(monkeypatch):
    api.Base.metadata.drop_all(api.engine)
    monkeypatch.setattr(api,'APP_ENVIRONMENT','development')
    monkeypatch.setattr(api,'LOCAL_DEMO_MODE',True)
    monkeypatch.setattr(api,'CORS_ORIGIN','http://localhost:8081')
    monkeypatch.setattr(api,'DEMO_ADMIN_PASSWORD','Admin@123')
    monkeypatch.setattr(api,'DEMO_ADMIN_USERNAME','Admin')
    with TestClient(api.app) as client:
        r=client.post('/api/auth/login',json={'identifier':'Admin','password':'Admin@123'})
        assert r.status_code==200,r.text
        assert r.json()['user']['role']=='admin'
        headers={'Authorization':'Bearer '+r.json()['token']}
        assert client.get('/api/me',headers=headers).status_code==200
        monkeypatch.setattr(api,'APP_ENVIRONMENT','production')
        assert client.post('/api/auth/login',json={'identifier':'Admin','password':'Admin@123'}).status_code==401
        assert client.get('/api/me',headers=headers).status_code==401
