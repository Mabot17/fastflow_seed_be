# ============================================= Start Noted Database ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Koneksi utama dari DB_CONNECTION_URL (core/.env)
# 2. Dipakai di router lewat dependency: db: Session = Depends(get_db)
# 3. Butuh database tambahan? Buat engine + SessionLocal + get_db_xxx baru dengan pola yang sama,
#    dan tambahkan URL-nya di core/config.py & .env.example
# ============================================= END Noted Database ===================================
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import DB_CONNECTION_URL


def make_engine(url: str):
    if url.startswith("sqlite"):
        # Dipakai untuk test otomatis (SQLite in-memory)
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(
        url,
        pool_size=20,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=10,
    )


engine = make_engine(DB_CONNECTION_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
