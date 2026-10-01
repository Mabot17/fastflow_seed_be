# ============================================= Start Noted JSON ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Response return wajib JSON/dict supaya bisa diolah kembali di router
# 2. Dibuat oleh `erp module new` dari table `users`, lalu disesuaikan:
#    kolom sensitif (user_passwd, user_passwd_sha, api_token, user_secret_otp, user_otp_code) TIDAK PERNAH dikirim
# ============================================= END Noted JSON ===================================
from sqlalchemy.orm import Session
from core.modules.users.model.users_model import UsersModel
from core.shared.json_helpers.json_global import json_data_timestamp, json_format_date
import logging


async def json_users(db: Session, users_data_row: UsersModel, timestamp_data: bool = False) -> dict:
    try:
        return_users = {
            "user_id": users_data_row.user_id,
            "user_name": users_data_row.user_name,
            "user_kode": users_data_row.user_kode,
            "user_groups": users_data_row.user_groups,
            "user_keterangan": users_data_row.user_keterangan,
            "user_aktif": users_data_row.user_aktif,
            "user_karyawan": users_data_row.user_karyawan,
            "user_supplier_id": users_data_row.user_supplier_id,
            "user_cabang": users_data_row.user_cabang,
            "user_cabang_default": users_data_row.user_cabang_default,
            "user_aktif_2fa": users_data_row.user_aktif_2fa,
            "user_device_id": users_data_row.user_device_id,
            "fcm_token": users_data_row.fcm_token,
            "fcm_token_excelsa": users_data_row.fcm_token_excelsa,
            "user_log": json_format_date(users_data_row.user_log),
            "user_log_end": json_format_date(users_data_row.user_log_end),
            "user_login_status": users_data_row.user_login_status,
            # Tambahkan properti lain dari users_data_row sesuai kebutuhan (JANGAN kolom password/token)
        }
        if timestamp_data:
            return_users["timestamp_data"] = await json_data_timestamp(db=db, data_row=users_data_row)

        return return_users
    except Exception as e:
        db.rollback()
        logging.error(f"Exception json_users: {e}")
        return {}
