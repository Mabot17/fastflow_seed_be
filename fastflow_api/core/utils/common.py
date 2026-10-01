# ============================================= Start Noted Common ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Helper umum yang tidak bergantung pada modul mana pun (paging, filter, waktu, konversi)
# 2. Jangan meng-import core.modules.* dari file ini (supaya kerangka tetap bebas modul)
# ============================================= END Noted Common ===================================
from datetime import datetime, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, or_

from core.config import ZONA_WAKTU_SERVER
from core.shared.base import DateRangeFilter, EqualFilter, KeywordFilter, LikeFilter

SUCCESS = "success"
FAILED = "failed"

BULAN = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


def start_from(page: int, resultperpage: int) -> int:
    return (page - 1) * resultperpage


def total_pages(total_records: int, records_per_page: int) -> int:
    div, mod = divmod(total_records, records_per_page)
    return div + 1 if mod > 0 else div


def get_local_now(timezone: str | None = None) -> datetime:
    try:
        tz = ZoneInfo(timezone or ZONA_WAKTU_SERVER)
    except Exception:
        tz = ZoneInfo(ZONA_WAKTU_SERVER)
    return datetime.now(dt_timezone.utc).astimezone(tz)


def tgl_indo(waktu: datetime) -> str:
    return f"{waktu.day} {BULAN[waktu.month]} {waktu.year}" if waktu else ""


def str_to_bool(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def apply_filters(query, filters: list):
    """
    Terapkan daftar filter (KeywordFilter, LikeFilter, EqualFilter, DateRangeFilter) ke query.

    Contoh:
        query = apply_filters(query, [
            KeywordFilter(columns=[UsersModel.user_name, UsersModel.user_keterangan], value=request.keywords),
            EqualFilter(column=UsersModel.user_aktif, value=request.user_aktif),
        ])
    """
    conditions = []
    for f in filters:
        if isinstance(f, KeywordFilter):
            if f.value and f.value.strip():
                kw = f.value.lower()
                query = query.filter(or_(*[func.lower(col).like(f"%{kw}%") for col in f.columns]))
        elif isinstance(f, LikeFilter):
            if f.value and f.value.strip():
                conditions.append(func.lower(f.column).like(f"%{f.value.lower()}%"))
        elif isinstance(f, EqualFilter):
            if f.value is not None and f.value != "Semua":
                conditions.append(f.column == f.value)
        elif isinstance(f, DateRangeFilter):
            if f.date_from:
                conditions.append(f.column >= f.date_from)
            if f.date_to:
                conditions.append(f.column <= f.date_to)
    if conditions:
        query = query.filter(and_(*conditions))
    return query
