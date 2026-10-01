# 🌱 seed_koffie_backend

Seed / kerangka backend **KoffieSoft** untuk memulai proyek baru: **Python**, **FastAPI**, **SQLAlchemy**,
**MySQL**, **Socket.IO** dan **APScheduler**, lengkap dengan alat bantu developer `erp`
(generate modul dari table, register router otomatis, rilis versi).

Kerangka ini diturunkan dari ERP Koffie dengan modul yang **bersih**: hanya `auth` (login) dan `users`.

---

## 📦 Kebutuhan

| Kebutuhan | Versi |
|---|---|
| Python | 3.11 – 3.13 |
| Poetry | 2.x (`pip install poetry`) |
| MySQL | 5.7 / 8.x |

---

## 🚀 Mulai

```bash
# 1. Install dependensi (sekaligus mendaftarkan perintah `erp`)
poetry install

# 2. Buat database & table awal (users + akun admin)
mysql -u root -p < "erp_updatedb/2026-10-01 00-00 init database.sql"
mysql -u root -p seed_koffie < "erp_updatedb/2026-10-01 00-01 init table users.sql"

# 3. Konfigurasi
cp erp_api/core/.env.example erp_api/core/.env
#    isi DB_CONNECTION_URL dan SECRET_KEY (buat dengan perintah di bawah)
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 4. Jalankan server (dari folder erp_api)
cd erp_api
poetry run uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Buka [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs), klik **Authorize**, login dengan:

| Username | Password |
|---|---|
| `admin` | `Admin@12345` |

> ⚠️ **Segera ganti password admin** setelah login pertama:
> `PATCH /sistem/users/{user_id}` dengan body `{"password": "PasswordBaru@123"}`.

### Memakai seed untuk proyek baru

1. Salin folder ini dengan nama proyek baru (atau jadikan template repository di git).
2. Ubah `name` & `description` di `pyproject.toml`, serta `TITLE_API` di `erp_api/core/router/api_metadata.py`.
3. Sesuaikan nama database di `erp_updatedb/... init database.sql` dan `DB_CONNECTION_URL`.
4. `poetry install`, lalu ikuti langkah **Mulai** di atas.

---

## 🔐 Konfigurasi `.env`

File `erp_api/core/.env` (salin dari `.env.example`, **jangan di-push**).
Environment variable sistem menimpa nilai di `.env` (memudahkan docker/CI).

| Variabel | Wajib | Keterangan |
|---|---|---|
| `DB_CONNECTION_URL` | ✅ | `mysql+pymysql://user:pass@host:3306/seed_koffie?charset=utf8mb4` |
| `SECRET_KEY` | ✅ | Kunci JWT, string acak panjang |
| `ACCESS_TOKEN_EXPIRE_DAYS` | | Masa berlaku token (default `1` hari) |
| `CORS_ORIGINS` | | Origin yang diizinkan, pisahkan koma. `*` hanya untuk development |
| `ROOT_PATH` | | Prefix path bila di belakang reverse proxy |
| `STATIC_FILES_FOLDER` | | Folder upload/log, default `erp_statics/`, di-mount di `/static` |
| `ENABLE_SISTEM_JOB` | | `1` = jalankan job terjadwal (lihat `core/jobs/`) |

---

## 🌐 Endpoint bawaan

| Method | Path | Keterangan |
|---|---|---|
| `POST` | `/login` | Login (form `username`, `password`) → `access_token` |
| `GET` | `/me` | Data user yang sedang login |
| `POST` | `/logout` | Tandai user logout |
| `GET` | `/sistem/users` | Daftar user (paging, `keywords`, filter `user_aktif`) |
| `GET` | `/sistem/users/{user_id}` | Detail user |
| `POST` | `/sistem/users` | Tambah user (password di-hash) |
| `PUT` / `PATCH` | `/sistem/users/{user_id}` | Ubah user (isi `password` = ganti password) |
| `DELETE` | `/sistem/users/{user_id}` | Hapus user (soft delete, tidak bisa hapus akun sendiri) |
| `GET` | `/version`, `/version/changelog` | Versi API & isi `CHANGELOG.md` |
| `GET` | `/docs`, `/redoc`, `/rapidoc` | Dokumentasi |

**Socket.IO** tersedia di server yang sama. Koneksi wajib membawa token:
`io("http://127.0.0.1:8001", { auth: { token: "<access_token>" } })`. Event bawaan: `connection:join_room:request`.

Format respons standar semua endpoint:

```json
{"status": {"code": 200, "message": "..."}, "data": {}, "paging": {}, "error": null, "request": {}}
```

