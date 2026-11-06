"""Accom by Emlen: property directory, student portal and listing operations API.

This first implementation intentionally excludes rent collection and booking confirmation.
"""
import os
import re
import json
import hashlib
import io
import uuid
import boto3
from PIL import Image, UnidentifiedImageError
import secrets
import smtplib
from bs4 import BeautifulSoup
from email.message import EmailMessage
from html import escape
from urllib.parse import quote
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, FastAPI, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, create_engine, func, or_, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool
from property_runtime import render_property
from demo_seed import seed_kingston

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./accom-local.db')
JWT_SECRET = os.getenv('JWT_SECRET', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
LOCAL_DEMO_MODE = os.getenv('LOCAL_DEMO_MODE', '0') == '1'
DEMO_ADMIN_USERNAME = os.getenv('DEMO_ADMIN_USERNAME', 'Admin')
DEMO_ADMIN_PASSWORD = os.getenv('DEMO_ADMIN_PASSWORD', '')
DEMO_ADMIN_EMAIL = 'demo-admin@accom.example'
CORS_ORIGIN = os.getenv('CORS_ORIGIN', 'http://localhost:5173')
PUBLIC_SITE_URL = os.getenv('PUBLIC_SITE_URL', 'https://accombyemlen.com').rstrip('/')
APP_ENVIRONMENT = os.getenv('APP_ENVIRONMENT','development')
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_FROM = os.getenv('SMTP_FROM', '')
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', '')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL','')
S3_BUCKET = os.getenv('S3_BUCKET','accom-assets')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY','')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY','')
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
    username: Mapped[str | None] = mapped_column(String(40), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30), default='student')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_version: Mapped[int] = mapped_column(Integer, default=1)
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
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    edit_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
    image_alt: Mapped[str] = mapped_column(String(240), default='')
    image_layout: Mapped[str] = mapped_column(String(15), default='regular')
    tenancies: Mapped[list] = mapped_column(JSON,default=list,nullable=False)
    edit_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
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
    booking_reference: Mapped[str] = mapped_column(String(120), default='')
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

