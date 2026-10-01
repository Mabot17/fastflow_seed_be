# ============================================= Start Noted CRUD ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Proses login: cari user -> cek status aktif -> verifikasi password (pbkdf2) -> buat token JWT
# 2. Mengembalikan (status_code, pesan, data) supaya router hanya membentuk respons
# ============================================= END Noted CRUD ===================================
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from core.config import ACCESS_TOKEN_EXPIRE_DAYS
from core.modules.users.crud.users_check import check_users, check_users_login
from core.shared.json_helpers.users.json_users import json_users
from core.utils.hashing import Hash
from core.utils.token import create_access_token


async def login_user(db: Session, user_name: str, password: str) -> tuple[int, str, dict | None]:
    user = await check_users_login(db, user_name=user_name)
    if not user:
        return 404, "Username belum terdaftar", None
    if user.user_aktif != "Aktif":
        return 403, "User tidak aktif, hubungi administrator", None
    if not Hash.verify(hashed_password=user.user_passwd_sha, plain_password=password):
        return 403, "Username atau Password tidak sesuai", None

    try:
        access_token = create_access_token(data={
            "sub": user.user_name,
            "user_id": user.user_id,
            "user_name": user.user_name,
            "grup": str(user.user_groups) if user.user_groups is not None else None,
        })

        now = datetime.now()
        user.api_token = access_token[:100]          # kolom api_token varchar(100): simpan sebagai penanda saja
        user.user_log = now
        user.user_log_end = now + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        user.user_login_status = "Y"
        db.commit()
        db.refresh(user)

        return 200, "Login Berhasil.", {
            "access_token": access_token,
            "token_type": "bearer",
            "data": await json_users(db=db, users_data_row=user),
        }
    except Exception as e:
        db.rollback()
        logging.error(f"Exception login_user: {e}")
        return 500, "Login gagal diproses", None


async def logout_user(db: Session, user_id: int) -> bool:
    user = await check_users(db, user_id=user_id)
    if not user:
        return False
    try:
        user.api_token = None
        user.user_login_status = "N"
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Exception logout_user: {e}")
        return False
