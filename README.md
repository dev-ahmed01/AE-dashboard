# Accom by Emlen — Category Page Manager

A separate student-accommodation platform with a public directory, student account area and **one admin module: Category**.

## Admin structure

The dashboard sidebar contains **Category only**, with three horizontal tabs:
**All Pages**, **Add Page**, **Upload Template**. No separate Listings, Enquiries, Cashback or Templates modules.

- **All Pages**: published/draft/archived accommodations and editorial pages. Open the relevant property to edit its content and rooms. Student enquiries, cashback records, staff access and activity history are expandable sections on this screen.
- **Add Page**: create an accommodation listing from the native property page layout, or create an editorial page from an approved HTML template.
- **Upload Template**: upload one UTF-8 HTML file, detect semantic sections and fields, map fields as Page variable or Static, approve and preview. Unsafe scripts/forms/embeds are stripped; uploaded HTML is for editorial pages, not arbitrary interactive components.

## Backend

FastAPI, PostgreSQL 16, SQLAlchemy, Alembic, JWT/Argon2id, S3-compatible private media storage and React 19/Vite.

## Local run

```sh
cp .env.example .env
# Replace every placeholder with strong unique secrets; configure SMTP for student signups.
docker compose up -d --build
docker compose ps
```

Open `http://localhost:8081`, sign in using `ADMIN_EMAIL` and `ADMIN_PASSWORD` from your `.env`.

Migrations run before the API is started in Docker. Run `cd apps/api && python -m pytest -q` to verify backend behavior and `cd apps/web && npm install && npm run build` for the front end. Always test database backups before migrating existing production data.

**Important:** This code is an improved development foundation, not a verified live launch. SMTP is required for student verification, and production deployment requires backups, HTTPS, multi-factor admin access, rate limit proxy configuration, image rights, real listing/price verification and end-to-end QA. Never publish real rent payments through Accom; students pay accommodation providers directly.

See [docs/QA_REMEDIATION_2026-11-06.md](docs/QA_REMEDIATION_2026-11-06.md) for regression coverage and remaining limitations.
