# Accom by Emlen — UI/feature audit, WE comparison and build plan

Date: 5 November 2026. Target site examined: https://admirable-kitsune-933239.netlify.app/ . Reference repository examined: https://github.com/dev-ahmed01/Dashboard-WE (`main`, November 2026). Public-site review uses rendered content and accessible browser DOM, **not the original unpublished HTML/CSS/JS source code or Netlify build settings**.

## A. Observed Accom prototype: comprehensive element inventory

**Property identity and top navigation**
- Accom by Emlen logo, Explore rooms/Amenities/Location links, Get help, breadcrumb; iQ Kingston title, address (15 Wood Street, Kingston upon Thames, KT1 1TY), 4.9 rating linked to Amber (11 reviews), Save and Share.
- Full-width hero/image mosaic; Photo count (7), Videos, 3D tour and Show all gallery; category photo tiles (En suites, Studios, Shared spaces, Exterior), lightbox with previous/next navigation and 3D-tour external link.
- Sticky on-scroll section links: Overview, Rooms, Included, Terms, Location, FAQs, Reviews. Compare/save affordances.

**Informational sections**
- Property intro and highlights: en suites/studios, private bathroom, bills included, proximity to university, 24-hour security.
- Residence description, Official property details external link, room-type explanation tiles, category photo guide.
- Amenity groups: utility inclusions, student life/social spaces, practical support.
- Interactive bill budgeting widget with Wi-Fi/electricity/heating/water/insurance inputs and 44/51-week switches; starts from £0 and is expressly not a verified discount/saving.
- Room listing: filter All rooms/En suites/Studios. Five observed cards: Saver En Suite, Silver En Suite, Gold En Suite, Platinum En Suite, Silver Studio. Source date 28 Oct 2026. Three rate snapshots (£315, £334, £360 per week) and two rates needing confirmation. Room cards show attributes, available-from values when stated, Compare and Select room actions.
- Rules/cancellation accordions; payment/fees explanations; floor-plan request; neighborhood guide, Maps link; five searchable FAQ questions; nearby landmarks grouped as universities, transport, shopping, attractions.
- Reviews section with attributed Amber snapshot and six **explicitly fictional concept testimonials**. Fictional reviews must never become real production reviews.

**Conversion/interactions**
- Sticky right-side rent/room card and Enquire CTA; mobile bottom CTA.
- Compare up to two room styles and clear selection; Save and Share buttons; room/category toggles.
- Enquiry modal fields: full name, email, enquiry subject, optional university, optional move-in date, optional phone, optional message, contact-consent checkbox.
- Most significant current limitation: prototype states **"This prototype does not transmit them"** after form check. No live enquiry DB, administration interface or student portal is evidenced on this page.
- There is no evidence that photographs are licensed real iQ Kingston images, that rates are real-time, or that reviews outside the attributed snapshot are authentic. Do not import these concept values as verified data.

**Page file/code audit boundary**: Browser access confirms DOM controls, labels, sections and current copy; it does not expose the unpublished original source repository, all JavaScript modules, Netlify deployment configuration or whether every click works in all browser states. Do not claim a code-level audit of those inaccessible assets.

## B. What Dashboard-WE actually provides (inspected on main)

Stack: React 19 + TypeScript + Vite + Nginx, FastAPI, PostgreSQL 16/SQLAlchemy/Alembic, MinIO/S3 media. On `main`: upload `.html`, detect `<section>` blocks and map fields as Static/Page/Shared, manage Category pages, preview (including unsaved content), advanced section/repeater/canvas edits, draft/publish snapshots, SEO metadata/canonical/index/follow/OG/breadcrumbs, sitemap and redirect controls, media alt text, team roles, audit logs and Docker/CI. WE's own README explicitly says its local published snapshot does **not** update the live WordPress website. Its latest main CI run was reported successful on 4 November 2026.

| WE capability | Accom decision | Reason |
|---|---|---|
| React/TypeScript UI, FastAPI, PostgreSQL, Nginx, Docker, CI | **Reuse architectural pattern** | Known, self-hostable stack and familiar operating workflow |
| Login/admin/editor RBAC, auditing | **Extend** | Add student and consultant identity, assigned enquiries and safer publishing |
| Category / Add Page / Upload Template / Visual Preview | **Reserve for editorial pages** | Useful for About, city guide, landing page; not the property master database |
| HTML section mapping, static/global/page fields, Canva-like editor | **Do not use as property database** | Rooms, rates, availability and bookings need schemas and relationships |
| Media library, alt text, preview | **Adapt** | Add galleries with categories, image ownership and floorplan/video media |
| Draft/published snapshots, redirects and SEO | **Adapt** | Property-level publishing, room/rate verification, SEO indexable detail pages |
| Generic page fields and CTA URLs | **Replace with typed listing fields** | Correct room-to-enquiry link and price/date validation |
| Shared content | **Reuse idea** | Global enquiry/contact sections and standard policy blocks |
| Local publishing | **Build actual frontend integration** | New Accom directory must fetch published property data |

