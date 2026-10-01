# ============================================= Start Noted CRUD ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Response return wajib JSON/dict supaya bisa diolah kembali di router
# 2. Dibuat oleh `erp module new` dari table `users`, lalu disesuaikan:
#    - hanya kolom di WRITABLE_FIELDS yang bisa diisi lewat API
#    - password di-hash (pbkdf2_sha256) ke user_passwd_sha, kolom user_passwd (legacy) tidak dipakai
# ============================================= END Noted CRUD ===================================
from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from core.modules.users.model.users_model import UsersModel
from core.modules.users.schema.users_schema import UsersReqSchema, UsersPutSchema, UsersRequestListSchema
from core.modules.users.crud.users_check import check_users
from core.utils.token import TokenData
from core.utils.hashing import Hash
from core.shared.json_helpers.users.json_users import json_users
from core.utils.common import start_from
from datetime import datetime
from typing import Dict
import logging

# Kolom yang boleh diisi lewat API (selain password). Kolom sensitif/internal sengaja tidak ada di sini.
WRITABLE_FIELDS = (
    "user_name", "user_kode", "user_groups", "user_keterangan", "user_aktif", "user_karyawan",
    "user_supplier_id", "user_cabang", "user_cabang_default", "user_aktif_2fa", "user_device_id",
    "fcm_token", "fcm_token_excelsa",
)


def apply_fields(user: UsersModel, data: dict):
    for field in WRITABLE_FIELDS:
        if field in data:
            setattr(user, field, data[field])
    if data.get("password"):
        user.user_passwd_sha = Hash.pbkdf2_sha256(data["password"])


async def get_crud_daftar_users(db: Session, request: UsersRequestListSchema) -> Dict:
    try:
        usersModel = aliased(UsersModel, name="usersModel")

        query = db.query(usersModel)
        if request.keywords and request.keywords.strip():
            keywords_lower = request.keywords.lower()
            query = query.filter(
                or_(
                    func.lower(usersModel.user_name).like(f"%{keywords_lower}%"),
                    func.lower(usersModel.user_kode).like(f"%{keywords_lower}%"),
                    func.lower(usersModel.user_keterangan).like(f"%{keywords_lower}%"),
                )
            )

        filter = []

        # Filter belum pernah dihapus
        filter.append(
            or_(
                usersModel.deleted_at.is_(None),
                usersModel.deleted_at == "0000-00-00 00:00:00"
            )
        )
        filter.append(usersModel.deleted_by.is_(None))

        # Filter berdasarkan user_aktif
        if request.user_aktif is not None and request.user_aktif != 'Semua':
            filter.append(usersModel.user_aktif == request.user_aktif)

        # Gabungkan semua filter menggunakan operator AND
        query = query.filter(and_(*filter))

        count = query.count()

        qr_data = (
            query.order_by(usersModel.user_id.desc())
            .limit(request.results_per_page)
            .offset(start_from(request.page, request.results_per_page))
            .all()
        )

        result_data = [
            await json_users(db=db, users_data_row=row, timestamp_data=request.timestamp_data)
            for row in qr_data
        ]

        if result_data:
            return {"data": result_data, "total_data": count}
        else:
            return {"data": None, "total_data": 0}

    except IntegrityError as e:
        logging.error(f"IntegrityError: {e}")
        return {"data": None, "total_data": 0}
    except SQLAlchemyError as e:
        logging.error(f"SQLAlchemyError: {e}")
        return {"data": None, "total_data": 0}
    except Exception as e:
        logging.error(e)
        return {"data": None, "total_data": 0}


async def select_users_by_id(
    db: Session,
    user_id: int,
    timestamp_data: bool = False
) -> Dict:
    try:
        result = await check_users(db, user_id=user_id)

        if result:
            return await json_users(
                db=db,
                users_data_row=result,
                timestamp_data=timestamp_data
            )
        else:
            return None
    except IntegrityError as e:
        logging.error(f"IntegrityError: {e}")
        return None
    except SQLAlchemyError as e:
        logging.error(f"SQLAlchemyError: {e}")
        return None
    except Exception as e:
        logging.error(e)
        return None


async def create_data_users(db: Session, users_data_create: UsersReqSchema, identity: TokenData):
    new_users = UsersModel()
    try:
        apply_fields(new_users, users_data_create.model_dump())

        new_users.created_at = datetime.now()
        new_users.created_by = identity.user_name

        db.add(new_users)
        db.commit()
        db.refresh(new_users)

        return await json_users(
            db=db,
            users_data_row=new_users
        )
    except IntegrityError as e:
        db.rollback()
        logging.error(f"IntegrityError: {e}")
        return None  # Tangani kesalahan unik di endpoint
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"SQLAlchemyError: {e}")
        return None
    except Exception as e:
        db.rollback()
        logging.error(e)
        return None


async def update_data_users(db: Session, user_id: int, users_data_update: UsersPutSchema, identity: TokenData):
    try:
        old_users = await check_users(db, user_id=user_id)
        if old_users:
            apply_fields(old_users, users_data_update.model_dump())

            # Update data flag
            old_users.revised = (old_users.revised or 0) + 1
            old_users.updated_by = identity.user_name
            old_users.updated_at = datetime.now()

            db.commit()
            db.refresh(old_users)

            return await json_users(
                db=db,
                users_data_row=old_users
            )
        else:
            return None
    except IntegrityError as e:
        db.rollback()
        logging.error(f"IntegrityError: {e}")
        return None  # Tangani kesalahan unik di endpoint
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"SQLAlchemyError: {e}")
        return None
    except Exception as e:
        db.rollback()
        logging.error(e)
        return None


# Update method patch, jadi bisa diupdate salah satu kolom / bbrp kolom saja. tanpa pengecekan required dahulu
async def partial_update_data_users(db: Session, user_id: int, users_data_update: dict, identity: TokenData):
    try:
        old_patch_users = await check_users(db, user_id=user_id)
        if old_patch_users:
            # Hanya field yang dikirim (exclude_unset) & ada di WRITABLE_FIELDS / password
            apply_fields(old_patch_users, users_data_update)

            # Update data flag
            old_patch_users.revised = (old_patch_users.revised or 0) + 1
            old_patch_users.updated_by = identity.user_name
            old_patch_users.updated_at = datetime.now()

            db.commit()
            db.refresh(old_patch_users)

            return await json_users(
                db=db,
                users_data_row=old_patch_users
            )
        else:
            return None
    except IntegrityError as e:
        db.rollback()
        logging.error(f"IntegrityError: {e}")
        return None  # Tangani kesalahan unik di endpoint
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"SQLAlchemyError: {e}")
        return None
    except Exception as e:
        db.rollback()
        logging.error(f"Exception: {e}")
        return None


async def delete_data_users(db: Session, user_id: int, identity: TokenData):
    try:
        deleted_users = await check_users(db, user_id=user_id)
        if not deleted_users:
            return None

        deleted_users.user_aktif = 'Tidak Aktif'
        deleted_users.api_token = None
        deleted_users.user_login_status = 'N'
        deleted_users.deleted_by = identity.user_name
        deleted_users.deleted_at = datetime.now()

        db.commit()
        db.refresh(deleted_users)

        return await json_users(
            db=db,
            users_data_row=deleted_users
        )
    except IntegrityError as e:
        db.rollback()
        logging.error(f"IntegrityError: {e}")
        return None  # Tangani kesalahan unik di endpoint
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"SQLAlchemyError: {e}")
        return None
    except Exception as e:
        db.rollback()
        logging.error(e)
        return None
