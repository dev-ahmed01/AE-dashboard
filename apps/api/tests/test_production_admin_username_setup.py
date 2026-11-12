"""Production administrator provisioning should accept a username, not require email input."""
from pathlib import Path
import os
import shutil
import stat
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
SETUP = ROOT / "ops" / "contabo" / "prepare-production.sh"


@pytest.mark.skipif(shutil.which("openssl") is None, reason="OpenSSL required")
def test_username_bootstrap_produces_private_config_without_input_email(tmp_path):
    isolated = tmp_path / "ops" / "contabo"
    isolated.mkdir(parents=True)
    script = isolated / "prepare-production.sh"
    script.write_bytes(SETUP.read_bytes())
    result = subprocess.run(
        ["bash", str(script), "dashboard.skillsalazar.com", "admin"],
        text=True, capture_output=True, check=True,
    )
    assert "email login required" not in result.stdout.lower()
    config_path = tmp_path / ".env.production"
    lines = dict(line.split("=", 1) for line in config_path.read_text().splitlines()
                 if "=" in line and not line.startswith("#"))
    assert lines["ADMIN_USERNAME"] == "admin"
    assert lines["ADMIN_EMAIL"] == "admin@bootstrap.invalid"
    assert len(lines["ADMIN_PASSWORD"]) >= 20
    assert len(lines["JWT_SECRET"]) >= 32
    assert lines["LOCAL_DEMO_MODE"] == "0"
    assert (stat.S_IMODE(config_path.stat().st_mode) & 0o077) == 0
    again = subprocess.run(
        ["bash", str(script), "dashboard.skillsalazar.com", "admin"],
        text=True, capture_output=True,
    )
    assert again.returncode != 0 and "never rotate" in again.stderr


@pytest.mark.parametrize("name", ["admn", "admins", "1dmin", "Adm!n"])
def test_username_must_have_five_lowercase_alphanumeric_characters(tmp_path, name):
    isolated = tmp_path / "ops" / "contabo"
    isolated.mkdir(parents=True)
    script = isolated / "prepare-production.sh"
    script.write_bytes(SETUP.read_bytes())
    result = subprocess.run(
        ["bash", str(script), "dashboard.skillsalazar.com", name],
        text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert not (tmp_path / ".env.production").exists()
