# ============================================= Start Noted Check ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Pengecekan data Users (ada / tidak, duplikat)
# 2. File ini HANYA boleh meng-import model & sqlalchemy (jangan import crud/json_helpers),
#    supaya bisa dipakai dari router, crud, json_helpers, maupun modul lain tanpa circular import
# 3. Dibuat otomatis oleh `erp module new` dari table `users`
# ============================================= END Noted Check ===================================
from sqlalchemy import and_
from sqlalchemy.orm import Session
from core.modules.users.model.users_model import UsersModel


async def check_users(
    db: Session, user_id: int, exclude_user_id: int = None
):
    filter = [
        UsersModel.user_id == user_id,
        UsersModel.deleted_at.is_(None),
        UsersModel.deleted_by.is_(None),
    ]

    if exclude_user_id:
        filter.append(UsersModel.user_id != exclude_user_id)

    return db.query(UsersModel).filter(and_(*filter)).first()


async def check_users_user_name(
    db: Session, user_name: str, exclude_user_id: int = None
):
    filter = [
        UsersModel.user_name == user_name,
        UsersModel.deleted_at.is_(None),
        UsersModel.deleted_by.is_(None),
    ]

    if exclude_user_id:
        filter.append(UsersModel.user_id != exclude_user_id)

    return db.query(UsersModel).filter(and_(*filter)).first()


async def check_users_kode(
    db: Session, user_kode: str, exclude_user_id: int = None
):
    # user_kode UNIQUE di database untuk semua baris (termasuk yang sudah dihapus), jadi tanpa filter deleted
    filter = [UsersModel.user_kode == user_kode]

    if exclude_user_id:
        filter.append(UsersModel.user_id != exclude_user_id)

    return db.query(UsersModel).filter(and_(*filter)).first()


async def check_users_login(db: Session, user_name: str):
    # Dipakai login: user belum dihapus (status aktif dicek terpisah supaya pesannya jelas)
    return await check_users_user_name(db, user_name=user_name)
