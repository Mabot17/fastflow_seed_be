# ============================================= Start Noted Router ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. routerUsers = APIRouter, didaftarkan lewat core/router/modules_registry/users_routers.py & api_router.py
# 2. identity: TokenData = Depends(get_current_user) -> endpoint wajib memakai token
# 3. get_all_users (router) & get_crud_daftar_users (crud) dibedakan supaya mudah ditelusuri
# 4. Setiap JSONResponse wajib status_code=result['status']['code'] (HTTP status = body status)
# 5. Dibuat oleh `erp module new` dari table `users`, lalu ditambah: cek duplikat user_kode & larangan hapus akun sendiri
# ============================================= END Noted Router ===================================
from fastapi import (
    APIRouter,
    Depends,
    status,
    Path,
    Query,
    Request,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from core.modules.users.crud.users_crud import (
    get_crud_daftar_users,
    select_users_by_id,
    create_data_users,
    update_data_users,
    partial_update_data_users,
    delete_data_users
)
from core.modules.users.crud.users_check import (
    check_users,
    check_users_user_name,
    check_users_kode,
)
from core.modules.users.schema.users_schema import (
    UsersRequestListSchema,
    UsersListSchema,
    UsersReqSchema,
    UsersPutSchema,
    UsersPatchSchema,
    UsersSingleSchema
)
from core.utils.oauth2 import get_current_user
from core.utils.token import TokenData
from core.utils.response_handle import (
    show_success_list,
    show_success,
    show_not_found,
    show_bad_response,
    show_bad_request,
    get_example_responses
)
import logging

# START CODE ROUTE Users
routerUsers = APIRouter(tags=["Sistem - Users"], prefix="/users")

example_responses = get_example_responses(status_codes=[401, 404, 405, 422, 500])


# ROUTE LIST & SEARCH DATA Users
@routerUsers.get("", response_model=UsersListSchema, responses=example_responses)
async def get_all_users(
    http_request: Request,
    request: UsersRequestListSchema = Depends(UsersRequestListSchema.as_form),
    identity: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        daftar = await get_crud_daftar_users(db=db, request=request)

        if daftar.get('total_data'):
            result = await show_success_list(
                http_request=http_request,
                data=daftar.get('data'),
                total_data=daftar.get('total_data'),
                page=request.page,
                results_per_page=request.results_per_page,
                is_paging=True,
            )
        else:
            result = await show_not_found(http_request=http_request, status_code=404)

        return JSONResponse(content=result, status_code=result['status']['code'])
    except Exception as e:
        logging.error(f"Exception list_users: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result['status']['code'])


# ROUTE GET DATA Users BY ID
@routerUsers.get("/{user_id}", response_model=UsersSingleSchema, responses=example_responses)
async def get_users(
    http_request: Request,
    timestamp_data: bool = Query(False, description="Jika true, JSON akan disertakan detail timestamp."),
    user_id: int = Path(..., description="ID dari API GET `/sistem/users` (get_all_users) -> key `user_id` "),
    db: Session = Depends(get_db),
    identity: TokenData = Depends(get_current_user),
):
    try:
        data_users = await select_users_by_id(db, user_id=user_id, timestamp_data=timestamp_data)
        if not data_users:
            result = await show_not_found(http_request=http_request, status_code=404)
        else:
            result = await show_success(data=data_users, http_request=http_request, status_code=status.HTTP_200_OK)

        return JSONResponse(content=result, status_code=result['status']['code'])
    except Exception as e:
        logging.error(f"Exception single_list_users: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result['status']['code'])


# ROUTE CREATE DATA Users
@routerUsers.post("", response_model=UsersSingleSchema, responses=example_responses)
async def create_users(
    http_request: Request,
    request: UsersReqSchema,
    db: Session = Depends(get_db),
    identity: TokenData = Depends(get_current_user),
):
    """
        **Catatan:**

        `user_name`: text biasa, unik (wajib, 3-50 karakter) \n
        `password`: minimal 8 karakter. Wajib saat POST, opsional saat PUT/PATCH (diisi = ganti password) \n
        `user_karyawan`: angka, default 0 \n
        `user_supplier_id`: angka \n
        `user_groups`: angka \n
        `user_kode`: text biasa, unik, maks 2 karakter \n
        `user_keterangan`: text biasa \n
        `user_aktif`: ENUM pilihan `Aktif`/`Tidak Aktif`, default `Aktif` \n
        `user_cabang`: text biasa, default 1000...0 (70 karakter) \n
        `user_cabang_default`: angka \n
        `fcm_token`: text biasa \n
        `fcm_token_excelsa`: text biasa \n
        `user_aktif_2fa`: ENUM pilihan `Aktif`/`Tidak Aktif` \n
        `user_device_id`: text biasa \n

    """
    try:
        if request.user_name is not None:
            users_check = await check_users_user_name(db, user_name=request.user_name)
            if users_check:
                result = await show_bad_request(http_request=http_request, error=f"User Name {request.user_name} Sudah terdaftar sebelumnya", status_code=status.HTTP_400_BAD_REQUEST)
                return JSONResponse(content=result, status_code=result['status']['code'])
        if request.user_kode is not None:
            kode_check = await check_users_kode(db, user_kode=request.user_kode)
            if kode_check:
                result = await show_bad_request(http_request=http_request, error=f"User Kode {request.user_kode} Sudah terdaftar sebelumnya", status_code=status.HTTP_400_BAD_REQUEST)
                return JSONResponse(content=result, status_code=result['status']['code'])

        new_users = await create_data_users(db=db, users_data_create=request, identity=identity)
        if new_users:
            result = await show_success(data=new_users, http_request=http_request, code_message='createTrue', status_code=status.HTTP_201_CREATED)
        else:
            result = await show_success(http_request=http_request, code_message='createFalse', status_code=422)

        return JSONResponse(content=result, status_code=result['status']['code'])
    except Exception as e:
        logging.error(f"Exception create_users: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result['status']['code'])


# ROUTE UPDATE DATA Users
@routerUsers.put("/{user_id}", response_model=UsersSingleSchema, responses=example_responses)
async def update_users(
    http_request: Request,
    request: UsersPutSchema,
    user_id: int = Path(..., description="ID dari API GET `/sistem/users` (get_all_users) -> key `user_id` "),
    db: Session = Depends(get_db),
    identity: TokenData = Depends(get_current_user),
):
    """
        **Catatan:**

        `user_name`: text biasa, unik (wajib, 3-50 karakter) \n
        `password`: minimal 8 karakter. Wajib saat POST, opsional saat PUT/PATCH (diisi = ganti password) \n
        `user_karyawan`: angka, default 0 \n
        `user_supplier_id`: angka \n
        `user_groups`: angka \n
        `user_kode`: text biasa, unik, maks 2 karakter \n
        `user_keterangan`: text biasa \n
        `user_aktif`: ENUM pilihan `Aktif`/`Tidak Aktif`, default `Aktif` \n
        `user_cabang`: text biasa, default 1000...0 (70 karakter) \n
        `user_cabang_default`: angka \n
        `fcm_token`: text biasa \n
        `fcm_token_excelsa`: text biasa \n
        `user_aktif_2fa`: ENUM pilihan `Aktif`/`Tidak Aktif` \n
        `user_device_id`: text biasa \n

    """
    try:
        if request.user_name is not None:
            users_check = await check_users_user_name(db, user_name=request.user_name, exclude_user_id=user_id)
            if users_check:
                result = await show_bad_request(http_request=http_request, error=f"User Name {request.user_name} Sudah terdaftar sebelumnya", status_code=status.HTTP_400_BAD_REQUEST)
                return JSONResponse(content=result, status_code=result['status']['code'])
        if request.user_kode is not None:
            kode_check = await check_users_kode(db, user_kode=request.user_kode, exclude_user_id=user_id)
            if kode_check:
                result = await show_bad_request(http_request=http_request, error=f"User Kode {request.user_kode} Sudah terdaftar sebelumnya", status_code=status.HTTP_400_BAD_REQUEST)
                return JSONResponse(content=result, status_code=result['status']['code'])

        check_data_users = await check_users(db, user_id=user_id)
        if not check_data_users:
            result = await show_not_found(http_request=http_request, status_code=404)
        else:
            data_users = await update_data_users(db=db, user_id=user_id, users_data_update=request, identity=identity)
            result = await show_success(data=data_users, http_request=http_request, status_code=status.HTTP_200_OK)

        return JSONResponse(content=result, status_code=result['status']['code'])
    except Exception as e:
        logging.error(f"Exception update_users: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result['status']['code'])


# ROUTE UPDATE PATCH DATA Users
@routerUsers.patch("/{user_id}", response_model=UsersSingleSchema, responses=example_responses)
async def partial_update_users(
    http_request: Request,
    request: UsersPatchSchema,
    user_id: int = Path(..., description="ID dari API GET `/sistem/users` (get_all_users) -> key `user_id` "),
    db: Session = Depends(get_db),
    identity: TokenData = Depends(get_current_user),
):
    """
        **Catatan:**

        `user_name`: text biasa, unik (wajib, 3-50 karakter) \n
        `password`: minimal 8 karakter. Wajib saat POST, opsional saat PUT/PATCH (diisi = ganti password) \n
        `user_karyawan`: angka, default 0 \n
        `user_supplier_id`: angka \n
        `user_groups`: angka \n
        `user_kode`: text biasa, unik, maks 2 karakter \n
        `user_keterangan`: text biasa \n
        `user_aktif`: ENUM pilihan `Aktif`/`Tidak Aktif`, default `Aktif` \n
        `user_cabang`: text biasa, default 1000...0 (70 karakter) \n
        `user_cabang_default`: angka \n
        `fcm_token`: text biasa \n
        `fcm_token_excelsa`: text biasa \n
        `user_aktif_2fa`: ENUM pilihan `Aktif`/`Tidak Aktif` \n
        `user_device_id`: text biasa \n

    """
    try:
        if request.user_name is not None:
            users_check = await check_users_user_name(db, user_name=request.user_name, exclude_user_id=user_id)
            if users_check:
                result = await show_bad_request(http_request=http_request, error=f"User Name {request.user_name} Sudah terdaftar sebelumnya", status_code=status.HTTP_400_BAD_REQUEST)
                return JSONResponse(content=result, status_code=result['status']['code'])
        if request.user_kode is not None:
            kode_check = await check_users_kode(db, user_kode=request.user_kode, exclude_user_id=user_id)
            if kode_check:
                result = await show_bad_request(http_request=http_request, error=f"User Kode {request.user_kode} Sudah terdaftar sebelumnya", status_code=status.HTTP_400_BAD_REQUEST)
                return JSONResponse(content=result, status_code=result['status']['code'])

        check_data_users = await check_users(db, user_id=user_id)
        if not check_data_users:
            result = await show_not_found(http_request=http_request, status_code=404)
        else:
            data_users = await partial_update_data_users(db=db, user_id=user_id, users_data_update=request.model_dump(exclude_unset=True), identity=identity)
            result = await show_success(data=data_users, http_request=http_request, status_code=status.HTTP_200_OK)

        return JSONResponse(content=result, status_code=result['status']['code'])
    except Exception as e:
        logging.error(f"Exception update_patch_users: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result['status']['code'])


# ROUTE DELETE DATA Users
@routerUsers.delete("/{user_id}", response_model=UsersSingleSchema, responses=example_responses)
async def delete_users(
    http_request: Request,
    user_id: int = Path(..., description="ID dari API GET `/sistem/users` (get_all_users) -> key `user_id` "),
    db: Session = Depends(get_db),
    identity: TokenData = Depends(get_current_user),
):
    try:
        if identity.user_id == user_id:
            result = await show_bad_request(http_request=http_request, error="Tidak bisa menghapus akun sendiri", status_code=status.HTTP_400_BAD_REQUEST)
            return JSONResponse(content=result, status_code=result['status']['code'])

        check_data_users = await check_users(db, user_id=user_id)
        if not check_data_users:
            result = await show_not_found(http_request=http_request, status_code=404)
        else:
            deleted_data_users = await delete_data_users(db=db, user_id=user_id, identity=identity)
            result = await show_success(data=deleted_data_users, http_request=http_request, status_code=status.HTTP_200_OK)

        return JSONResponse(content=result, status_code=result['status']['code'])
    except Exception as e:
        logging.error(f"Exception delete_users: {e}")
        result = show_bad_response(error=str(e), http_request=http_request)
        return JSONResponse(content=result, status_code=result['status']['code'])

# END CODE ROUTE Users
