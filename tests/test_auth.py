"""Test login, me, logout."""
from conftest import ADMIN_PASSWORD, ADMIN_USER, assert_status_match
from core.modules.users.model.users_model import UsersModel

SENSITIF = ("user_passwd", "user_passwd_sha", "api_token", "user_secret_otp", "user_otp_code")


def test_login_berhasil(client, db):
    r = client.post("/login", data={"username": ADMIN_USER, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["data"]["user_name"] == ADMIN_USER
    assert not any(k in body["data"] for k in SENSITIF)
    user = db.query(UsersModel).filter(UsersModel.user_name == ADMIN_USER).first()
    db.refresh(user)
    assert user.user_login_status == "Y" and user.user_log is not None


def test_login_password_salah_403(client):
    r = client.post("/login", data={"username": ADMIN_USER, "password": "salah-sekali"})
    assert r.status_code == 403
    assert_status_match(r)
    assert r.json()["status"]["message"] == "Username atau Password tidak sesuai"


def test_login_user_tidak_ada_404(client):
    r = client.post("/login", data={"username": "tidak_ada", "password": "apapun123"})
    assert r.status_code == 404
    assert_status_match(r)


def test_login_user_tidak_aktif_403(client, db, admin):
    admin.user_aktif = "Tidak Aktif"
    db.commit()
    r = client.post("/login", data={"username": ADMIN_USER, "password": ADMIN_PASSWORD})
    assert r.status_code == 403
    assert "tidak aktif" in r.json()["status"]["message"]


def test_login_tanpa_form_422(client):
    r = client.post("/login", data={})
    assert r.status_code == 422
    assert_status_match(r)


def test_me(client, auth_header):
    r = client.get("/me", headers=auth_header)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["user_name"] == ADMIN_USER
    assert "timestamp_data" in data
    assert not any(k in data for k in SENSITIF)


def test_me_tanpa_token_401(client):
    assert client.get("/me").status_code == 401


def test_logout(client, db, auth_header, admin):
    r = client.post("/logout", headers=auth_header)
    assert r.status_code == 200
    db.refresh(admin)
    assert admin.user_login_status == "N" and admin.api_token is None
