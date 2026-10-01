# ============================================= Start Noted JSON Global ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Helper JSON yang dipakai semua modul (format tanggal, blok timestamp)
# 2. Jangan meng-import core.modules.* dari file ini (supaya kerangka tetap bebas modul)
# ============================================= END Noted JSON Global ===================================
import logging

from sqlalchemy.orm import Session

ZERO_DATES = ("0000-00-00", "0000-00-00 00:00:00")


def json_format_date(date_value, date_format: str = "%Y-%m-%d %H:%M:%S"):
    """Format date/datetime/time menjadi string. None / '0000-00-00' / nilai tidak valid -> None."""
    if not date_value or str(date_value) in ZERO_DATES:
        return None
    try:
        return date_value.strftime(date_format)
    except AttributeError:
        return None


async def json_data_timestamp(db: Session, data_row=None) -> dict:
    """Blok `timestamp_data`: siapa & kapan data dibuat/diubah/dihapus (atribut model standar)."""
    if data_row is None:
        return {}
    try:
        return {
            "created_by": getattr(data_row, "created_by", None),
            "created_at": json_format_date(getattr(data_row, "created_at", None)),
            "updated_by": getattr(data_row, "updated_by", None),
            "updated_at": json_format_date(getattr(data_row, "updated_at", None)),
            "deleted_by": getattr(data_row, "deleted_by", None),
            "deleted_at": json_format_date(getattr(data_row, "deleted_at", None)),
            "revised": getattr(data_row, "revised", None),
        }
    except Exception as e:
        logging.error(f"Exception json_data_timestamp: {e}")
        return {}
