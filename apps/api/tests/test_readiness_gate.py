"""Migration preflight and fail-closed runtime readiness contracts."""
import pytest
from fastapi import HTTPException

import app as api


class FakeQuery:
    def __init__(self, revisions=None):
        self.revisions = revisions or []

    def scalars(self):
        return iter(self.revisions)


class FakeSession:
    def __init__(self, revision="revision-1", fail=False):
        self.revision = revision
        self.fail = fail

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, query):
        if self.fail:
            raise RuntimeError("private database hostname must never appear")
        if "alembic_version" in str(query):
            return FakeQuery([self.revision])
        return FakeQuery([])


class FakeStore:
    def __init__(self, fail=False):
        self.fail = fail

    def list_buckets(self):
        if self.fail:
            raise RuntimeError("sensitive bucket credentials must not be returned")
        return {"Buckets": []}


def test_readiness_checks_database_schema_and_object_storage(monkeypatch):
    monkeypatch.setattr(api, "_migration_heads", lambda: {"revision-1"})
    monkeypatch.setattr(api, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(api, "_s3", lambda: FakeStore())
    assert api.readiness() == {"status": "ready"}


@pytest.mark.parametrize("failure", ["database", "schema", "storage"])
def test_readiness_fails_closed_without_leaking_secrets(monkeypatch, failure):
    monkeypatch.setattr(api, "_migration_heads", lambda: {"revision-1"})
    monkeypatch.setattr(
        api, "SessionLocal",
        lambda: FakeSession(revision="wrong" if failure == "schema" else "revision-1",
                            fail=failure == "database"),
    )
    monkeypatch.setattr(api, "_s3", lambda: FakeStore(fail=failure == "storage"))
    with pytest.raises(HTTPException) as exc:
        api.readiness()
    assert exc.value.status_code == 503
    assert exc.value.detail == "Service unavailable"


def test_hosted_settings_reject_demo_mode_and_placeholder_secrets(monkeypatch):
    monkeypatch.setattr(api, "APP_ENVIRONMENT", "production")
    monkeypatch.setattr(api, "DATABASE_URL", "postgresql+psycopg://user:secret@db:5432/accom")
    monkeypatch.setattr(api, "JWT_SECRET", "safe-secret-with-at-least-thirty-two-characters")
    monkeypatch.setattr(api, "ADMIN_EMAIL", "staff@example.test")
    monkeypatch.setattr(api, "ADMIN_PASSWORD", "unique-admin-test-password-123")
    monkeypatch.setattr(api, "S3_ENDPOINT_URL", "http://minio:9000")
    monkeypatch.setattr(api, "S3_ACCESS_KEY", "private-access-key")
    monkeypatch.setattr(api, "S3_SECRET_KEY", "private-storage-secret")
    monkeypatch.setattr(api, "CORS_ORIGIN", "https://staging.example.test")
    monkeypatch.setattr(api, "PUBLIC_SITE_URL", "https://staging.example.test")
    monkeypatch.delenv("SEED_ACCOM_DEMO", raising=False)
    monkeypatch.delenv("ALLOW_BOOTSTRAP_SCHEMA", raising=False)
    monkeypatch.setattr(api, "LOCAL_DEMO_MODE", False)
    api._validate_hosted_settings()
    monkeypatch.setattr(api, "LOCAL_DEMO_MODE", True)
    with pytest.raises(RuntimeError, match="no demo mode"):
        api._validate_hosted_settings()
    monkeypatch.setattr(api, "LOCAL_DEMO_MODE", False)
    monkeypatch.setattr(api, "JWT_SECRET", "REPLACE_WITH_32_PLUS_RANDOM_CHARACTERS")
    with pytest.raises(RuntimeError, match="placeholder credentials"):
        api._validate_hosted_settings()
