# ============================================= Start Noted Socket Connection ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Event koneksi dasar: connect, disconnect, join_room
# 2. Koneksi WAJIB membawa token JWT: io(url, { auth: { token: "<access_token>" } })
# 3. Contoh channel baru: buat core/socket/channel/<nama>_channel.py dengan fungsi register_<nama>_events(sio),
#    lalu panggil di socket_router.py
# ============================================= END Noted Socket Connection ===================================
import logging

from jose import JWTError

from core.socket.socket_metadata import PREFIX_CONNECTION, build_event_request, build_event_response
from core.utils.token import decode_token


def register_connection_events(sio):
    @sio.on("connect")
    async def handle_connect(sid, environ, auth=None):
        token = (auth or {}).get("token")
        try:
            payload = decode_token(token) if token else None
        except JWTError:
            payload = None
        if not payload:
            logging.warning(f"Socket ditolak (token tidak valid): {sid}")
            return False  # tolak koneksi

        await sio.save_session(sid, {"user_id": payload.get("user_id"), "user_name": payload.get("user_name")})
        await sio.emit("connect", {"message": "Websocket is Connected!"}, room=sid)

    @sio.on("disconnect")
    async def handle_disconnect(sid, reason=None):
        logging.info(f"Socket terputus: {sid} ({reason})")

    @sio.on(build_event_request(PREFIX_CONNECTION, "join_room"))
    async def handle_join_room(sid, data):
        room_id = (data or {}).get("room_id")
        if not room_id:
            return
        await sio.enter_room(sid, room_id)
        await sio.emit(build_event_response(PREFIX_CONNECTION, "join_room"), {"rooms": list(sio.rooms(sid))}, to=sid)
