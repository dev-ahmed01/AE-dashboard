# Accom Dashboard — QA remediation (6 November 2026)

## Locked admin navigation
Exactly ONE admin module appears: **Category**. Three horizontal primary tabs: **All Pages**, **Add Page**, **Upload Template**. Rooms, student enquiries, cashback, staff access and audit history are managed inside All Pages, not separate sidebar modules. Public directory and student portal remain separate public/student routes.

## Implemented & regression-tested
- `edit_version` checks protect property and room records from stale edits (HTTP 409), including parent page changes.
- Published room changes require administrator permission. Publication requires complete property description/address/gallery and at least one active room.
- Search room-type and budget filters apply to one matching available room. Lowest headline price excludes unavailable rooms and mixed currencies/rent periods.
- Admin room lists include inactive records for reactivation.
- Guest enquiries can be linked after student email verification; duplicate enquiries are suppressed; login, sign-up and enquiry endpoints are rate-limited using database records.
- Consultant unassignment, booking references, staff account management and deactivation, enquiry notes and cashback status updates have working API endpoints.
- Property SEO metadata is rendered server-side at `/property/{slug}`, with canonical, robots, Open Graph, JSON-LD, sitemap and robots.txt.
- HTML editorial templates upload, sanitize unsafe elements, expose section/field mappings, allow Static/Page Variable behavior, support isolated preview and can produce editorial pages.
- Gallery and floor-plan repeaters support add/remove/reorder and Regular/Large layout. UI groups collapse and the editor has persistent actions and unsaved-change warning.
- Images can be uploaded to private MinIO/S3 with actual-file verification, max-size limits, EXIF-stripped JPEG output, alt text and per-item layout control.
- Alembic baseline migration upgrades existing tables without dropping data. A clean SQLite migration was tested.

## Verification in the current development environment
- 15 FastAPI API regression tests passing.
- TypeScript/TSX parser passed; temporary local type stubs found no additional non-module typing errors.
- Npm was unavailable in the offline container, so the actual Vite/React production build must pass in GitHub Actions before the feature branch is merged.
- Browser/device QA on a React 19 production build is still required.

## Known remaining launch requirements
- Configure SMTP before student email registration; without SMTP, registration is disabled. `DEV_AUTO_VERIFY_EMAIL=1` is only for tests/development and MUST NOT be set in production.
- HTTPS, production credentials, MFA/SSO for privileged users, tested PostgreSQL and object-storage backup/restore, monitoring and content/licensing review remain compulsory.
- Existing historic student accounts are not silently marked email-verified. Verify user ownership before linking historic guest enquiries.
- Data-backed cashback policies, actual provider confirmations, secure third-party communications, automatic inventory sync, advanced analytics and accessibility testing are not complete.
- Direct rent payment processing is intentionally out of scope; students pay accommodation providers.
- Template importer safely removes JavaScript and unsupported embeds. It is intended for editorial pages; interactive property pages use native components.

## Manual release acceptance steps
1. Sign in as Admin. Only Category must appear, with All Pages / Add Page / Upload Template horizontally.
2. Add a property, save draft, add a room, upload a photo, toggle Regular/Large and publish after meeting checklist.
3. Open the same property in two admin browser sessions; second stale save must show 409 and not erase the first save.
4. Sign in as editor; confirm a published property/room is read-only, while drafts are editable.
5. Mark a room inactive, find it in Rooms, reactivate it and verify public visibility.
6. Search with room-type and price combinations; no property should match conditions split across rooms.
7. Upload a 2+ section HTML template, inspect mapping, mark Static/Page Variable fields, approve and create an editorial page.
8. Test actual SMTP email verification, student login, old guest-enquiry linking, throttles and invalid tokens.
9. Test enquiry assignment/unassignment, provider booking reference, notes and cashback administrator controls.
10. Test image uploads with actual MinIO, inspect mobile/desktop, keyboard focus, responsive gallery and SEO crawl output.
11. Upgrade a copy of an existing PostgreSQL database through Alembic after taking a backup and verify records remain intact.