class EmailVerification(Base):
    __tablename__ = 'email_verifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class RateEvent(Base):
    __tablename__ = 'rate_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(35), index=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class EnquiryNote(Base):
    __tablename__ = 'enquiry_notes'
    id: Mapped[int] = mapped_column(primary_key=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey('enquiries.id'), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MediaAsset(Base):
    __tablename__='media_assets'
    id:Mapped[int]=mapped_column(primary_key=True)
    object_key:Mapped[str]=mapped_column(String(200),unique=True)
    filename:Mapped[str]=mapped_column(String(220))
    mime_type:Mapped[str]=mapped_column(String(70))
    alt:Mapped[str]=mapped_column(String(240),default='')
    bytes:Mapped[int]=mapped_column(Integer)
    uploaded_by:Mapped[int]=mapped_column(ForeignKey('users.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class ContentTemplate(Base):
    __tablename__='content_templates'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(160))
    source_html:Mapped[str]=mapped_column(Text)
    sections:Mapped[list]=mapped_column(JSON,default=list)
    fields:Mapped[list]=mapped_column(JSON,default=list)
    approved:Mapped[bool]=mapped_column(Boolean,default=False)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class EditorialPage(Base):
    __tablename__='editorial_pages'
    id:Mapped[int]=mapped_column(primary_key=True)
    template_id:Mapped[int]=mapped_column(ForeignKey('content_templates.id'))
    title:Mapped[str]=mapped_column(String(220))
    slug:Mapped[str]=mapped_column(String(240),unique=True)
    values:Mapped[dict]=mapped_column(JSON,default=dict)
    seo_title:Mapped[str]=mapped_column(String(250),default='')
    meta_description:Mapped[str]=mapped_column(String(400),default='')
    noindex:Mapped[bool]=mapped_column(Boolean,default=False)
    published:Mapped[bool]=mapped_column(Boolean,default=False)
    archived:Mapped[bool]=mapped_column(Boolean,default=False)
    edit_version:Mapped[int]=mapped_column(Integer,default=1,nullable=False)

class Audit(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    event: Mapped[str] = mapped_column(String(90))
    reference: Mapped[str] = mapped_column(String(140))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

app = FastAPI(title='Accom by Emlen API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=[CORS_ORIGIN], allow_credentials=True, allow_methods=['GET','POST','PATCH','DELETE'], allow_headers=['Authorization','Content-Type'])

def local_demo_enabled():
    # Short demo credentials are never available in a production environment.
    return (APP_ENVIRONMENT == 'development' and LOCAL_DEMO_MODE
            and CORS_ORIGIN.rstrip('/') in ('http://localhost:8081','http://127.0.0.1:8081',
                                            'http://localhost:5173','http://127.0.0.1:5173'))

def clean_username(raw: str | None, *, reserved: bool = False) -> str | None:
    if not raw: return None
    name=raw.strip().lower()
    if not re.fullmatch(r'[a-z][a-z0-9_.-]{2,31}',name):
        raise HTTPException(422,'Username must have 3–32 characters and begin with a letter')
    if not reserved and name in ('admin','administrator','root','system','support','accom'):
        raise HTTPException(422,'This username is reserved')
    return name

@app.on_event('startup')
def startup():
    if SQLITE or os.getenv('ALLOW_BOOTSTRAP_SCHEMA') == '1':
        Base.metadata.create_all(engine)  # tests/local only; production runs Alembic before start
    if ADMIN_EMAIL and ADMIN_PASSWORD and len(ADMIN_PASSWORD) >= 12:
        with SessionLocal() as db:
            main_admin=db.scalar(select(User).where(User.email==ADMIN_EMAIL.lower()))
            if not main_admin:
                username=clean_username(ADMIN_USERNAME,reserved=True)
                if username and db.scalar(select(User).where(User.username==username)):
                    raise RuntimeError('ADMIN_USERNAME already assigned to a different user')
                db.add(User(name='Administrator',email=ADMIN_EMAIL.lower(),username=username,
                            password_hash=ph.hash(ADMIN_PASSWORD),role='admin',email_verified=True))
                db.commit()
            elif ADMIN_USERNAME and main_admin.role=='admin' and not main_admin.username:
                username=clean_username(ADMIN_USERNAME,reserved=True)
                if not db.scalar(select(User).where(User.username==username)):
                    main_admin.username=username
                    db.commit()
    # Demo account is explicitly local and becomes inactive outside demo mode.
    with SessionLocal() as db:
        demo=db.scalar(select(User).where(User.email==DEMO_ADMIN_EMAIL))
        if local_demo_enabled():
            username=clean_username(DEMO_ADMIN_USERNAME,reserved=True)
            if not DEMO_ADMIN_PASSWORD or len(DEMO_ADMIN_PASSWORD)<8:
                raise RuntimeError('DEMO_ADMIN_PASSWORD must have at least 8 characters')
            clash=db.scalar(select(User).where(User.username==username))
            if clash and (not demo or clash.id!=demo.id):
                raise RuntimeError('Demo username already assigned to another user')
            if not demo:
                db.add(User(name='Local demo administrator',email=DEMO_ADMIN_EMAIL,
                            username=username,password_hash=ph.hash(DEMO_ADMIN_PASSWORD),
                            role='admin',email_verified=True))
            else:
                demo.username=username;demo.active=True
                demo.password_hash=ph.hash(DEMO_ADMIN_PASSWORD)
                demo.auth_version+=1
            db.commit()
        elif demo and demo.active:
            demo.active=False;demo.auth_version+=1;db.commit()

    if APP_ENVIRONMENT=='development' and os.getenv('SEED_ACCOM_DEMO')=='1':
        with SessionLocal() as db:
            seed_kingston(db,Property,Room)

def get_db():
    with SessionLocal() as db:
        yield db

def require_user(creds: HTTPAuthorizationCredentials | None = Depends(auth_scheme), db: Session = Depends(get_db)) -> User:
    if not creds or not JWT_SECRET or len(JWT_SECRET) < 32:
        raise HTTPException(401,'Sign in required')
    try:
        payload=jwt.decode(creds.credentials,JWT_SECRET,algorithms=['HS256'])
        user=db.get(User,int(payload['sub']))
        if not user or not user.active or payload.get('av') != user.auth_version:
            raise ValueError('inactive')
        if user.email==DEMO_ADMIN_EMAIL and not local_demo_enabled():
            raise ValueError('demo account disabled')
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
    return jwt.encode({'sub':str(user.id),'role':user.role,'av':user.auth_version,'exp':datetime.now(timezone.utc)+timedelta(hours=8)},JWT_SECRET,algorithm='HS256')

def user_json(u):
    return {'id':u.id,'name':u.name,'email':u.email,'username':u.username,'role':u.role,'active':u.active,'email_verified':u.email_verified}

def room_json(r):
    return {'id':r.id,'property_id':r.property_id,'name':r.name,'room_type':r.room_type,'details':r.details,'size_sqm':float(r.size_sqm) if r.size_sqm is not None else None,'kitchen':r.kitchen,'bathroom':r.bathroom,'price':float(r.price) if r.price is not None else None,'currency':r.currency,'price_period':r.price_period,'available_from':r.available_from.isoformat() if r.available_from else None,'availability':r.availability,'rate_checked_at':r.rate_checked_at.isoformat() if r.rate_checked_at else None,'source_url':r.source_url,'image_url':r.image_url,'image_alt':r.image_alt,'image_layout':r.image_layout,'tenancies':r.tenancies or [],'edit_version':r.edit_version,'active':r.active}

def _public_rooms(p):
    return [r for r in p.rooms if r.active and r.availability != 'unavailable']

def _headline_rate(p):
    rated = [r for r in _public_rooms(p) if r.availability == 'available' and r.price is not None
             and (not r.rate_checked_at or r.rate_checked_at >= date.today()-timedelta(days=30))]
    groups = {(r.currency, r.price_period) for r in rated}
    if not rated or len(groups) != 1:
        return (None, 'GBP', 'week', 'Rates vary by currency or period' if len(groups)>1 else 'Ask about current rates')
    cheapest = min(rated, key=lambda r:r.price)
    return (float(cheapest.price), cheapest.currency, cheapest.price_period, '')

def prop_json(p, detail=False, staff=False):
    rooms=[room_json(r) for r in p.rooms if staff or (r.active and r.availability!='unavailable')]
    price,currency,period,note=_headline_rate(p)
    d={'id':p.id,'name':p.name,'slug':p.slug,'city':p.city,'country':p.country,'address':p.address,'postcode':p.postcode,'university':p.university,'description':p.description,'gallery':p.gallery,'published':p.published,'archived':p.archived,'is_demo':p.is_demo,'edit_version':p.edit_version,'verified_at':p.verified_at.isoformat() if p.verified_at else None,'from_price':price,'price_note':note,'currency':currency,'price_period':period}
    if detail:d.update({'highlights':p.highlights,'amenities':p.amenities,'policies':p.policies,'faq':p.faq,'landmarks':p.landmarks,'floorplans':p.floorplans,'tour_url':p.tour_url,'offers':p.offers,'reviews':p.reviews,'review_source_url':p.review_source_url,'review_score':float(p.review_score) if p.review_score is not None else None,'review_count':p.review_count,'seo_title':p.seo_title,'meta_description':p.meta_description,'noindex':p.noindex,'rooms':rooms})
    return d

def slugify(t):
    return re.sub(r'^-+|-+$','',re.sub(r'[^a-z0-9]+','-',t.lower()))[:225]

class Credentials(BaseModel):
    identifier: str | None = Field(default=None,max_length=250)
    email: str | None = Field(default=None,max_length=250)
    password: str

class Registration(BaseModel):
    name: str = Field(min_length=2,max_length=150)
    email: EmailStr
    password: str
    username: str | None = Field(default=None,max_length=40)
class MediaInput(BaseModel):
    """An image is both an asset and a per-image layout choice."""
    url: str = Field(min_length=9, max_length=2048)
    alt: str = Field(default='', max_length=240)
    category: str = Field(default='Photos', max_length=100)
    layout: Literal['regular', 'large'] = 'regular'

    @field_validator('url')
    @classmethod
    def valid_web_image(cls, value: str):
        if not (re.fullmatch(r'https://[^\s]+', value) or re.fullmatch(r'/api/media/[1-9][0-9]*',value) or re.fullmatch(r'/accom-template/assets/[a-z0-9_-]+\.(?:webp|png|jpg)',value)):
            raise ValueError('Use an HTTPS image URL or an image from the Accom media library')
        return value

class PairInput(BaseModel):
    question: str = Field(min_length=2,max_length=240)
    answer: str = Field(min_length=2,max_length=3500)
class LandmarkInput(BaseModel):
    name: str = Field(min_length=2,max_length=200)
    detail: str = Field(min_length=2,max_length=240)
class OfferInput(BaseModel):
    title: str = Field(min_length=2,max_length=200)
    description: str = Field(min_length=2,max_length=2500)
    valid_until: date | None = None
class ReviewInput(BaseModel):
    name: str = Field(min_length=2,max_length=180)
    quote: str = Field(min_length=2,max_length=2000)
    source_url: str = Field(pattern=r'^https://[^\s]+$')

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
    policies: list[PairInput] = Field(default_factory=list)
    faq: list[PairInput] = Field(default_factory=list)
    landmarks: list[LandmarkInput] = Field(default_factory=list)
    gallery: list[MediaInput] = Field(default_factory=list)
    floorplans: list[MediaInput] = Field(default_factory=list)
    tour_url: str = ''
    offers: list[OfferInput] = Field(default_factory=list)
    reviews: list[ReviewInput] = Field(default_factory=list)
    review_source_url: str = ''
    review_score: Decimal | None = Field(default=None,ge=0,le=5)
    review_count: int | None = Field(default=None,ge=0)
    seo_title: str = ''
    meta_description: str = ''
    noindex: bool = False
    published: bool = False
    is_demo: bool = False
    edit_version: int | None = Field(default=None,ge=1)
class TenancyInput(BaseModel):
    weeks: int = Field(ge=0,le=104)
    start: str = Field(default='',max_length=80)
    end: str = Field(default='',max_length=80)
    weekly: Decimal | None = Field(default=None,ge=0)
    availability: str = Field(default='Confirm availability',max_length=100)
    illustrative: bool = False

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
    image_alt: str = Field(default='',max_length=240)
    image_layout: Literal['regular','large'] = 'regular'
    tenancies: list[TenancyInput] = Field(default_factory=list,max_length=12)
    edit_version: int | None = Field(default=None,ge=1)
    parent_edit_version: int | None = Field(default=None,ge=1)
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
    booking_reference: str = Field(default='',max_length=120)
    status: Literal['new','contacted','in_progress','applied','booked','closed'] | None = None
    assigned_to_id: int | None = None
class CashbackInput(BaseModel):
    enquiry_id: int
    amount: Decimal | None = Field(default=None,ge=0)
    currency: str = 'GBP'
    status: Literal['under_review','eligible','approved','paid','ineligible'] = 'under_review'
    notes: str = ''

def _require_publish_ready(p, db):
    errors=[]
    if not p.address or len(p.address.strip())<5:errors.append('Property address')
    if not p.description or len(p.description.strip())<25:errors.append('Description (at least 25 characters)')
    if not p.gallery:errors.append('At least one approved property photo')
    if p.is_demo:errors.append('Convert demonstration listing to verified property before publishing')
    if any(t.get('illustrative') for r in p.rooms for t in (r.tenancies or [])):
        errors.append('Illustrative tenancy prices cannot be published')
    rooms=db.scalars(select(Room).where(Room.property_id==p.id,Room.active.is_(True))).all()
    if not rooms:errors.append('At least one active room')
    if errors:raise HTTPException(422,'Complete before publishing: '+', '.join(errors))

def _fingerprint(request):
    # Avoid trusting client-supplied X-Forwarded-For headers.
    address=request.client.host if request.client else 'unknown'
    return hashlib.sha256((JWT_SECRET+address).encode()).hexdigest()

def _throttle(db, request, action, limit, minutes):
    key=_fingerprint(request)
    since=datetime.now(timezone.utc)-timedelta(minutes=minutes)
    count=db.scalar(select(func.count(RateEvent.id)).where(RateEvent.fingerprint==key,RateEvent.action==action,RateEvent.at>=since)) or 0
    if count>=limit:raise HTTPException(429,'Too many requests. Try again later.')
    db.add(RateEvent(fingerprint=key,action=action));db.commit()

def _claim_guest_enquiries(db, user):
    if user.role=='student' and user.email_verified:
        for e in db.scalars(select(Enquiry).where(Enquiry.student_id.is_(None),Enquiry.email==user.email.lower())).all():
            e.student_id=user.id
        db.commit()

def _send_verification(to, raw_token):
    if not SMTP_HOST or not SMTP_FROM:raise HTTPException(503,'Student registration is temporarily unavailable; email service is not configured')
    msg=EmailMessage()
    msg['Subject']='Verify your Accom by Emlen student account'
    msg['From']=SMTP_FROM
    msg['To']=to
    msg.set_content(f'Verify your Accom student account with this link: {PUBLIC_SITE_URL}/verify-email?token={quote(raw_token)}\n\nThis link expires in 30 minutes.')
    port=int(os.getenv('SMTP_PORT','587'))
    with smtplib.SMTP(SMTP_HOST,port,timeout=12) as client:
        client.starttls()
        if os.getenv('SMTP_USER'):
            client.login(os.getenv('SMTP_USER'),os.getenv('SMTP_PASSWORD',''))
        client.send_message(msg)

@app.get('/api/health')
def health():return {'status':'ok'}

@app.post('/api/auth/register',status_code=201)
def register(data:Registration,request:Request,db:Session=Depends(get_db)):
    _throttle(db,request,'register',5,60)
    if len(data.password)<12:raise HTTPException(422,'Password must have at least 12 characters')
    if db.scalar(select(User).where(User.email==data.email.lower())):raise HTTPException(409,'Email already registered')
    username=clean_username(data.username)
    if username and db.scalar(select(User).where(User.username==username)):
        raise HTTPException(409,'Username already taken')
    dev_skip=(APP_ENVIRONMENT!='production' and os.getenv('DEV_AUTO_VERIFY_EMAIL')=='1')
    if not dev_skip and (not SMTP_HOST or not SMTP_FROM):raise HTTPException(503,'Email verification must be configured before student sign-up')
    u=User(name=data.name,email=data.email.lower(),username=username,password_hash=ph.hash(data.password),role='student',email_verified=dev_skip)
    db.add(u);db.flush()
    if dev_skip:
        _claim_guest_enquiries(db,u);db.commit();db.refresh(u)
        return {'token':token(u),'user':user_json(u),'verification_required':False}
    raw=secrets.token_urlsafe(36)
    db.add(EmailVerification(user_id=u.id,token_hash=hashlib.sha256(raw.encode()).hexdigest(),expires_at=datetime.now(timezone.utc)+timedelta(minutes=30)))
    db.commit()
    try:_send_verification(u.email,raw)
    except Exception:
        # Keep unverified, make email service failure visible without exposing token.
        raise HTTPException(503,'Could not send verification email; contact support')
    return {'verification_required':True,'message':'Check your email to verify your account.'}

class VerifyEmailInput(BaseModel):
    token: str = Field(min_length=30,max_length=200)

@app.post('/api/auth/verify-email')
def verify_email(data:VerifyEmailInput,db:Session=Depends(get_db)):
    row=db.scalar(select(EmailVerification).where(EmailVerification.token_hash==hashlib.sha256(data.token.encode()).hexdigest()))
    if not row:raise HTTPException(400,'Link invalid or already used')
    expires=row.expires_at.replace(tzinfo=timezone.utc) if row.expires_at.tzinfo is None else row.expires_at
    if expires<datetime.now(timezone.utc):raise HTTPException(400,'Verification link expired')
    u=db.get(User,row.user_id)
    if not u:raise HTTPException(404,'Account not found')
    u.email_verified=True;db.delete(row);_claim_guest_enquiries(db,u);db.commit();return {'verified':True}

@app.post('/api/auth/login')
def login(data:Credentials,request:Request,db:Session=Depends(get_db)):
    _throttle(db,request,'login',10,15)
    login_id=(data.identifier or data.email or '').strip().lower()
    if not login_id:raise HTTPException(422,'Enter your email or username')
    if '@' in login_id:
        u=db.scalar(select(User).where(User.email==login_id))
    else:
        u=db.scalar(select(User).where(User.username==login_id))
    if not u or not u.active or (u.email==DEMO_ADMIN_EMAIL and not local_demo_enabled()):
        raise HTTPException(401,'Incorrect credentials')
    try:ph.verify(u.password_hash,data.password)
    except Exception:raise HTTPException(401,'Incorrect credentials')
    if u.role=='student' and not u.email_verified:raise HTTPException(403,'Verify your email before signing in')
    _claim_guest_enquiries(db,u)
    return {'token':token(u),'user':user_json(u)}

class PasswordChange(BaseModel):
    current_password:str
    new_password:str=Field(min_length=12,max_length=128)
@app.post('/api/auth/change-password')
def change_password(data:PasswordChange,user:User=Depends(require_user),db:Session=Depends(get_db)):
    try:ph.verify(user.password_hash,data.current_password)
    except Exception:raise HTTPException(403,'Current password incorrect')
    user.password_hash=ph.hash(data.new_password);user.auth_version+=1
    db.commit();return {'changed':True,'sessions_revoked':True}

@app.get('/api/me')
def me(user:User=Depends(require_user)):return user_json(user)

@app.get('/api/properties')
def properties(q:str='',city:str='',university:str='',room_type:str='',max_price:float|None=Query(default=None,ge=0),db:Session=Depends(get_db)):
    qry=select(Property).where(Property.published.is_(True),Property.archived.is_(False))
    if q:qry=qry.where(or_(Property.name.ilike('%'+q+'%'),Property.city.ilike('%'+q+'%'),Property.university.ilike('%'+q+'%')))
    if city:qry=qry.where(Property.city.ilike('%'+city+'%'))
    if university:qry=qry.where(Property.university.ilike('%'+university+'%'))
    ps=db.scalars(qry.order_by(Property.name)).all()
    result=[]
    for p in ps:
        rooms=[r for r in p.rooms if r.active and r.availability=='available']
        if room_type or max_price is not None:
            matching=[r for r in rooms if (not room_type or r.room_type.lower()==room_type.lower())
                      and (max_price is None or (r.price is not None and r.price<=Decimal(str(max_price))
                      and (not r.rate_checked_at or r.rate_checked_at>=date.today()-timedelta(days=30))))]
            if not matching:continue
        result.append(prop_json(p))
    return result

@app.get('/api/properties/{slug}')
def public_property(slug:str,db:Session=Depends(get_db)):
    p=db.scalar(select(Property).where(Property.slug==slug,Property.published.is_(True),Property.archived.is_(False)))
    if not p:raise HTTPException(404,'Listing not found')
    return prop_json(p,True)

@app.post('/api/enquiries',status_code=201)
def create_enquiry(data:EnquiryInput,request:Request,creds:HTTPAuthorizationCredentials | None=Depends(auth_scheme),db:Session=Depends(get_db)):
    _throttle(db,request,'enquiry',8,60)
    if not data.consent:raise HTTPException(422,'Contact consent is required')
    p=db.get(Property,data.property_id)
    if not p or not p.published or p.archived:raise HTTPException(404,'Listing not found')
    if data.room_id:
        r=db.get(Room,data.room_id)
        if not r or r.property_id!=p.id or not r.active or r.availability=='unavailable':raise HTTPException(422,'Room does not belong to listing')
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
    recent=datetime.now(timezone.utc)-timedelta(minutes=2)
    existing=db.scalar(select(Enquiry).where(Enquiry.email==data.email.lower(),Enquiry.property_id==p.id,Enquiry.room_id==data.room_id,Enquiry.message==data.message,Enquiry.created_at>=recent).order_by(Enquiry.id.desc()).limit(1))
    if existing:return {'id':existing.id,'status':existing.status,'message':'Enquiry already received; this is not a booking confirmation.'}
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
    return {'properties':db.scalar(select(func.count(Property.id))),'published':db.scalar(select(func.count(Property.id)).where(Property.published.is_(True))),'rooms':db.scalar(select(func.count(Room.id)).where(Room.active.is_(True))),'inactive_rooms':db.scalar(select(func.count(Room.id)).where(Room.active.is_(False))),'enquiries':db.scalar(select(func.count(Enquiry.id))),'new_enquiries':db.scalar(select(func.count(Enquiry.id)).where(Enquiry.status=='new'))}

@app.get('/api/admin/properties')
def admin_properties(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [prop_json(p,True,staff=True) for p in db.scalars(select(Property).order_by(Property.id.desc())).all()]

def _serialize_data(model):
    return model.model_dump(mode='json',exclude={'edit_version','parent_edit_version'})

def _as_db(model):
    data=model.model_dump(exclude={'edit_version','parent_edit_version'})
    if isinstance(model,PropertyInput):data['offers']=[o.model_dump(mode='json') for o in model.offers]
    if isinstance(model,RoomInput):data['tenancies']=[t.model_dump(mode='json') for t in model.tenancies]
    return data

class NewPropertyDraft(BaseModel):
    name: str = Field(min_length=3, max_length=220)

@app.post('/api/admin/properties/draft',status_code=201)
def create_property_draft(data:NewPropertyDraft,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    """Create an unpublished property page with only a name."""
    name=data.name.strip()
    if len(name)<3:raise HTTPException(422,'Page name must contain at least 3 characters')
    base=slugify(name)
    if not base:raise HTTPException(422,'Enter a valid page name')
    candidate=base
    suffix=2
    while db.scalar(select(Property.id).where(Property.slug==candidate)):
        candidate=base[:213]+'-'+str(suffix)
        suffix+=1
        if suffix>9999:raise HTTPException(409,'Too many pages with this name')
    page=Property(name=name,slug=candidate,city='',country='United Kingdom',
                  description='',published=False,archived=False,noindex=True)
    db.add(page);db.flush();log(db,user,'property.draft.create',str(page.id));db.commit();db.refresh(page)
    return prop_json(page,True,staff=True)

@app.post('/api/admin/properties',status_code=201)
def add_property(data:PropertyInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    if data.published:raise HTTPException(422,'Save a draft, add rooms, then publish after completing the checklist')
    d=_as_db(data);d['slug']=slugify(d['slug'] or d['name'])
    if not d['slug']:raise HTTPException(422,'Invalid slug')
    if db.scalar(select(Property).where(Property.slug==d['slug'])):raise HTTPException(409,'Slug already in use')
    p=Property(**d);db.add(p);db.flush();log(db,user,'property.create',str(p.id));db.commit();db.refresh(p)
    return prop_json(p,True,staff=True)

@app.patch('/api/admin/properties/{id}')
def update_property(id:int,data:PropertyInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    p=db.get(Property,id)
    if not p:raise HTTPException(404,'Listing not found')
    if user.role!='admin' and (p.published or data.published):raise HTTPException(403,'An admin must review published listings')
    if data.edit_version is None:raise HTTPException(428,'Refresh listing: edit_version is required')
    d=_as_db(data);d['slug']=slugify(d['slug'] or d['name'])
    if not d['slug']:raise HTTPException(422,'Invalid slug')
    if db.scalar(select(Property).where(Property.slug==d['slug'],Property.id!=id)):raise HTTPException(409,'Slug already in use')
    if not p.published and data.published:raise HTTPException(422,'Use Publish after completing the listing checklist')
    d['edit_version']=data.edit_version+1
    updated=db.execute(update(Property).where(Property.id==id,Property.edit_version==data.edit_version).values(**d))
    if not updated.rowcount:db.rollback();raise HTTPException(409,'This page was changed by another user. Reload before saving.')
    log(db,user,'property.update',str(id));db.commit();db.expire_all()
    return prop_json(db.get(Property,id),True,staff=True)

@app.post('/api/admin/properties/{id}/rooms',status_code=201)
def add_room(id:int,data:RoomInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    p=db.get(Property,id)
    if not p or p.archived:raise HTTPException(404,'Listing not found')
    if p.published and user.role!='admin':raise HTTPException(403,'Only administrators can edit published rooms')
    if data.parent_edit_version is None:raise HTTPException(428,'Refresh page: parent_edit_version required')
    changed=db.execute(update(Property).where(Property.id==id,Property.edit_version==data.parent_edit_version).values(edit_version=data.parent_edit_version+1))
    if not changed.rowcount:db.rollback();raise HTTPException(409,'Listing was changed. Reload the page before adding a room.')
    d=_as_db(data)
    r=Room(property_id=id,**d);db.add(r);db.flush();log(db,user,'room.create',str(r.id));db.commit();return room_json(r)

@app.patch('/api/admin/rooms/{id}')
def update_room(id:int,data:RoomInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    r=db.get(Room,id)
    if not r:raise HTTPException(404,'Room not found')
    p=db.get(Property,r.property_id)
    if p.archived:raise HTTPException(403,'Restore the property before editing rooms')
    if p.published and user.role!='admin':raise HTTPException(403,'Only administrators can edit published rooms')
    if data.edit_version is None or data.parent_edit_version is None:raise HTTPException(428,'Refresh page: edit versions required')
    changed_parent=db.execute(update(Property).where(Property.id==p.id,Property.edit_version==data.parent_edit_version).values(edit_version=data.parent_edit_version+1))
    if not changed_parent.rowcount:db.rollback();raise HTTPException(409,'Listing changed. Reload before saving room.')
    d=_as_db(data);d['edit_version']=data.edit_version+1
    changed=db.execute(update(Room).where(Room.id==id,Room.edit_version==data.edit_version).values(**d))
    if not changed.rowcount:db.rollback();raise HTTPException(409,'Another editor modified this room. Reload before saving.')
    log(db,user,'room.update',str(id));db.commit();db.expire_all();return room_json(db.get(Room,id))

@app.post('/api/admin/properties/{id}/publish')
def publish_property(id:int,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    p=db.get(Property,id)
    if not p or p.archived:raise HTTPException(404,'Page not found')
    _require_publish_ready(p,db)
    p.published=True;p.edit_version+=1;p.verified_at=datetime.now(timezone.utc)
    log(db,user,'property.publish',str(id));db.commit();return prop_json(p,True,staff=True)

@app.post('/api/admin/properties/{id}/archive')
def archive_property(id:int,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    p=db.get(Property,id)
    if not p:raise HTTPException(404,'Page not found')
    p.archived=True;p.published=False;p.edit_version+=1
    log(db,user,'property.archive',str(id));db.commit();return prop_json(p,True,staff=True)

@app.post('/api/admin/properties/{id}/restore')
def restore_property(id:int,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    p=db.get(Property,id)
    if not p:raise HTTPException(404,'Page not found')
    p.archived=False;p.edit_version+=1
    log(db,user,'property.restore',str(id));db.commit();return prop_json(p,True,staff=True)

@app.get('/api/admin/properties/{id}/preview')
def preview_property(id:int,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    p=db.get(Property,id)
    if not p:raise HTTPException(404,'Page not found')
    return prop_json(p,True,staff=True)

@app.get('/api/admin/enquiries')
def admin_enquiries(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [{'id':e.id,'property':db.get(Property,e.property_id).name,'property_id':e.property_id,'room_id':e.room_id,'student_id':e.student_id,'name':e.name,'email':e.email,'phone':e.phone,'university':e.university,'move_in_date':e.move_in_date.isoformat() if e.move_in_date else None,'message':e.message,'status':e.status,'assigned_to_id':e.assigned_to_id,'created_at':e.created_at.isoformat()} for e in db.scalars(select(Enquiry).order_by(Enquiry.id.desc())).all()]

@app.patch('/api/admin/enquiries/{id}')
def update_enquiry(id:int,data:EnquiryUpdate,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    e=db.get(Enquiry,id)
    if not e:raise HTTPException(404,'Enquiry not found')
    changes=data.model_fields_set
    if 'assigned_to_id' in changes:
        if data.assigned_to_id is None:e.assigned_to_id=None
        else:
            target=db.get(User,data.assigned_to_id)
            if not target or not target.active or target.role not in ('admin','editor'):raise HTTPException(422,'Assign only to active staff')
            e.assigned_to_id=target.id
    if data.status is not None:
        if data.status=='booked':
            if user.role!='admin' or not data.booking_reference.strip():
                raise HTTPException(403,'Admin confirmation and provider booking reference required to mark as booked')
            e.booking_reference=data.booking_reference.strip()
            e.confirmed_at=datetime.now(timezone.utc)
        e.status=data.status
    log(db,user,'enquiry.update',str(e.id));db.commit();return {'id':e.id,'status':e.status,'assigned_to_id':e.assigned_to_id}

class EnquiryNoteInput(BaseModel):
    message: str = Field(min_length=2,max_length=4000)
@app.get('/api/admin/enquiries/{id}/notes')
def read_enquiry_notes(id:int,_:User=Depends(require_admin),db:Session=Depends(get_db)):
    if not db.get(Enquiry,id):raise HTTPException(404,'Enquiry not found')
    rows=db.scalars(select(EnquiryNote).where(EnquiryNote.enquiry_id==id).order_by(EnquiryNote.created_at)).all()
    return [{'id':r.id,'message':r.message,'created_at':r.created_at.isoformat(),'by':db.get(User,r.actor_id).name} for r in rows]
@app.post('/api/admin/enquiries/{id}/notes',status_code=201)
def add_enquiry_note(id:int,data:EnquiryNoteInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    if not db.get(Enquiry,id):raise HTTPException(404,'Enquiry not found')
    r=EnquiryNote(enquiry_id=id,actor_id=user.id,message=data.message.strip());db.add(r);db.flush();log(db,user,'enquiry.note',str(id));db.commit();return {'id':r.id,'message':r.message}

@app.get('/api/admin/staff')
def staff(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [user_json(u) for u in db.scalars(select(User).where(User.role.in_(['admin','editor']),User.active.is_(True))).all()]

class StaffInput(BaseModel):
    name: str = Field(min_length=2,max_length=150)
    email: EmailStr
    username: str | None = Field(default=None,max_length=40)
    password: str = Field(min_length=12,max_length=128)
    role: Literal['admin','editor'] = 'editor'
@app.post('/api/admin/staff',status_code=201)
def add_staff(data:StaffInput,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==data.email.lower())):raise HTTPException(409,'Email in use')
    username=clean_username(data.username)
    if username and db.scalar(select(User).where(User.username==username)):
        raise HTTPException(409,'Username already taken')
    member=User(name=data.name,email=data.email.lower(),username=username,
                password_hash=ph.hash(data.password),role=data.role,email_verified=True)
    db.add(member);db.flush();log(db,user,'staff.create',str(member.id));db.commit();return user_json(member)
class StaffUpdate(BaseModel):
    active: bool | None = None
    role: Literal['admin','editor'] | None = None
@app.patch('/api/admin/staff/{id}')
def edit_staff(id:int,data:StaffUpdate,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    member=db.get(User,id)
    if not member or member.role not in ('admin','editor'):raise HTTPException(404,'Staff member not found')
    if user.id==id and (data.active is False or data.role=='editor'):raise HTTPException(422,'You cannot remove your own admin access')
    if data.active is not None:member.active=data.active
    if data.role is not None:member.role=data.role
    member.auth_version+=1
    log(db,user,'staff.update',str(id));db.commit();return user_json(member)
@app.get('/api/admin/audit')
def admin_audit(user:User=Depends(require_manager),db:Session=Depends(get_db)):
    rows=db.scalars(select(Audit).order_by(Audit.id.desc()).limit(80)).all()
    return [{'event':a.event,'reference':a.reference,'at':a.created_at.isoformat(),'actor':(db.get(User,a.actor_id).name if db.get(User,a.actor_id) else 'Former staff')} for a in rows]

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


def _seo_page_html(p,preview=False):
    return render_property(p,prop_json(p,detail=True,staff=preview),PUBLIC_SITE_URL,preview=preview)

@app.get('/property/{slug}',response_class=HTMLResponse)
def seo_property(slug:str,preview_token:str|None=None,db:Session=Depends(get_db)):
    p=db.scalar(select(Property).where(Property.slug==slug))
    if not p:raise HTTPException(404,'Page not found')
    preview=False
    if preview_token:
        try:
            claim=jwt.decode(preview_token,JWT_SECRET,algorithms=['HS256'])
            user=db.get(User,int(claim['sub']))
            preview=(claim.get('scope')=='accom-property-preview' and claim.get('property_id')==p.id
                and user is not None and user.active and user.role in ('admin','editor')
                and user.auth_version==claim.get('av'))
        except Exception:preview=False
    if not preview and (not p.published or p.archived):raise HTTPException(404,'Page not found')
    return HTMLResponse(_seo_page_html(p,preview),headers={
       'Cache-Control':'no-store' if preview else 'public, max-age=60',
       'Referrer-Policy':'no-referrer' if preview else 'strict-origin-when-cross-origin',
       'X-Robots-Tag':'noindex, nofollow' if preview or p.noindex else 'index,follow',
       'Content-Security-Policy':"script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"})

@app.post('/api/admin/properties/{id}/preview-link')
def property_preview_link(id:int,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    p=db.get(Property,id)
    if not p:raise HTTPException(404,'Page not found')
    preview_token=jwt.encode({'sub':str(user.id),'scope':'accom-property-preview',
        'property_id':p.id,'av':user.auth_version,
        'exp':datetime.now(timezone.utc)+timedelta(minutes=5)},JWT_SECRET,algorithm='HS256')
    return {'url':'/property/'+quote(p.slug)+'?preview_token='+quote(preview_token),
        'expires_in_seconds':300}

@app.get('/sitemap.xml',response_class=HTMLResponse)
def sitemap(db:Session=Depends(get_db)):
    pages=db.scalars(select(Property).where(Property.published.is_(True),Property.archived.is_(False),Property.noindex.is_(False))).all()
    nodes=''.join(f'<url><loc>{escape(PUBLIC_SITE_URL+"/property/"+quote(p.slug))}</loc></url>' for p in pages)
    editorials=db.scalars(select(EditorialPage).where(EditorialPage.published.is_(True),EditorialPage.archived.is_(False),EditorialPage.noindex.is_(False))).all()
    nodes+=''.join(f'<url><loc>{escape(PUBLIC_SITE_URL+"/site/"+quote(p.slug))}</loc></url>' for p in editorials)
    return HTMLResponse('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+nodes+'</urlset>',media_type='application/xml')

@app.get('/robots.txt',response_class=PlainTextResponse)
def robots():
    return f'User-agent: *\nDisallow: /admin\nDisallow: /student\nSitemap: {PUBLIC_SITE_URL}/sitemap.xml\n'


# Approved HTML templates are for editorial pages. Accommodation listings remain
# native structured components so rooms, price filters and enquiries keep working.
_ALLOWED_TAGS={'html','head','body','main','section','article','div','span','h1','h2','h3','h4','h5','h6',
 'p','strong','b','em','i','ul','ol','li','a','img','figure','figcaption','blockquote','br','hr','small','header','footer','nav'}
_ALLOWED_ATTRS={'class','id','alt','title','href','src','role','aria-label'}
def _safe_template(html):
    soup=BeautifulSoup(html,'html.parser')
    for tag in list(soup.find_all(True)):
        if tag.name not in _ALLOWED_TAGS:
            # Remove scripts, styles, forms, embeds and unknown elements entirely.
            tag.decompose()
            continue
        for attr in list(tag.attrs):
            if attr not in _ALLOWED_ATTRS:del tag[attr]
        for attr in ('href','src'):
            if tag.has_attr(attr):
                url=str(tag[attr]).strip()
                if not (url.startswith('/') and not url.startswith('//')) and not re.fullmatch(r'https://[^\s<>"\']+',url):
                    del tag[attr]
    return soup

def _extract_template(source):
    soup=_safe_template(source)
    blocks=soup.find_all('section')
    if not blocks:blocks=soup.find_all('main')
    if not blocks:blocks=[soup.body or soup]
    sections=[];fields=[]
    for i,section in enumerate(blocks):
        sid='section_'+str(i+1)
        section['data-ac-section']=sid
        heading=section.find(['h1','h2','h3','h4','h5','h6'])
        sections.append({'id':sid,'name':heading.get_text(' ',strip=True)[:70] if heading else 'Section '+str(i+1),'order':i+1})
        nodes=section.find_all(['h1','h2','h3','h4','h5','h6','p','a','img'])
        for j,node in enumerate(nodes):
            if len(fields)>=240:break
            kind='image' if node.name=='img' else 'link' if node.name=='a' else 'text'
            attr='src' if kind=='image' else 'href' if kind=='link' else 'text'
            value=str(node.get(attr,'')) if attr!='text' else node.get_text(' ',strip=True)
            if not value:continue
            key=f'{sid}_field_{j+1}'
            node['data-ac-field']=key
            fields.append({'key':key,'section_id':sid,'label':('Image' if kind=='image' else 'Link' if kind=='link' else node.name.upper())+' '+str(j+1),'kind':kind,'tag':node.name,'attr':attr,'default':value[:4000],'mode':'page'})
    return str(soup),sections,fields

def _template_info(t):
    return {'id':t.id,'name':t.name,'approved':t.approved,'sections':t.sections,'fields':t.fields}

def _editorial_info(p):
    return {'id':p.id,'kind':'editorial','template_id':p.template_id,'title':p.title,'slug':p.slug,'values':p.values,'seo_title':p.seo_title,'meta_description':p.meta_description,'noindex':p.noindex,'published':p.published,'archived':p.archived,'edit_version':p.edit_version}

def _render_editorial(t,p,preview=False):
    soup=BeautifulSoup(t.source_html,'html.parser')
    for field in t.fields:
        if field.get('mode')!='page':continue
        node=soup.find(attrs={'data-ac-field':field['key']})
        if not node:continue
        value=str((p.values or {}).get(field['key'],field['default']))[:4000]
        if field['kind']=='text':node.clear();node.append(value)
        elif field['kind']=='image' and re.fullmatch(r'https://[^\s]+',value):node['src']=value
        elif field['kind']=='link' and (value.startswith('/') and not value.startswith('//') or re.fullmatch(r'https://[^\s]+',value)):node['href']=value
    # Editorial templates cannot execute JavaScript, even on their own published URLs.
    body=str(soup.body or soup)
    head=f'<meta name="robots" content="{"noindex,nofollow" if preview or p.noindex else "index,follow"}">' \
         +f'<title>{escape(p.seo_title or p.title)}</title><meta name="description" content="{escape(p.meta_description,quote=True)}">'
    canonical=PUBLIC_SITE_URL+'/site/'+quote(p.slug)
    return '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+head+f'<link rel="canonical" href="{escape(canonical,quote=True)}">' \
           +'<style>body{font:15px/1.6 system-ui, sans-serif;max-width:1160px;margin:auto;padding:35px;color:#161616}img{max-width:100%;height:auto}section{margin-bottom:36px}h1,h2,h3{line-height:1.16}a{color:#d7191d}</style></head><body>'+body+'</body></html>'

@app.get('/api/admin/templates')
def get_templates(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [_template_info(t) for t in db.scalars(select(ContentTemplate).order_by(ContentTemplate.id.desc())).all()]

@app.post('/api/admin/templates',status_code=201)
async def upload_template(file:UploadFile=File(...),name:str=Form(''),user:User=Depends(require_manager),db:Session=Depends(get_db)):
    if not (file.filename or '').lower().endswith('.html'):raise HTTPException(422,'Upload an .html file')
    raw=await file.read(1500001)
    if len(raw)>1500000:raise HTTPException(413,'HTML must be under 1.5 MB')
    try:source=raw.decode('utf-8')
    except UnicodeDecodeError:raise HTTPException(422,'Use UTF-8 encoded HTML')
    clean,sections,fields=_extract_template(source)
    if not fields:raise HTTPException(422,'No editable text or image fields detected')
    t=ContentTemplate(name=(name.strip() or (file.filename or 'Template')[:-5])[:160],source_html=clean,sections=sections,fields=fields)
    db.add(t);db.flush();log(db,user,'template.upload',str(t.id));db.commit();return _template_info(t)

class TemplateMappingInput(BaseModel):
    fields: list[dict]
    approved: bool = False
@app.patch('/api/admin/templates/{id}')
def update_template(id:int,data:TemplateMappingInput,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    t=db.get(ContentTemplate,id)
    if not t:raise HTTPException(404,'Template not found')
    expected={f['key']:f for f in t.fields}
    if {f.get('key') for f in data.fields}!=set(expected):raise HTTPException(422,'The original field mapping must be preserved')
    updated=[]
    for f in data.fields:
        prev=expected[f['key']]
        mode=f.get('mode')
        if mode not in ('static','page'):raise HTTPException(422,'Field mode must be static or page')
        updated.append({**prev,'mode':mode,'label':str(f.get('label') or prev['label'])[:100]})
    t.fields=updated;t.approved=data.approved;t.updated_at=datetime.now(timezone.utc)
    log(db,user,'template.mapping',str(t.id));db.commit();return _template_info(t)

@app.get('/api/admin/templates/{id}/preview',response_class=HTMLResponse)
def preview_template(id:int,_:User=Depends(require_admin),db:Session=Depends(get_db)):
    t=db.get(ContentTemplate,id)
    if not t:raise HTTPException(404,'Template not found')
    fake=type('Sample',(),{'title':t.name,'seo_title':t.name,'meta_description':'Preview only','slug':'preview','values':{},'noindex':True})()
    return HTMLResponse(_render_editorial(t,fake,preview=True),headers={'Content-Security-Policy':"default-src 'none'; img-src https: data:; style-src 'unsafe-inline'; sandbox"})

class EditorialInput(BaseModel):
    template_id:int
    title:str=Field(min_length=3,max_length=220)
    slug:str=''
    values:dict[str,str]=Field(default_factory=dict)
    seo_title:str=''
    meta_description:str=''
    noindex:bool=False
    edit_version:int|None=None

@app.get('/api/admin/pages')
def get_editorial_pages(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [_editorial_info(p) for p in db.scalars(select(EditorialPage).order_by(EditorialPage.id.desc())).all()]

@app.post('/api/admin/pages',status_code=201)
def create_editorial_page(data:EditorialInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    t=db.get(ContentTemplate,data.template_id)
    if not t or not t.approved:raise HTTPException(422,'Choose an approved template')
    slug=slugify(data.slug or data.title)
    if not slug or db.scalar(select(EditorialPage).where(EditorialPage.slug==slug)):raise HTTPException(409,'Page slug in use')
    allowed={f['key'] for f in t.fields if f['mode']=='page'}
    if any(k not in allowed or not isinstance(v,str) for k,v in data.values.items()):raise HTTPException(422,'Values contain fields that are not editable')
    p=EditorialPage(template_id=t.id,title=data.title,slug=slug,values=data.values,seo_title=data.seo_title,meta_description=data.meta_description,noindex=data.noindex)
    db.add(p);db.flush();log(db,user,'editorial.create',str(p.id));db.commit();return _editorial_info(p)

@app.patch('/api/admin/pages/{id}')
def update_editorial_page(id:int,data:EditorialInput,user:User=Depends(require_admin),db:Session=Depends(get_db)):
    p=db.get(EditorialPage,id)
    if not p:raise HTTPException(404,'Page not found')
    if p.published and user.role!='admin':raise HTTPException(403,'Only admins can change published pages')
    if data.edit_version is None:raise HTTPException(428,'edit_version required')
    if data.edit_version!=p.edit_version:raise HTTPException(409,'Page changed by another editor')
    if data.template_id!=p.template_id:raise HTTPException(422,'Template cannot change after page creation')
    t=db.get(ContentTemplate,p.template_id)
    allowed={f['key'] for f in t.fields if f['mode']=='page'}
    if any(k not in allowed or not isinstance(v,str) for k,v in data.values.items()):raise HTTPException(422,'Only approved variable fields may be edited')
    slug=slugify(data.slug or data.title)
    if db.scalar(select(EditorialPage).where(EditorialPage.slug==slug,EditorialPage.id!=id)):raise HTTPException(409,'Slug already used')
    for k in ('title','values','seo_title','meta_description','noindex'):setattr(p,k,getattr(data,k))
    p.slug=slug;p.edit_version+=1
    log(db,user,'editorial.update',str(id));db.commit();return _editorial_info(p)

@app.post('/api/admin/pages/{id}/publish')
def publish_editorial(id:int,user:User=Depends(require_manager),db:Session=Depends(get_db)):
    p=db.get(EditorialPage,id)
    if not p:raise HTTPException(404,'Page not found')
    t=db.get(ContentTemplate,p.template_id)
    if not t or not t.approved or not p.seo_title.strip() or len(p.meta_description.strip())<40:
        raise HTTPException(422,'Approve template and complete SEO title and 40+ character meta description')
    p.published=True;p.edit_version+=1
    log(db,user,'editorial.publish',str(id));db.commit();return _editorial_info(p)

@app.get('/api/admin/pages/{id}/preview',response_class=HTMLResponse)
def preview_editorial(id:int,_:User=Depends(require_admin),db:Session=Depends(get_db)):
    p=db.get(EditorialPage,id)
    if not p:raise HTTPException(404,'Page not found')
    t=db.get(ContentTemplate,p.template_id)
    return HTMLResponse(_render_editorial(t,p,preview=True),headers={'Content-Security-Policy':"default-src 'none'; img-src https: data:; style-src 'unsafe-inline'; sandbox"})

@app.get('/site/{slug}',response_class=HTMLResponse)
def public_editorial(slug:str,db:Session=Depends(get_db)):
    p=db.scalar(select(EditorialPage).where(EditorialPage.slug==slug,EditorialPage.published.is_(True),EditorialPage.archived.is_(False)))
    if not p:raise HTTPException(404,'Page not found')
    t=db.get(ContentTemplate,p.template_id)
    return HTMLResponse(_render_editorial(t,p),headers={'Content-Security-Policy':"default-src 'none'; img-src https: data:; style-src 'unsafe-inline'; sandbox"})


def _s3():
    if not S3_ENDPOINT_URL or not S3_ACCESS_KEY or not S3_SECRET_KEY:
        raise HTTPException(503,'Media storage is not configured')
    return boto3.client('s3',endpoint_url=S3_ENDPOINT_URL,aws_access_key_id=S3_ACCESS_KEY,
                        aws_secret_access_key=S3_SECRET_KEY,region_name='us-east-1')

@app.post('/api/admin/media',status_code=201)
async def upload_media(file:UploadFile=File(...),alt:str=Form(''),user:User=Depends(require_admin),db:Session=Depends(get_db)):
    raw=await file.read(8*1024*1024+1)
    if not raw or len(raw)>8*1024*1024:raise HTTPException(413,'Images must be below 8MB')
    try:
        Image.MAX_IMAGE_PIXELS=20_000_000
        with Image.open(io.BytesIO(raw)) as img:
            img.verify()
        with Image.open(io.BytesIO(raw)) as img:
            if img.format not in ('JPEG','PNG','WEBP'):
                raise HTTPException(422,'Use JPEG, PNG or WebP images')
            if img.width>5000 or img.height>5000:
                raise HTTPException(422,'Image dimensions must be at most 5000px')
            if img.width>2000 or img.height>2000:img.thumbnail((2000,2000))
            if img.mode not in ('RGB','L'):img=img.convert('RGB')
            output=io.BytesIO();img.save(output,format='JPEG',quality=83,optimize=True)
            payload=output.getvalue()
    except HTTPException:raise
    except (OSError,ValueError,UnidentifiedImageError,Image.DecompressionBombError):
        raise HTTPException(422,'Could not validate the image file')
    key='photos/'+uuid.uuid4().hex+'.jpg'
    try:
        storage=_s3()
        try:storage.head_bucket(Bucket=S3_BUCKET)
        except Exception:storage.create_bucket(Bucket=S3_BUCKET)
        storage.put_object(Bucket=S3_BUCKET,Key=key,Body=payload,ContentType='image/jpeg')
    except HTTPException:raise
    except Exception:raise HTTPException(503,'Photo storage is temporarily unavailable')
    asset=MediaAsset(object_key=key,filename=(file.filename or 'photo')[:220],mime_type='image/jpeg',alt=alt[:240],bytes=len(payload),uploaded_by=user.id)
    db.add(asset);db.flush();log(db,user,'media.upload',str(asset.id));db.commit()
    return {'id':asset.id,'url':'/api/media/'+str(asset.id),'alt':asset.alt,'bytes':asset.bytes}

@app.get('/api/admin/media')
def list_media(_:User=Depends(require_admin),db:Session=Depends(get_db)):
    return [{'id':a.id,'url':'/api/media/'+str(a.id),'alt':a.alt,'filename':a.filename,'bytes':a.bytes} for a in db.scalars(select(MediaAsset).order_by(MediaAsset.id.desc()).limit(200)).all()]

@app.get('/api/media/{id}')
def media_asset(id:int,db:Session=Depends(get_db)):
    a=db.get(MediaAsset,id)
    if not a:raise HTTPException(404,'Image not found')
    try:
        obj=_s3().get_object(Bucket=S3_BUCKET,Key=a.object_key)
        content=obj['Body'].read(8*1024*1024)
    except HTTPException:raise
    except Exception:raise HTTPException(503,'Image storage unavailable')
    return Response(content,media_type=a.mime_type,headers={'Cache-Control':'public, max-age=86400','X-Content-Type-Options':'nosniff'})
