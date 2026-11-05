# Accom by Emlen — accommodation platform (first working foundation)

An independent application for **Accom by Emlen**, based on the architecture lessons of [Dashboard-WE](https://github.com/dev-ahmed01/Dashboard-WE), but using **structured property and room records instead of uploading each property as an opaque HTML template**.

This repository contains an initial functioning vertical slice: public property discovery/detail pages, room comparison, enquiry capture, student shortlists/progress, staff listing/room management, enquiry status/assignment, and optional cashback records. It is **not yet a production-ready replacement for accombyemlen.com**. Media import, provider verification, migrations, email delivery, SEO SSR, hardened session controls, and deployment integrations are recorded as outstanding in `BUILD_PLAN.md`.

## What is working in v0.1

- **Directory**: search by property/city/university; filter by room category and budget; only published listings are shown.
- **Property details**: image mosaic/lightbox (when approved URLs exist), highlights, amenity list, room cards with dated rates, up-to-two-room comparison, policies, FAQs, location/landmarks, source-attributed reviews, rent-related budgeting example, sticky enquiry CTA.
- **Enquiries**: contact-consent-gated public form creates a real database record, never claims booking confirmation.
- **Students**: create account/sign in, save properties, view linked enquiry progress and Accom-confirmed cashback status.
- **Staff**: create and edit listings; edit room types, rates, and availability; monitor and progress/assign enquiries; enter cashback records when supported.
- **Security baseline**: JWT authentication, Argon2 password hashing, staff permission checks, server-side validation, no default demo passwords in source.
- **Ops**: Docker Compose with PostgreSQL, Nginx reverse proxy, backend/FE CI checks. Local dev can use SQLite. Services are bound to localhost until HTTPS is configured.

## Run via Docker Compose

1. Copy `.env.example` to `.env` and replace every placeholder with an independent, strong value. `JWT_SECRET` must contain 32+ characters and `ADMIN_PASSWORD` 12+ characters.
2. From the repository root: `docker compose up -d --build`.
3. Browse `http://localhost:8081`; sign in using your configured admin email/password. The admin can add a property and its room options and explicitly publish it.
4. Create a separate student account using the public sign-in page, and test a property enquiry and saved listing.

No fake property pictures or unverified cashback amounts are automatically seeded. Until an administrator creates and publishes a property, the directory intentionally shows an empty state.

## Development

Backend: `cd apps/api && pip install -r requirements.txt && uvicorn app:app --reload` (local SQLite defaults). Set `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` in the environment first.

Frontend: `cd apps/web && npm install && npm run dev` (API proxied to `localhost:8000`).

Tests: `cd apps/api && python -m pytest -q`; UI type/build check `cd apps/web && npm run build`.

## Project structure

- `apps/api/app.py` — SQLAlchemy models, auth, property APIs, student and staff endpoints
- `apps/api/tests/` — end-to-end API workflow regression
- `apps/web/src/App.tsx` — directory, property page, student portal, admin screens
- `apps/web/src/styles.css` — Accom design system and responsive layouts
- `compose.yaml` — private PostgreSQL, API and frontend Nginx stack
- `BUILD_PLAN.md` — audited current page sections, Dashboard-WE feature mapping, phased work and launch blockers

## Scope and truthfulness

- This is **Accom's own experience**, not a clone of Amber.
- **No Accom rent checkout or rent collection**: accommodation payments take place directly with the provider.
- Public prices and availability are admin-entered snapshots. A submitted enquiry is **not a reserved room**.
- Only approved and appropriately licensed images/reviews should be published. The Netlify iQ Kingston concept currently includes explicitly illustrative imagery and testimonial placeholders; they are *not* seeded as factual data.
- A pre-existing design concept is not proof of signed scope approval or live business integration.

## Before client/public launch

The first version is built to make the data journey tangible. **Do not expose it to real student PII until** database migrations, staff role permissions, verified email ownership, CSRF/rate-limit/abuse controls, secure token management, log privacy, backups/restore tests, upload hardening and privacy/consent controls are completed. See `BUILD_PLAN.md`.
