"""Accom by Emlen: property directory, student portal and listing operations API.

This first implementation intentionally excludes rent collection and booking confirmation.
"""
import os
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, create_engine, func, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./accom-local.db')
JWT_SECRET = os.getenv('JWT_SECRET', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
CORS_ORIGIN = os.getenv('CORS_ORIGIN', 'http://localhost:5173')
SQLITE = DATABASE_URL.startswith('sqlite')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if SQLITE else {}, poolclass=StaticPool if DATABASE_URL == 'sqlite:///:memory:' else None)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
ph = PasswordHasher()
auth_scheme = HTTPBearer(auto_error=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(250), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30), default='student')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Property(Base):
    __tablename__ = 'properties'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(220))
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    city: Mapped[str] = mapped_column(String(120), index=True)
    country: Mapped[str] = mapped_column(String(90), default='United Kingdom')
    address: Mapped[str] = mapped_column(Text, default='')
    postcode: Mapped[str] = mapped_column(String(30), default='')
    university: Mapped[str] = mapped_column(String(180), default='')
    description: Mapped[str] = mapped_column(Text, default='')
    highlights: Mapped[list] = mapped_column(JSON, default=list)
    amenities: Mapped[list] = mapped_column(JSON, default=list)
    policies: Mapped[list] = mapped_column(JSON, default=list)
    faq: Mapped[list] = mapped_column(JSON, default=list)
    landmarks: Mapped[list] = mapped_column(JSON, default=list)
    gallery: Mapped[list] = mapped_column(JSON, default=list)
    floorplans: Mapped[list] = mapped_column(JSON, default=list)
    tour_url: Mapped[str] = mapped_column(Text, default='')
    offers: Mapped[list] = mapped_column(JSON, default=list)
    reviews: Mapped[list] = mapped_column(JSON, default=list)
    review_source_url: Mapped[str] = mapped_column(Text, default='')
    review_score: Mapped[Decimal | None] = mapped_column(Numeric(3,1), nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seo_title: Mapped[str] = mapped_column(String(250), default='')
    meta_description: Mapped[str] = mapped_column(String(400), default='')
    noindex: Mapped[bool] = mapped_column(Boolean, default=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    rooms: Mapped[list['Room']] = relationship(back_populates='property', cascade='all, delete-orphan')

class Room(Base):
    __tablename__ = 'rooms'
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey('properties.id'), index=True)
    name: Mapped[str] = mapped_column(String(180))
    room_type: Mapped[str] = mapped_column(String(40), default='En suite')
    details: Mapped[str] = mapped_column(Text, default='')
    size_sqm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    kitchen: Mapped[str] = mapped_column(String(70), default='')
    bathroom: Mapped[str] = mapped_column(String(70), default='')
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default='GBP')
    price_period: Mapped[str] = mapped_column(String(20), default='week')
    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    availability: Mapped[str] = mapped_column(String(30), default='enquire')
    rate_checked_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, default='')
    image_url: Mapped[str] = mapped_column(Text, default='')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    property: Mapped[Property] = relationship(back_populates='rooms')

