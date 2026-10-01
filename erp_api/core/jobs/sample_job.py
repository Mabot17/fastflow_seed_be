# ============================================= Start Noted Sample Job ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Contoh job terjadwal. Didaftarkan di core/jobs/jobs_config.py -> register_jobs()
# 2. Job yang butuh database: buka session sendiri (SessionLocal()) dan tutup di finally
# ============================================= END Noted Sample Job ===================================
import logging

from core.utils.common import get_local_now


async def job_heartbeat():
    logging.info(f"[JOB] heartbeat {get_local_now():%Y-%m-%d %H:%M:%S}")
