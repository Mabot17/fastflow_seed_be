# ============================================= Start Noted API Metadata ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Judul, versi & deskripsi API (VERSI_API diubah otomatis oleh `fastflow release`)
# 2. TAGS_METADATA_API -> urutan & deskripsi tag di /docs. "name" harus sama dengan tags=[...] di APIRouter
# 3. Tag modul baru ditambahkan otomatis oleh `fastflow module new` / `fastflow module register`
# ============================================= END Noted API Metadata ===================================

TITLE_API = "FastFlow Seed API"
VERSI_API = "0.0.2"

TAGS_METADATA_API = [
    {
        "name": "Version",
        "description": """
    Versi API & changelog
        """,
    },
    {
        "name": "Authentication",
        "description": """
    Login untuk mendapatkan access token (Bearer).
    Hampir semua endpoint hanya bisa diakses dengan access token.
        """,
    },
    {
        "name": "Sistem - Users",
        "description": """
    Manajemen user: daftar, tambah, ubah, hapus user
        """
    },
]

DESCRIPTION_API = """
Seed backend FastFlow: FastAPI + SQLAlchemy + MySQL.

- Format respons standar: `{status: {code, message}, data, paging, error, request}`
- HTTP status selalu sama dengan `status.code`
- Login di `POST /login`, lalu klik **Authorize** dan isi username & password
"""
