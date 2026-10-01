"""
Konfigurasi test: database SQLite in-memory (tidak menyentuh MySQL), table dibuat dari model,
setiap test mulai dengan 1 user admin.
Jalankan: poetry run pytest
"""
import os
import sys
import tempfile
from pathlib import Path

# Konfigurasi WAJIB di-set sebelum aplikasi di-import (core/config.py membaca os.environ lebih dulu dari .env)
os.environ["DB_CONNECTION_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "secret-khusus-test-tidak-dipakai-di-server"
os.environ["ENABLE_SISTEM_JOB"] = "0"
os.environ["STATIC_FILES_FOLDER"] = tempfile.mkdtemp(prefix="seed_statics_")

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "fastflow_api"), str(ROOT)]

import pytest
from fastapi.testclient import TestClient

import main
import database
from core.modules.users.model.users_model import UsersModel
from core.utils.hashing import Hash

ADMIN_USER = "admin"
ADMIN_PASSWORD = "Admin@12345"


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    database.Base.metadata.create_all(database.engine)
    yield
    database.Base.metadata.drop_all(database.engine)


@pytest.fixture()
def db():
    session = database.SessionLocal()
    session.query(UsersModel).delete()
    session.add(UsersModel(
        user_name=ADMIN_USER, user_passwd_sha=Hash.pbkdf2_sha256(ADMIN_PASSWORD), user_kode="01",
        user_keterangan="Administrator", user_aktif="Aktif", user_karyawan=0, user_groups=1,
        user_cabang="1" + "0" * 69, revised=0, created_by="system",
    ))
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    return TestClient(main.fastapi_app, raise_server_exceptions=False)


@pytest.fixture()
def admin(db):
    return db.query(UsersModel).filter(UsersModel.user_name == ADMIN_USER).first()


@pytest.fixture()
def auth_header(client):
    r = client.post("/login", data={"username": ADMIN_USER, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def assert_status_match(response):
    """Aturan seed: HTTP status selalu sama dengan body status.code."""
    body = response.json()
    if isinstance(body, dict) and "status" in body:
        assert body["status"]["code"] == response.status_code, (response.status_code, body["status"])
