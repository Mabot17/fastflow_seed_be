# ============================================= Start Noted Schema ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Dibuat oleh `fastflow module new` dari table `users`, lalu disesuaikan:
#    - kolom sensitif/internal (user_passwd, user_passwd_sha, api_token, user_secret_otp, user_otp_code,
#      user_log, user_log_end, user_login_status) TIDAK bisa diisi lewat API
#    - password dikirim lewat field `password`, disimpan sebagai hash di user_passwd_sha
# ============================================= END Noted Schema ===================================
from datetime import datetime
from fastapi import Query
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from core.shared.base import (
    PagingSchema,
    ResponseBaseSchema,
    ErrorSchema,
    RequestSchema
)

DEFAULT_USER_CABANG = "1" + "0" * 69


class UsersBaseDataSchema(BaseModel):
    user_name: str = Field(min_length=3, max_length=50)
    user_kode: Optional[str] = Field(default=None, max_length=2)
    user_groups: Optional[int] = None
    user_keterangan: Optional[str] = Field(default=None, max_length=250)
    user_aktif: Optional[Literal['Aktif', 'Tidak Aktif']] = 'Aktif'
    user_karyawan: Optional[int] = 0
    user_supplier_id: Optional[int] = None
    user_cabang: Optional[str] = Field(default=DEFAULT_USER_CABANG, max_length=70)
    user_cabang_default: Optional[int] = None
    user_aktif_2fa: Optional[Literal['Aktif', 'Tidak Aktif']] = None
    user_device_id: Optional[str] = Field(default=None, max_length=100)
    fcm_token: Optional[str] = None
    fcm_token_excelsa: Optional[str] = None


class UsersDataSchema(UsersBaseDataSchema):
    # Bentuk data di respons (info login ikut ditampilkan, password/token tidak)
    user_id: int
    user_log: Optional[datetime] = None
    user_log_end: Optional[datetime] = None
    user_login_status: Optional[Literal['Y', 'N']] = None


class UsersListSchema(ResponseBaseSchema):
    data: List[UsersDataSchema]
    paging: List[PagingSchema]
    error: ErrorSchema
    request: RequestSchema


class UsersSingleSchema(ResponseBaseSchema):
    data: UsersDataSchema
    error: ErrorSchema
    request: RequestSchema


class UsersRequestListSchema(BaseModel):
    # Inisialisasi obj & set nilai default untuk validasi pydantic
    keywords: Optional[str] = Field(default=None)
    page: int = Field(default=1, gt=0)
    results_per_page: int = Field(default=20, gt=0, le=100)
    user_aktif: Optional[Literal['Aktif', 'Tidak Aktif', 'Semua']] = Field(default='Semua')
    timestamp_data: Optional[bool] = Field(default=False)

    # as form = membuat sebuah form untuk dokumentasi
    @classmethod
    def as_form(
        cls,
        keywords: str = Query(None, description="Cari di user_name, user_kode, user_keterangan"),
        page: int = Query(1, gt=0),
        results_per_page: int = Query(20, gt=0, le=100),
        user_aktif: Literal['Aktif', 'Tidak Aktif', 'Semua'] = Query('Semua', description="Status Users"),
        timestamp_data: bool = Query(False, description="Jika true, JSON akan disertakan detail timestamp."),
    ):
        return cls(
            keywords=keywords,
            page=page,
            results_per_page=results_per_page,
            user_aktif=user_aktif,
            timestamp_data=timestamp_data,
        )


class UsersReqSchema(UsersBaseDataSchema):
    # Dipakai untuk POST (create): password wajib
    password: str = Field(min_length=8, max_length=100)


class UsersPutSchema(UsersBaseDataSchema):
    # Dipakai untuk PUT (update penuh). password opsional: diisi = ganti password
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)


class UsersPatchSchema(UsersBaseDataSchema):
    # Method patch: semua field opsional, hanya field yang dikirim yang diupdate
    user_name: Optional[str] = Field(default=None, min_length=3, max_length=50)
    user_kode: Optional[str] = Field(default=None, max_length=2)
    user_groups: Optional[int] = Field(default=None)
    user_keterangan: Optional[str] = Field(default=None, max_length=250)
    user_aktif: Optional[Literal['Aktif', 'Tidak Aktif']] = Field(default=None)
    user_karyawan: Optional[int] = Field(default=None)
    user_supplier_id: Optional[int] = Field(default=None)
    user_cabang: Optional[str] = Field(default=None, max_length=70)
    user_cabang_default: Optional[int] = Field(default=None)
    user_aktif_2fa: Optional[Literal['Aktif', 'Tidak Aktif']] = Field(default=None)
    user_device_id: Optional[str] = Field(default=None, max_length=100)
    fcm_token: Optional[str] = Field(default=None)
    fcm_token_excelsa: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)
