# ============================================= Start Noted Log ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. setup_custom_logger(name, file_name) -> log ke console + file di <STATIC_FILES_FOLDER>/logs/
# 2. log_mysql_query_raw(query) -> tampilkan SQL mentah sebuah query SQLAlchemy (debug)
# ============================================= END Noted Log ===================================
import logging
import os
import sys

from sqlalchemy.dialects import mysql

from core import config


def setup_custom_logger(name: str, file_name: str = "default.log"):
    formatter = logging.Formatter(fmt="%(asctime)s - [%(levelname)s]%(filename)s:%(lineno)d > %(message)s")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        log_dir = os.path.join(config.UPLOAD_FOLDER, "logs")
        os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(os.path.join(log_dir, file_name), encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger


def log_mysql_query_raw(query) -> str:
    """
    Contoh:
        query = db.query(UsersModel).filter(UsersModel.user_name == "admin")
        print(log_mysql_query_raw(query))
    """
    try:
        compiled = query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
        return str(compiled)
    except Exception as e:
        return f"[ERROR] Gagal log SQL: {e}"
