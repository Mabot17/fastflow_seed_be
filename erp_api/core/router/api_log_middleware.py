# ============================================= Start Noted API Log Middleware ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Log setiap request (IP, user dari JWT, status, durasi) ke <STATIC_FILES_FOLDER>/logs/api_request.log
# 2. Blokir path mencurigakan (../, ~, <, >) dengan 403
# ============================================= END Noted API Log Middleware ===================================
import time
import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from core.utils.log import setup_custom_logger
from jose import JWTError
from typing import Optional
from core.utils.token import decode_token
from collections import defaultdict

# Logger
logger = setup_custom_logger("api_logger", "api_request.log")

# Simple in-memory tracking
IP_SCORE = defaultdict(int)

# Pattern detection
BLOCK_REGEX = re.compile(r"^/\.|(\.\./|~|`|<|>)", re.IGNORECASE)

# Extract user ID
def extract_user_id_from_token(auth_header: Optional[str]) -> str:
    if not auth_header or not auth_header.startswith("Bearer "):
        return "anonymous"
    token = auth_header.split(" ")[1]
    try:
        payload = decode_token(token)
        return str(payload.get("sub") or "unknown")
    except JWTError:
        return "invalid_token"
    
def get_ip_info(request: Request):
    host_ip = request.client.host  # IP dari NGINX / proxy

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        real_ip = x_forwarded_for.split(",")[0].strip()
    else:
        real_ip = request.headers.get("x-real-ip", host_ip)

    return host_ip, real_ip


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        host_ip, real_ip = get_ip_info(request)
        path = request.url.path
        method = request.method
        user_agent = request.headers.get("user-agent", "unknown")
        auth_header = request.headers.get("authorization")
        user_id = extract_user_id_from_token(auth_header)

        # Simpan ke state
        request.state.host_ip = host_ip
        request.state.real_ip = real_ip
        request.state.user_agent = user_agent
        request.state.user_id = user_id

        # =========================
        # DETECTION LAYER
        # =========================
        is_suspicious = bool(BLOCK_REGEX.search(path))

        if is_suspicious:
            IP_SCORE[real_ip] += 1

            logger.warning(
                f"[BLOCKED:{IP_SCORE[real_ip]}x] {real_ip} | {method} {path} | UA: {user_agent}"
            )

            # OPTIONAL: langsung block
            return Response(status_code=403)

        # =========================
        # NORMAL FLOW
        # =========================
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)

        log_message = (
            f"{host_ip} | {real_ip} | {request.method} {request.url.path} | "
            f"UserID: {user_id} | UA: {user_agent} | "
            f"Status: {response.status_code} | Time: {process_time}ms"
        )

        logger.info(log_message)

        return response
