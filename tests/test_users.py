"""Test modul users: list, single, create, put, patch, delete."""
from conftest import ADMIN_PASSWORD, ADMIN_USER, assert_status_match
from core.modules.users.model.users_model import UsersModel
from core.utils.hashing import Hash

BASE = "/sistem/users"
SENSITIF = ("user_passwd", "user_passwd_sha", "api_token", "user_secret_otp", "user_otp_code")


def buat_user(client, auth_header, **data):
    payload = {"user_name": "kasir01", "password": "Kasir@12345", "user_kode": "02", "user_keterangan": "Kasir"}
    payload.update(data)
    return client.post(BASE, headers=auth_header, json=payload)


# ---------------- list & single ----------------
def test_list(client, auth_header):
    buat_user(client, auth_header)
    r = client.get(BASE, headers=auth_header)
    assert r.status_code == 200
    body = r.json()
    assert len(body["data"]) == 2
    assert body["paging"]["total_records"] == 2
    assert not any(k in row for row in body["data"] for k in SENSITIF)


def test_list_keywords_dan_filter_aktif(client, auth_header):
    buat_user(client, auth_header)
    buat_user(client, auth_header, user_name="gudang01", user_kode="03", user_keterangan="Gudang", user_aktif="Tidak Aktif")
    r = client.get(BASE, headers=auth_header, params={"keywords": "kasir"})
    assert [u["user_name"] for u in r.json()["data"]] == ["kasir01"]
    r = client.get(BASE, headers=auth_header, params={"user_aktif": "Tidak Aktif"})
    assert [u["user_name"] for u in r.json()["data"]] == ["gudang01"]


def test_list_kosong_404(client, auth_header):
    r = client.get(BASE, headers=auth_header, params={"keywords": "tidak-ada-yang-cocok"})
    assert r.status_code == 404
    assert_status_match(r)


def test_single(client, auth_header, admin):
    r = client.get(f"{BASE}/{admin.user_id}", headers=auth_header, params={"timestamp_data": True})
    assert r.status_code == 200
    assert r.json()["data"]["user_name"] == ADMIN_USER
    assert r.json()["data"]["timestamp_data"]["created_by"] == "system"


def test_single_tidak_ada_404(client, auth_header):
    r = client.get(f"{BASE}/9999", headers=auth_header)
    assert r.status_code == 404
    assert_status_match(r)


# ---------------- create ----------------
def test_create_password_di_hash_dan_tidak_bocor(client, db, auth_header):
    r = buat_user(client, auth_header)
    assert r.status_code == 201
    body = r.json()
    assert body["data"]["user_name"] == "kasir01"
    assert not any(k in body["data"] for k in SENSITIF)
    assert body["request"]["body"]["password"] == "***"          # body request disamarkan di respons
    user = db.query(UsersModel).filter(UsersModel.user_name == "kasir01").first()
    assert user.user_passwd_sha != "Kasir@12345" and Hash.verify(user.user_passwd_sha, "Kasir@12345")
    assert user.created_by == ADMIN_USER and user.user_karyawan == 0 and len(user.user_cabang) == 70


def test_create_user_baru_bisa_login(client, auth_header):
    buat_user(client, auth_header)
    r = client.post("/login", data={"username": "kasir01", "password": "Kasir@12345"})
    assert r.status_code == 200


def test_create_tidak_bisa_isi_kolom_sensitif(client, db, auth_header):
    buat_user(client, auth_header, api_token="paksa", user_passwd_sha="paksa", user_secret_otp="paksa")
    user = db.query(UsersModel).filter(UsersModel.user_name == "kasir01").first()
    assert user.api_token is None and user.user_secret_otp is None and user.user_passwd_sha != "paksa"


def test_create_user_name_duplikat_400(client, auth_header):
    r = buat_user(client, auth_header, user_name=ADMIN_USER, user_kode="09")
    assert r.status_code == 400
    assert_status_match(r)


def test_create_user_kode_duplikat_400(client, auth_header):
    r = buat_user(client, auth_header, user_kode="01")
    assert r.status_code == 400
    assert "User Kode" in r.json()["error"]


def test_create_validasi_422(client, auth_header):
    assert buat_user(client, auth_header, password="pendek").status_code == 422
    r = client.post(BASE, headers=auth_header, json={"user_name": "tanpa_password"})
    assert r.status_code == 422
    assert_status_match(r)


# ---------------- put & patch ----------------
def test_put(client, db, auth_header):
    user_id = buat_user(client, auth_header).json()["data"]["user_id"]
    r = client.put(f"{BASE}/{user_id}", headers=auth_header,
                   json={"user_name": "kasir01", "user_kode": "02", "user_keterangan": "Kasir Pagi"})
    assert r.status_code == 200
    user = db.get(UsersModel, user_id)
    db.refresh(user)
    assert user.user_keterangan == "Kasir Pagi" and user.revised == 1 and user.updated_by == ADMIN_USER
    assert Hash.verify(user.user_passwd_sha, "Kasir@12345")       # tanpa password -> password lama tetap


def test_put_ganti_password(client, auth_header):
    user_id = buat_user(client, auth_header).json()["data"]["user_id"]
    client.put(f"{BASE}/{user_id}", headers=auth_header, json={"user_name": "kasir01", "password": "BaruSekali@1"})
    assert client.post("/login", data={"username": "kasir01", "password": "BaruSekali@1"}).status_code == 200
    assert client.post("/login", data={"username": "kasir01", "password": "Kasir@12345"}).status_code == 403


def test_put_tidak_ada_404(client, auth_header):
    r = client.put(f"{BASE}/9999", headers=auth_header, json={"user_name": "siapa"})
    assert r.status_code == 404


def test_patch_hanya_field_dikirim(client, db, auth_header):
    user_id = buat_user(client, auth_header).json()["data"]["user_id"]
    r = client.patch(f"{BASE}/{user_id}", headers=auth_header, json={"user_keterangan": "Kasir Malam"})
    assert r.status_code == 200
    user = db.get(UsersModel, user_id)
    db.refresh(user)
    assert user.user_keterangan == "Kasir Malam" and user.user_kode == "02" and user.user_name == "kasir01"


def test_patch_user_name_duplikat_400(client, auth_header):
    user_id = buat_user(client, auth_header).json()["data"]["user_id"]
    r = client.patch(f"{BASE}/{user_id}", headers=auth_header, json={"user_name": ADMIN_USER})
    assert r.status_code == 400


# ---------------- delete ----------------
def test_delete_soft(client, db, auth_header):
    user_id = buat_user(client, auth_header).json()["data"]["user_id"]
    r = client.delete(f"{BASE}/{user_id}", headers=auth_header)
    assert r.status_code == 200
    user = db.get(UsersModel, user_id)
    db.refresh(user)
    assert user.deleted_at is not None and user.deleted_by == ADMIN_USER and user.user_aktif == "Tidak Aktif"
    assert client.get(f"{BASE}/{user_id}", headers=auth_header).status_code == 404
    assert client.post("/login", data={"username": "kasir01", "password": "Kasir@12345"}).status_code == 404


def test_delete_akun_sendiri_400(client, auth_header, admin):
    r = client.delete(f"{BASE}/{admin.user_id}", headers=auth_header)
    assert r.status_code == 400
    assert_status_match(r)


def test_delete_tidak_ada_404(client, auth_header):
    assert client.delete(f"{BASE}/9999", headers=auth_header).status_code == 404
