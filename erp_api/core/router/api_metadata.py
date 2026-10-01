# ============================================= Start Noted API Metadata ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Judul, versi & deskripsi API (VERSI_API diubah otomatis oleh `erp release`)
# 2. TAGS_METADATA_API -> urutan & deskripsi tag di /docs. "name" harus sama dengan tags=[...] di APIRouter
# 3. Tag modul baru ditambahkan otomatis oleh `erp module new` / `erp module register`
# ============================================= END Noted API Metadata ===================================

TITLE_API = "KoffieSoft Seed API"
VERSI_API = "0.0.1"

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
Seed backend KoffieSoft: FastAPI + SQLAlchemy + MySQL.

- Format respons standar: `{status: {code, message}, data, paging, error, request}`
- HTTP status selalu sama dengan `status.code`
- Login di `POST /login`, lalu klik **Authorize** dan isi username & password
"""
