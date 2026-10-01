# ============================================= Start Noted Socket Router ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Menggabungkan semua event socket yang didaftarkan
# 2. Semua channel wajib didaftarkan di register_all_events()
# ============================================= END Noted Socket Router ===================================
import socketio

from core.config import CORS_ORIGINS
from core.socket.socket_connection import register_connection_events

sio = socketio.AsyncServer(
    cors_allowed_origins="*" if CORS_ORIGINS == ["*"] else CORS_ORIGINS,
    async_mode="asgi",
)


def register_all_events():
    register_connection_events(sio)
    # register_xxx_events(sio)   <- daftarkan channel baru di sini


register_all_events()


def get_socket_app(main_app):
    """Bungkus FastAPI dengan Socket.IO (dipakai di main.py)."""
    return socketio.ASGIApp(sio, other_asgi_app=main_app)
