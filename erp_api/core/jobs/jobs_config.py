# ============================================= Start Noted Jobs Config ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Lifespan FastAPI: start/stop APScheduler bila ENABLE_SISTEM_JOB=1
# 2. Scheduler berjalan DI DALAM proses API. Bila memakai beberapa worker/instance,
#    aktifkan ENABLE_SISTEM_JOB di SATU instance saja supaya job tidak berjalan ganda
# 3. Tambah job: buat fungsi di core/jobs/<nama>_job.py lalu daftarkan di register_jobs()
# ============================================= END Noted Jobs Config ===================================
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from core import config
from core.jobs.sample_job import job_heartbeat


def register_jobs(scheduler: AsyncIOScheduler):
    # Contoh: tiap jam di menit 0 -> scheduler.add_job(fungsi, trigger="cron", minute=0)
    scheduler.add_job(job_heartbeat, trigger="cron", minute=0, id="heartbeat", replace_existing=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if config.ENABLE_SISTEM_JOB == 1:
        scheduler = AsyncIOScheduler(timezone=config.ZONA_WAKTU_SERVER)
        register_jobs(scheduler)
        scheduler.start()
        logging.info("Scheduler berjalan.")

    yield

    if scheduler:
        scheduler.shutdown()
        logging.info("Scheduler dimatikan.")