HTTP status selalu sama dengan `status.code`.

---

## 📁 Struktur Folder

```plaintext
.
├── erp_api/
│   ├── main.py                        # Entry point (FastAPI + Socket.IO + middleware + scheduler)
│   ├── database.py                    # Koneksi database & get_db
│   └── core/
│       ├── config.py                  # Semua konfigurasi dari .env
│       ├── modules/                   # Kode domain: auth, users (+ modul baru dari `erp module new`)
│       ├── router/                    # Pendaftaran endpoint (lihat router_readme.md)
│       │   └── modules_registry/      # Daftar router per modul (<modul>_routers.py)
│       ├── shared/                    # Schema respons standar & json_helpers
│       ├── socket/                    # Socket.IO (koneksi + channel)
│       ├── jobs/                      # Job terjadwal (APScheduler)
│       ├── utils/                     # Token JWT, auth, hashing, respons standar, log, helper
│       └── .env.example
├── erp_tools/                         # Perintah `erp` (lihat tools_readme.md)
├── erp_updatedb/                      # SQL perubahan database (dijalankan manual)
├── erp_statics/                       # File upload & log (tidak di-push)
├── tests/                             # Test otomatis (pytest)
├── CHANGELOG.md
└── pyproject.toml / poetry.lock
```

---

## 🛠️ Membuat Modul Baru

```bash
# 1. Buat table lewat SQL di erp_updatedb/ dan jalankan di database
# 2. Lihat rencana, lalu generate + register
poetry run erp module new master/voucher --dry-run
poetry run erp module new master/voucher
```

Hasilnya modul standar 6 endpoint (`GET/POST /master/voucher`, `GET/PUT/PATCH/DELETE /master/voucher/{voucher_id}`)
lengkap dengan model, schema, check, crud, router, json helper, registrasi router & tag dokumentasi.
Kolom, tipe, field wajib, soft delete, filter status, cek duplikat dibaca dari struktur table.

> Pengguna **Git Bash**: jalankan dengan `MSYS_NO_PATHCONV=1 poetry run erp ...` bila memakai opsi
> yang diawali `/` (mis. `--api-prefix /master`), atau gunakan PowerShell/CMD.

Panduan lengkap: [`erp_tools/tools_readme.md`](erp_tools/tools_readme.md).

---

## 🧪 Test

```bash
poetry run pytest
```

Test memakai SQLite in-memory (tidak menyentuh MySQL) dan mencakup: kerangka & dokumentasi, login/me/logout,
CRUD users, generator, serta **aturan arsitektur** (kerangka tidak meng-import modul, `__init__.py` modul kosong,
setiap `JSONResponse` memakai `status_code`).

---

## 📐 Konvensi

- Struktur modul: `core/modules/<domain>/<fitur>/{model,schema,crud,router}/<fitur>_*.py`, buat dengan `erp module new`.
- `__init__.py` di `core/modules/**` kosong; router didaftarkan di `core/router/modules_registry/`.
- Kerangka (`core/utils`, `core/shared`, `core/socket`, `core/jobs`, `database.py`) tidak meng-import `core.modules`.
- Identitas user: `identity: TokenData = Depends(get_current_user)`.
- Setiap `JSONResponse` wajib `status_code=result['status']['code']`.
- HTTP 401 hanya untuk token tidak valid; kesalahan login lain memakai 403/404.
- Password tidak pernah dikembalikan di respons; field sensitif di blok `request` disamarkan (`***`).

Detail: [`erp_api/core/router/router_readme.md`](erp_api/core/router/router_readme.md) ·
[`erp_tools/tools_readme.md`](erp_tools/tools_readme.md) ·
[`erp_tools/modules_template/modules_template_readme.md`](erp_tools/modules_template/modules_template_readme.md)

---

## 🏭 Production

```bash
cd erp_api
poetry run gunicorn main:app -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8001
```

- `gunicorn` hanya berjalan di **Linux**. Di Windows (development) gunakan `uvicorn` seperti di bagian Mulai.
- Isi `CORS_ORIGINS` dengan domain frontend (bukan `*`) dan `SECRET_KEY` yang kuat.
- Socket.IO dengan lebih dari 1 worker butuh sticky session + message queue (mis. Redis);
  tanpa itu gunakan 1 worker per instance.
- Job terjadwal berjalan di dalam proses API: aktifkan `ENABLE_SISTEM_JOB=1` di **satu** instance saja.

---

## 🏷️ Rilis

```bash
poetry run erp release --dry-run        # preview versi & changelog
poetry run erp release                  # bump versi, update CHANGELOG, commit & tag (tanpa push)
```
