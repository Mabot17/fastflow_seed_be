# ============================================= Start Noted Socket Metadata ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Prefix unik per jenis event (dipakai FE), contoh event: "connection:join_room:request"
# 2. Tambahkan PREFIX_xxx baru di sini saat membuat channel baru
# ============================================= END Noted Socket Metadata ===================================
PREFIX_CONNECTION = "connection"

EVENT_REQUEST = "request"
EVENT_RESPONSE = "response"


def build_event_request(prefix: str, event: str) -> str:
    return f"{prefix}:{event}:{EVENT_REQUEST}"


def build_event_response(prefix: str, event: str) -> str:
    return f"{prefix}:{event}:{EVENT_RESPONSE}"