## C. Approved-direction product boundaries

The existing Accom development proposal covers THREE systems: (1) accommodation directory, (2) student portal, (3) admin dashboard. Directory search uses city/university/area, detail pages, saved options and enquiries. Student portal shows own enquiries, assigned consultant and progress; cashback **when supported by verified Accom records**. Admin manages listings/rooms/rates, enquiry handoffs, consultant assignments and basic reporting. **Accommodation rent is paid directly to providers**; no Accom rent checkout.

Client design challenge: property-detail page using Bricolage Grotesque headings, Montserrat body, #ED2024 red; full-width lightbox gallery, ~75:25 content/sticky CTA, on-scroll section navigation, restrained liquid glass, accessible mobile layout. Do not duplicate Amber's interface. Final UI awaits any required client review.

## D. Target product modules

1. **Directory & SEO** — country/city/university/area relations; listing card, search/sort/filter; indexable clean property/city URLs; provenance for price and reviews.
2. **Property manager** — identity, operator, address, map coordinates, categories, highlights, amenities, approved photo/video/360/floorplan gallery, landmarks, policies, FAQs, offer validity, per-property SEO, draft/approval/publish.
3. **Room inventory** — property → room type → rate plan; currency and per-week/month basis; checked-at source, start/end dates, actual availability status; room comparison; no implied reservation.
4. **Enquiries & leads** — property/room association, GDPR/UK privacy consent, source, duplicate handling, consultant assignment, stage history, follow-up, operational reporting.
5. **Student portal** — secure registration/verified contact, saved/compared listings, authenticated enquiries, status, consultant name and messages; optional verified cashback.
6. **Admin settings** — staff RBAC, audit trail, media and SEO management, safe publishing, backups, analytics and future integrations.

## E. Concrete schema (version 1)

`users` (student/admin/editor); `properties` (title, location, overview, gallery/amenities/policies/FAQs, SEO, publish state); `rooms` (property FK, type, size, price/currency/period, source/date, availability); `saved_properties` (student/property unique); `enquiries` (student optional, property/room, consent, contact, status, assigned staff); `cashbacks` (enquiry, eligibility and payout status); `audit_logs` (author and mutations).

Before production expand the model to normalized universities, operators, locations, media objects, price history, date-window inventory, notifications/consent, publication revisions, audit-level changes, and message histories. Avoid asserting live room availability from a single listing snapshot.

## F. Delivery sequence and definitions of done

**Foundation (implemented in this repository's v0.1)**: bootable backend/database and frontend, basic admin property+room editor, published-directory rendering, room detail/comparison, enquiry DB capture, student account + saved list + progress, admin lead status/assignment and optional cashback records. Backend happy-path test passes locally.

**Next engineering pass — mandatory before handling real student data**:
- Signed-in student enquiries must be linked to authenticated account only. Guest enquiry ownership needs email verification or authenticated claiming.
- Harden permissions: admin-only publish, editor drafts, immutable public publication snapshots, staff account management and session revocation.
- Add migrations (Alembic), concurrency/version checks, database indexes, pagination, validation of HTML/links, automated backups and restore drill.
- Add rate limits/spam/abuse protections, consent privacy policy links, retention controls, logging redaction, transport security, secure cookies/MFA or SSO for staff.
- Image/media upload to S3-compatible storage and responsive transforms, alt text, permitted-license fields, lightbox categories and videos/360.
- Improve SEO via SSR/SSG indexed directory/property pages, canonical, real sitemap/robots, structured data, redirect rules; build local preview/staging/live publish path and validate Google Search Console.
- Upgrade visual editing without reintroducing WE template import's script-stripping bug: model interactive gallery, rooms and forms as native components, use HTML template import for **editorial** pages only.
- Enquiry confirmations with verified email provider, student-only messages, notification history; map travel times only from source or route API; real QA of mobile/keyboard flows.

**Release review**: correct content/photo rights and current rates supplied by Accom; student test (search→enquiry→portal), admin test (draft→room setup→publish, lead assignment→status), keyboard/mobile accessibility, CI, production TLS, restores, privacy/legal review, client sign-off. No unverified testimonials, cashback promotions or assumed booking confirmations.

## G. Rollout plan

Stage 1: controlled internal preview with seeded *explicitly fictional* data (or real listings with approved media); no public student data. Stage 2: reviewed content, source verification and team workflow test. Stage 3: production-ready auth/SEO/media/security, final client review and deployment. The original commercial proposal's 30-calendar-day implementation start conditions and handover terms remain separate and have not been asserted as satisfied.
