# ============================================= Start Noted Model ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Koneksi Table di database
# 2. Relasi Table di database bisa juga dilakukan disini
# 3. Dibuat otomatis oleh `erp module new` dari table `users`
# ============================================= END Noted Model ===================================
from database import Base
from sqlalchemy import Column, DateTime, Integer, SmallInteger, String, Text


class UsersModel(Base):
    __tablename__ = "users"

    user_id = Column("user_id", Integer, primary_key=True, index=True)
    user_name = Column("user_name", String(50))
    user_passwd = Column("user_passwd", String(50))
    user_passwd_sha = Column("user_passwd_sha", String(255))
    user_karyawan = Column("user_karyawan", Integer)
    user_supplier_id = Column("user_supplier_id", Integer)
    user_log = Column("user_log", DateTime)
    user_log_end = Column("user_log_end", DateTime)
    user_groups = Column("user_groups", Integer)
    user_kode = Column("user_kode", String(2))
    user_keterangan = Column("user_keterangan", String(250))
    user_aktif = Column("user_aktif", String(11))
    user_cabang = Column("user_cabang", String(70))
    user_cabang_default = Column("user_cabang_default", Integer)
    fcm_token = Column("fcm_token", Text)
    fcm_token_excelsa = Column("fcm_token_excelsa", Text)
    api_token = Column("api_token", String(100))
    user_secret_otp = Column("user_secret_otp", String(100))
    user_aktif_2fa = Column("user_aktif_2fa", String(11))
    user_device_id = Column("user_device_id", String(100))
    user_otp_code = Column("user_otp_code", String(6))
    user_login_status = Column("user_login_status", String(1))
    updated_at = Column("user_updated_at", DateTime)
    updated_by = Column("user_updated_by", String(50))
    created_at = Column("user_created_at", DateTime)
    created_by = Column("user_created_by", String(50))
    revised = Column("revised", SmallInteger)
    deleted_at = Column("user_deleted_at", DateTime)
    deleted_by = Column("user_deleted_by", String(50))
