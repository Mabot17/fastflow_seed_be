# ============================================= Start Noted API Middleware ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Script ini digunakan untuk menghandle response sebelum dilakukan oleh pydantic
# 2. Sementara response yang sudah didaftarkan menjadi custom
# - HTTP_401_UNAUTHORIZED
# - HTTP_404_METHOD_NOT_FOUND
# - HTTP_405_METHOD_NOT_ALLOWED
# - HTTP_422_UNPROCESSABLE_ENTITY
# - HTTP_500_INTERNAL_SERVER_ERROR
# 3. Default response bisa di cek di core.response_handle.py
# ============================================= END Noted Middleware ===================================
import time
import logging

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette import status

from core.utils.response_handle import (
    show_unauthorized,
    show_not_found,
    show_method_not_allowed,
    show_validation_response,
    show_bad_response
)

# function generate response sesuai dengan code yang dikirim, ini bisa dicek
def generate_response(http_code: int, err: dict = None):
    content = None

    if http_code == 401:
        content = show_unauthorized(status_code=http_code, error=err)
    elif http_code == 405:
        content = show_method_not_allowed(status_code=http_code, error=err)
    elif http_code == 422:
        # Hapus error kode pydantic
        # "url": "https://errors.pydantic.dev/2.8/v/missing"
        errors = err
        for error in errors:
            if "url" in error:
                del error["url"]
        content = show_validation_response(status_code=http_code, error=errors)
    elif http_code == 500:
        content = show_bad_response(status_code=http_code, error=err)

    return content

# INIT Middleware handle code response
async def api_middleware_response(request: Request, call_next):
    start_time = time.time()
    logging.info(f"START {request.method} {request.url}")

    try:
        response = await call_next(request)
        if response.status_code == 401:
            err_custom = f"Token tidak valid. Silahkan login kembali."
            return await not_authenticated_handler(request, HTTPException, err_custom)
        elif response.status_code == 405:
            err_custom = f"Metode Anda: ({request.method}) tidak diizinkan. Seharusnya menggunakan: ({response.headers.get('allow')})"
            return await method_not_allowed_handler(request, HTTPException, err_custom)

        return response
    finally:
        duration = time.time() - start_time
        logging.info(f"END {request.method} {request.url} | {duration:.2f}s")

# Custom middleware handle error 404 not found
async def not_authenticated_handler(request: Request, exc: Exception, err_custom):
    custom_not_authenticated_response = generate_response(http_code=401, err=err_custom)
    return JSONResponse(content=jsonable_encoder(custom_not_authenticated_response), status_code=status.HTTP_401_UNAUTHORIZED)

# Custom middleware handle error 405
async def method_not_allowed_handler(request: Request, exc: HTTPException, err_custom):
    custom_method_not_allowed_response = generate_response(http_code=405, err=err_custom)
    return JSONResponse(content=jsonable_encoder(custom_method_not_allowed_response), status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

# Custom middleware handle error 422 (Dipanggil independend di main sebagai exception)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_original = exc.errors()
    custom_validation_response = generate_response(http_code=422, err=error_original)
    return JSONResponse(content=jsonable_encoder(custom_validation_response), status_code=422)

# Custom middleware handle error 500
async def general_exception_handler(request: Request, exc: Exception, err_custom):
    custom_method_not_allowed_response = generate_response(http_code=500, err=err_custom)
    return JSONResponse(content=jsonable_encoder(custom_method_not_allowed_response), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


#  Untuk log maintenance, langsung mengubah di api_router.py
class MaintenanceException(Exception):
    def __init__(self, message: str):
        self.message = message


async def maintenance_exception_handler(
    request: Request,
    exc: MaintenanceException,
):
    
    from core.utils.response_handle import (
        show_bad_response,
    )
        
    result = show_bad_response(
        error=exc.message,
        http_request=request,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )

    return JSONResponse(
        content=result,
        status_code=result["status"]["code"],
    )