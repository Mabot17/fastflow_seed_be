# ============================================= Start Noted Base Schema ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Schema respons standar {status, data, paging, error, request} yang dipakai semua modul
# 2. Dataclass filter untuk core.utils.common.apply_filters
# ============================================= END Noted Base Schema ===================================
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel


class PagingSchema(BaseModel):
    page: int
    total_pages: int
    records_per_page: int
    total_records: int


class ErrorSchema(BaseModel):
    List


class RequestSchema(BaseModel):
    List


class StatusResponseSchema(BaseModel):
    code: str
    message: str


class ResponseBaseSchema(BaseModel):
    status: StatusResponseSchema


class DaftarBaseSchema(BaseModel):
    paging: Optional[PagingSchema]


class StatusStringRecord(Enum):
    aktif = "Aktif"
    nonaktif = "Tidak Aktif"


@dataclass
class LikeFilter:
    """Pencarian sebagian teks (LIKE %...%)"""
    column: Any
    value: Optional[str]


@dataclass
class EqualFilter:
    """Nilai sama dengan (=), misal status/enum. Nilai 'Semua' diabaikan"""
    column: Any
    value: Optional[Any]


@dataclass
class DateRangeFilter:
    """Rentang tanggal (>= date_from dan <= date_to)"""
    column: Any
    date_from: Optional[date]
    date_to: Optional[date]


@dataclass
class KeywordFilter:
    """Quick search di banyak kolom sekaligus (OR)"""
    columns: List[Any]
    value: Optional[str]
