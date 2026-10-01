# ============================================= Start Noted Router ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. POST /login  -> form username & password (dipakai juga tombol Authorize di /docs)
# 2. GET  /me     -> data user yang sedang login
# 3. POST /logout -> tandai user logout (token JWT tetap berlaku sampai kedaluwarsa)
# 4. Kesalahan login memakai 403/404, BUKAN 401 (401 diubah middleware menjadi "Token tidak valid")
# ============================================= END Noted Router ===================================
import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from core.modules.auth.crud.auth_crud import login_user, logout_user
from core.modules.auth.schema.login_schema import LoginResponseSchema, MeResponseSchema
from core.modules.users.crud.users_crud import select_users_by_id
from core.utils.oauth2 import get_current_user
from core.utils.response_handle import (
    get_example_responses,
    show_bad_response,
    show_not_found,
    show_success,
)
from core.utils.token import TokenData

routerLogin = APIRouter(tags=["Authentication"])

example_responses = get_example_responses(status_codes=[401, 422, 500])


@routerLogin.post("/login", response_model=LoginResponseSchema, responses=example_responses)
async def login(
    http_request: Request,
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
        **Catatan:**

        - `username`: user_name di table users \n
        - `password`: password user \n
        - Berhasil -> `access_token` (Bearer) untuk header `Authorization: Bearer <token>` \n
        - Gagal -> 404 (username belum terdaftar) / 403 (password salah / user tidak aktif)
    """
    try:
        code, message, payload = await login_user(db, user_name=request.username, password=request.password)
        if code != 200:
            result = {"status": {"code": code, "message": message}, "data": None, "error": message}
        else:
            result = {"status": {"code": 200, "message": message}, **payload, "error": None}
        return JSONResponse(content=result, status_code=result["status"]["code"])
    except Exception as e:
        logging.error(f"Exception login: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result["status"]["code"])


@routerLogin.get("/me", response_model=MeResponseSchema, responses=example_responses)
async def get_me(
    http_request: Request,
    identity: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data_user = await select_users_by_id(db, user_id=identity.user_id, timestamp_data=True)
        if not data_user:
            result = await show_not_found(http_request=http_request, error="User tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
        else:
            result = await show_success(data=data_user, http_request=http_request, status_code=status.HTTP_200_OK)
        return JSONResponse(content=result, status_code=result["status"]["code"])
    except Exception as e:
        logging.error(f"Exception me: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result["status"]["code"])


@routerLogin.post("/logout", responses=example_responses)
async def logout(
    http_request: Request,
    identity: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        if await logout_user(db, user_id=identity.user_id):
            result = await show_success(http_request=http_request, message="Logout Berhasil.", status_code=status.HTTP_200_OK)
        else:
            result = await show_not_found(http_request=http_request, error="User tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
        return JSONResponse(content=result, status_code=result["status"]["code"])
    except Exception as e:
        logging.error(f"Exception logout: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result["status"]["code"])
