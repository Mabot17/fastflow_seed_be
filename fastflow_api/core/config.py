# ============================================= Start Noted Config ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Semua konfigurasi dibaca dari fastflow_api/core/.env (salin dari .env.example)
# 2. Environment variable sistem (os.environ) menimpa nilai di .env -> memudahkan docker/CI/test
# 3. Tambahkan konfigurasi baru di sini, jangan membaca .env langsung dari modul lain
# ============================================= END Noted Config ===================================
import os
from pathlib import Path
from dotenv import dotenv_values

ZONA_WAKTU_SERVER = "Asia/Jakarta"

ROOT_FOLDER = Path(__file__).resolve().parents[2]          # root repo
ENV_FILE = Path(__file__).resolve().parent / ".env"

config = {**dotenv_values(ENV_FILE), **os.environ}


def _get(key, default=None, required=False):
    value = config.get(key)
    if value in (None, ""):
        if required:
            raise RuntimeError(f"Konfigurasi `{key}` wajib diisi di {ENV_FILE} (lihat .env.example)")
        return default
    return value


def _int(key, default):
    return int(_get(key, default))


# ---------- Aplikasi ----------
ROOT_PATH = _get("ROOT_PATH", "")
CORS_ORIGINS = [o.strip() for o in _get("CORS_ORIGINS", "*").split(",") if o.strip()]
ENABLE_SISTEM_JOB = _int("ENABLE_SISTEM_JOB", 0)

# ---------- Folder file statis / upload / log ----------
UPLOAD_FOLDER = Path(_get("STATIC_FILES_FOLDER", ROOT_FOLDER / "fastflow_statics"))
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# ---------- Database ----------
DB_CONNECTION_URL = _get("DB_CONNECTION_URL", required=True)

# ---------- Token JWT ----------
SECRET_KEY = _get("SECRET_KEY", required=True)
ACCESS_TOKEN_EXPIRE_DAYS = _int("ACCESS_TOKEN_EXPIRE_DAYS", 1)