class Enquiry(Base):
    __tablename__ = 'enquiries'
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey('properties.id'), index=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey('rooms.id'), nullable=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(250), index=True)
    phone: Mapped[str] = mapped_column(String(50), default='')
    university: Mapped[str] = mapped_column(String(180), default='')
    move_in_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    message: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(30), default='new')
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class SavedProperty(Base):
    __tablename__ = 'saved_properties'
    __table_args__ = (UniqueConstraint('student_id','property_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey('properties.id'), index=True)

class Cashback(Base):
    __tablename__ = 'cashbacks'
    id: Mapped[int] = mapped_column(primary_key=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey('enquiries.id'), unique=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12,2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default='GBP')
    status: Mapped[str] = mapped_column(String(30), default='under_review')
    notes: Mapped[str] = mapped_column(Text, default='')

class Audit(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    event: Mapped[str] = mapped_column(String(90))
    reference: Mapped[str] = mapped_column(String(140))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

app = FastAPI(title='Accom by Emlen API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=[CORS_ORIGIN], allow_credentials=True, allow_methods=['GET','POST','PATCH','DELETE'], allow_headers=['Authorization','Content-Type'])

@app.on_event('startup')
def startup():
    Base.metadata.create_all(engine)  # bootstrap for v0.1; replace with Alembic before production
    if ADMIN_EMAIL and ADMIN_PASSWORD and len(ADMIN_PASSWORD) >= 12:
        with SessionLocal() as db:
            if not db.scalar(select(User).where(User.email==ADMIN_EMAIL.lower())):
                db.add(User(name='Administrator',email=ADMIN_EMAIL.lower(),password_hash=ph.hash(ADMIN_PASSWORD),role='admin'))
                db.commit()

def get_db():
    with SessionLocal() as db:
        yield db

def require_user(creds: HTTPAuthorizationCredentials | None = Depends(auth_scheme), db: Session = Depends(get_db)) -> User:
    if not creds or not JWT_SECRET or len(JWT_SECRET) < 32:
        raise HTTPException(401,'Sign in required')
    try:
        payload=jwt.decode(creds.credentials,JWT_SECRET,algorithms=['HS256'])
        user=db.get(User,int(payload['sub']))
        if not user or not user.active:
            raise ValueError('inactive')
        return user
    except Exception:
        raise HTTPException(401,'Invalid or expired session')

def require_admin(user: User=Depends(require_user)) -> User:
    if user.role not in ('admin','editor'):
        raise HTTPException(403,'Staff only')
    return user

def require_manager(user: User=Depends(require_user)) -> User:
    if user.role!='admin':
        raise HTTPException(403,'Admin only')
    return user

def log(db: Session, user: User, event: str, reference: str):
    db.add(Audit(actor_id=user.id,event=event,reference=reference))

def token(user):
    if len(JWT_SECRET) < 32:
        raise HTTPException(503,'Configure JWT_SECRET before accepting logins')
    return jwt.encode({'sub':str(user.id),'role':user.role,'exp':datetime.now(timezone.utc)+timedelta(hours=12)},JWT_SECRET,algorithm='HS256')

def user_json(u):
    return {'id':u.id,'name':u.name,'email':u.email,'role':u.role}

def room_json(r):
    return {'id':r.id,'property_id':r.property_id,'name':r.name,'room_type':r.room_type,'details':r.details,'size_sqm':float(r.size_sqm) if r.size_sqm is not None else None,'kitchen':r.kitchen,'bathroom':r.bathroom,'price':float(r.price) if r.price is not None else None,'currency':r.currency,'price_period':r.price_period,'available_from':r.available_from.isoformat() if r.available_from else None,'availability':r.availability,'rate_checked_at':r.rate_checked_at.isoformat() if r.rate_checked_at else None,'source_url':r.source_url,'image_url':r.image_url,'active':r.active}

def prop_json(p, detail=False):
    rooms=[room_json(r) for r in p.rooms if r.active]
    prices=[r['price'] for r in rooms if r['price'] is not None]
    d={'id':p.id,'name':p.name,'slug':p.slug,'city':p.city,'country':p.country,'address':p.address,'postcode':p.postcode,'university':p.university,'description':p.description,'gallery':p.gallery,'published':p.published,'verified_at':p.verified_at.isoformat() if p.verified_at else None,'from_price':min(prices) if prices else None,'currency':next((r['currency'] for r in rooms if r['price'] is not None),'GBP'),'price_period':next((r['price_period'] for r in rooms if r['price'] is not None),'week')}
    if detail:d.update({'highlights':p.highlights,'amenities':p.amenities,'policies':p.policies,'faq':p.faq,'landmarks':p.landmarks,'floorplans':p.floorplans,'tour_url':p.tour_url,'offers':p.offers,'reviews':p.reviews,'review_source_url':p.review_source_url,'review_score':float(p.review_score) if p.review_score is not None else None,'review_count':p.review_count,'seo_title':p.seo_title,'meta_description':p.meta_description,'noindex':p.noindex,'rooms':rooms})
    return d

def slugify(t):
    return re.sub(r'^-+|-+$','',re.sub(r'[^a-z0-9]+','-',t.lower()))[:225]

class Credentials(BaseModel):
    email: EmailStr
    password: str
class Registration(Credentials):
    name: str = Field(min_length=2,max_length=150)
class MediaInput(BaseModel):
    """An image is both an asset and a per-image layout choice."""
    url: str = Field(min_length=9, max_length=2048)
    alt: str = Field(default='', max_length=240)
    category: str = Field(default='Photos', max_length=100)
    layout: Literal['regular', 'large'] = 'regular'

    @field_validator('url')
    @classmethod
    def valid_web_image(cls, value: str):
        if not re.fullmatch(r'https?://[^\s]+', value):
            raise ValueError('Use a full HTTP(S) image URL')
        return value

class PropertyInput(BaseModel):
    name: str = Field(min_length=3,max_length=220)
    slug: str = ''
    city: str = Field(min_length=2,max_length=120)
    country: str = 'United Kingdom'
    address: str = ''
    postcode: str = ''
    university: str = ''
    description: str = ''
    highlights: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    policies: list[dict] = Field(default_factory=list)
    faq: list[dict] = Field(default_factory=list)
    landmarks: list[dict] = Field(default_factory=list)
    gallery: list[MediaInput] = Field(default_factory=list)
    floorplans: list[MediaInput] = Field(default_factory=list)
    tour_url: str = ''
    offers: list[dict] = Field(default_factory=list)
    reviews: list[dict] = Field(default_factory=list)
    review_source_url: str = ''
    review_score: Decimal | None = Field(default=None,ge=0,le=5)
    review_count: int | None = Field(default=None,ge=0)
    seo_title: str = ''
    meta_description: str = ''
    noindex: bool = False
    published: bool = False
class RoomInput(BaseModel):
    name: str = Field(min_length=2,max_length=180)
    room_type: str = 'En suite'
    details: str = ''
    size_sqm: Decimal | None = Field(default=None,ge=0)
    kitchen: str = ''
    bathroom: str = ''
    price: Decimal | None = Field(default=None,ge=0)
    currency: str = Field(default='GBP',pattern=r'^[A-Z]{3}$')
    price_period: Literal['week','month'] = 'week'
    available_from: date | None = None
    availability: Literal['available','enquire','unavailable'] = 'enquire'
    rate_checked_at: date | None = None
    source_url: str = ''
    image_url: str = ''
    active: bool = True
class EnquiryInput(BaseModel):
    property_id: int
    room_id: int | None = None
    name: str = Field(min_length=2,max_length=160)
    email: EmailStr
    phone: str = Field(default='',max_length=50)
    university: str = ''
    move_in_date: date | None = None
    message: str = Field(default='',max_length=3000)
    consent: bool
class EnquiryUpdate(BaseModel):
    status: Literal['new','contacted','in_progress','applied','booked','closed'] | None = None
    assigned_to_id: int | None = None
class CashbackInput(BaseModel):
    enquiry_id: int
    amount: Decimal | None = Field(default=None,ge=0)
    currency: str = 'GBP'
    status: Literal['under_review','eligible','approved','paid','ineligible'] = 'under_review'
    notes: str = ''

@app.get('/api/health')
def health():return {'status':'ok'}

@app.post('/api/auth/register',status_code=201)
def register(data:Registration,db:Session=Depends(get_db)):
    if len(data.password)<12:raise HTTPException(422,'Password must have at least 12 characters')
    if db.scalar(select(User).where(User.email==data.email.lower())):raise HTTPException(409,'Email already registered')
    u=User(name=data.name,email=data.email.lower(),password_hash=ph.hash(data.password),role='student');db.add(u);db.commit();db.refresh(u)
    return {'token':token(u),'user':user_json(u)}

@app.post('/api/auth/login')
def login(data:Credentials,db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==data.email.lower()))
    if not u or not u.active:raise HTTPException(401,'Incorrect credentials')
    try:ph.verify(u.password_hash,data.password)
    except Exception:raise HTTPException(401,'Incorrect credentials')
    return {'token':token(u),'user':user_json(u)}

@app.get('/api/me')
def me(user:User=Depends(require_user)):return user_json(user)

@app.get('/api/properties')
def properties(q:str='',city:str='',university:str='',room_type:str='',max_price:float|None=Query(default=None,ge=0),db:Session=Depends(get_db)):
    qry=select(Property).where(Property.published.is_(True))
    if q:qry=qry.where(or_(Property.name.ilike('%'+q+'%'),Property.city.ilike('%'+q+'%'),Property.university.ilike('%'+q+'%')))
    if city:qry=qry.where(Property.city.ilike('%'+city+'%'))
    if university:qry=qry.where(Property.university.ilike('%'+university+'%'))
    ps=db.scalars(qry.order_by(Property.name)).all()
    result=[]
    for p in ps:
        rooms=[r for r in p.rooms if r.active]
        if room_type and not any(r.room_type.lower()==room_type.lower() for r in rooms):continue
        if max_price is not None and not any(r.price is not None and r.price<=Decimal(str(max_price)) for r in rooms):continue
        result.append(prop_json(p))
    return result

@app.get('/api/properties/{slug}')
def public_property(slug:str,db:Session=Depends(get_db)):
    p=db.scalar(select(Property).where(Property.slug==slug,Property.published.is_(True)))
    if not p:raise HTTPException(404,'Listing not found')
    return prop_json(p,True)

@app.post('/api/enquiries',status_code=201)
def create_enquiry(data:EnquiryInput,creds:HTTPAuthorizationCredentials | None=Depends(auth_scheme),db:Session=Depends(get_db)):
    if not data.consent:raise HTTPException(422,'Contact consent is required')
    p=db.get(Property,data.property_id)
    if not p or not p.published:raise HTTPException(404,'Listing not found')
    if data.room_id:
        r=db.get(Room,data.room_id)
        if not r or r.property_id!=p.id or not r.active:raise HTTPException(422,'Room does not belong to listing')
    student=None
    if creds and len(JWT_SECRET)>=32:
        try:
            claims=jwt.decode(creds.credentials,JWT_SECRET,algorithms=['HS256'])
            candidate=db.get(User,int(claims['sub']))
            if candidate and candidate.active and candidate.role=='student':
                if candidate.email!=data.email.lower():raise HTTPException(422,'Use your signed-in email address for portal tracking')
                student=candidate
        except HTTPException:raise
        except Exception:raise HTTPException(401,'Invalid or expired session')
    e=Enquiry(property_id=p.id,room_id=data.room_id,student_id=student.id if student else None,name=data.name,email=data.email.lower(),phone=data.phone,university=data.university,move_in_date=data.move_in_date,message=data.message,consent_at=datetime.now(timezone.utc))
    db.add(e);db.commit();db.refresh(e)
    return {'id':e.id,'status':e.status,'message':'Enquiry received; this is not a booking confirmation.'}

@app.get('/api/me/overview')
def student_overview(user:User=Depends(require_user),db:Session=Depends(get_db)):
    if user.role!='student':raise HTTPException(403,'Student account required')
    saves=db.scalars(select(SavedProperty).where(SavedProperty.student_id==user.id)).all()
    enquiry_rows=db.scalars(select(Enquiry).where(Enquiry.student_id==user.id).order_by(Enquiry.created_at.desc())).all()
    cashback=[]
    if enquiry_rows:
        ids=[e.id for e in enquiry_rows]
        cashback=[{'enquiry_id':c.enquiry_id,'amount':float(c.amount) if c.amount is not None else None,'currency':c.currency,'status':c.status} for c in db.scalars(select(Cashback).where(Cashback.enquiry_id.in_(ids))).all()]
    return {'user':user_json(user),'saved':[prop_json(p) for s in saves if (p:=db.get(Property,s.property_id)) and p.published],'enquiries':[{'id':e.id,'property':db.get(Property,e.property_id).name,'status':e.status,'assigned_consultant':db.get(User,e.assigned_to_id).name if e.assigned_to_id and db.get(User,e.assigned_to_id) else None,'created_at':e.created_at.isoformat()} for e in enquiry_rows],'cashback':cashback}

@app.post('/api/me/saved/{property_id}',status_code=201)
def save_property(property_id:int,user:User=Depends(require_user),db:Session=Depends(get_db)):
    if user.role!='student':raise HTTPException(403,'Student account required')
    p=db.get(Property,property_id)
    if not p or not p.published:raise HTTPException(404,'Listing not found')
    if not db.scalar(select(SavedProperty).where(SavedProperty.student_id==user.id,SavedProperty.property_id==p.id)):
        db.add(SavedProperty(student_id=user.id,property_id=p.id));db.commit()
    return {'saved':True}

@app.delete('/api/me/saved/{property_id}')
def unsave_property(property_id:int,user:User=Depends(require_user),db:Session=Depends(get_db)):
    s=db.scalar(select(SavedProperty).where(SavedProperty.student_id==user.id,SavedProperty.property_id==property_id))
    if s:db.delete(s);db.commit()
    return {'saved':False}

@app.get('/api/admin/summary')
def summary(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return {'properties':db.scalar(select(func.count(Property.id))),'published':db.scalar(select(func.count(Property.id)).where(Property.published.is_(True))),'rooms':db.scalar(select(func.count(Room.id))),'enquiries':db.scalar(select(func.count(Enquiry.id))),'new_enquiries':db.scalar(select(func.count(Enquiry.id)).where(Enquiry.status=='new'))}

@app.get('/api/admin/properties')
def admin_properties(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [prop_json(p,True) for p in db.scalars(select(Property).order_by(Property.id.desc())).all()]

@app.post('/api/admin/properties',status_code=201)
def add_property(data:PropertyInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    if data.published and user.role!='admin':raise HTTPException(403,'Only admins can publish')
    d=data.model_dump();d['slug']=slugify(d['slug'] or d['name'])
    if not d['slug']:raise HTTPException(422,'Invalid slug')
    if db.scalar(select(Property).where(Property.slug==d['slug'])):raise HTTPException(409,'Slug already in use')
    p=Property(**d);db.add(p);db.flush();log(db,user,'property.create',str(p.id));db.commit();db.refresh(p)
    return prop_json(p,True)

@app.patch('/api/admin/properties/{id}')
def update_property(id:int,data:PropertyInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    p=db.get(Property,id)
    if not p:raise HTTPException(404,'Listing not found')
    if user.role!='admin' and (p.published or data.published):raise HTTPException(403,'An admin must review published listings')
    d=data.model_dump();d['slug']=slugify(d['slug'] or d['name'])
    if not d['slug']:raise HTTPException(422,'Invalid slug')
    if db.scalar(select(Property).where(Property.slug==d['slug'],Property.id!=id)):raise HTTPException(409,'Slug already in use')
    for k,v in d.items():setattr(p,k,v)
    log(db,user,'property.update',str(p.id));db.commit();return prop_json(p,True)

@app.post('/api/admin/properties/{id}/rooms',status_code=201)
def add_room(id:int,data:RoomInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    if not db.get(Property,id):raise HTTPException(404,'Listing not found')
    r=Room(property_id=id,**data.model_dump());db.add(r);db.flush();log(db,user,'room.create',str(r.id));db.commit();return room_json(r)

@app.patch('/api/admin/rooms/{id}')
def update_room(id:int,data:RoomInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    r=db.get(Room,id)
    if not r:raise HTTPException(404,'Room not found')
    for k,v in data.model_dump().items():setattr(r,k,v)
    log(db,user,'room.update',str(r.id));db.commit();return room_json(r)

@app.get('/api/admin/enquiries')
def admin_enquiries(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [{'id':e.id,'property':db.get(Property,e.property_id).name,'property_id':e.property_id,'room_id':e.room_id,'student_id':e.student_id,'name':e.name,'email':e.email,'phone':e.phone,'university':e.university,'move_in_date':e.move_in_date.isoformat() if e.move_in_date else None,'message':e.message,'status':e.status,'assigned_to_id':e.assigned_to_id,'created_at':e.created_at.isoformat()} for e in db.scalars(select(Enquiry).order_by(Enquiry.id.desc())).all()]

@app.patch('/api/admin/enquiries/{id}')
def update_enquiry(id:int,data:EnquiryUpdate,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    e=db.get(Enquiry,id)
    if not e:raise HTTPException(404,'Enquiry not found')
    if data.assigned_to_id is not None:
        target=db.get(User,data.assigned_to_id)
        if not target or not target.active or target.role not in ('admin','editor'):raise HTTPException(422,'Assign only to active staff')
        e.assigned_to_id=target.id
    if data.status:e.status=data.status
    log(db,user,'enquiry.update',str(e.id));db.commit();return {'id':e.id,'status':e.status,'assigned_to_id':e.assigned_to_id}

@app.get('/api/admin/staff')
def staff(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [user_json(u) for u in db.scalars(select(User).where(User.role.in_(['admin','editor']),User.active.is_(True))).all()]

@app.get('/api/admin/cashback')
def admin_cashback(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [{'id':c.id,'enquiry_id':c.enquiry_id,'amount':float(c.amount) if c.amount is not None else None,'currency':c.currency,'status':c.status,'notes':c.notes} for c in db.scalars(select(Cashback)).all()]

@app.post('/api/admin/cashback',status_code=201)
def create_cashback(data:CashbackInput,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    if not db.get(Enquiry,data.enquiry_id):raise HTTPException(404,'Enquiry not found')
    if db.scalar(select(Cashback).where(Cashback.enquiry_id==data.enquiry_id)):raise HTTPException(409,'Cashback record exists')
    c=Cashback(**data.model_dump());db.add(c);db.flush();log(db,user,'cashback.create',str(c.id));db.commit();return {'id':c.id,'status':c.status}

@app.patch('/api/admin/cashback/{id}')
def update_cashback(id:int,data:CashbackInput,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    c=db.get(Cashback,id)
    if not c:raise HTTPException(404,'Record not found')
    if c.enquiry_id!=data.enquiry_id:raise HTTPException(422,'Cannot reassign a cashback to another enquiry')
    for k,v in data.model_dump().items():setattr(c,k,v)
    log(db,user,'cashback.update',str(c.id));db.commit();return {'id':c.id,'status':c.status}
