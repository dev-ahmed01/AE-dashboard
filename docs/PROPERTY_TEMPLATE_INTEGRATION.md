# Accom Property Detail integration — iQ Kingston demo

## Architecture
The original approved visual page is imported from `dev-ahmed01/Clone/accom-design-prototype`
as a **trusted, built-in template**, not processed through the generic
HTML uploader. Its HTML lives in `apps/api/property_template.html`;
its original CSS, JS and example media live under
`apps/web/public/accom-template/`.

FastAPI serves `/property/<slug>` with an embedded JSON snapshot of
the property and its rooms. The `data.js` adapter feeds the original
gallery, room selector, comparison and FAQ UI with database values.
`bridge.js` handles property identity, photos, maps and real enquiry
submissions. Uploaded editorial templates remain sanitized and do not run JS.

## Preload and review locally
In the existing `.env` set:

```env
APP_ENVIRONMENT=development
LOCAL_DEMO_MODE=1
SEED_ACCOM_DEMO=1
```

Run `docker compose up -d --build`. Alembic applies the
`0003_demo_tenancies` migration before FastAPI starts. Open
`http://localhost:8081/admin` using your local admin credentials.
Under **Category → All Pages**, iQ Kingston is available as an
**unpublished draft**. Click **Preview** to open the approved responsive
design with rooms, gallery and tenancy options preloaded.

The preview link expires in five minutes and requires an active member
of staff. Re-opening Preview refreshes the link. In preview mode the
enquiry form demonstrates validation without storing a real enquiry.

## Production behavior
Publishing is blocked while the property is marked `is_demo`, or any
room contains an `illustrative` tenancy plan. Replace illustrative
photos and prices with approved source data and verify room terms before
publishing. Once published, the enquiry modal submits through
`POST /api/enquiries`; enquiries then appear in Category operations.
Student saves require a student session.

Regular/Large photo layout and repeatable property fields stay in the
existing Category editor. Room-level tenancy plans now have their own
repeatable editor. The three Category tabs remain All Pages, Add Page
and Upload Template; no new admin module is introduced.

The gallery illustrations in this prototype are **not real photographs
of iQ Kingston**. Current prices, policies and availability must be
confirmed with the accommodation provider. Rent payments are never
collected by the Accom platform.

## Verification
GitHub Actions tests the backend API and frontend build. Perform an
additional hands-on review in Docker at 1440 px, 768 px and 390 px.
Do not interpret a CI pass as a full browser-tested production release.
