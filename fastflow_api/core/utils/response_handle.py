# ============================================= Start Noted Response Handler ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Class ini digunakan untuk menghandle semua hasil response yang dikirim ke user. contoh fungsi
# - show_success_list() (list + paging)
# - show_success()
# - show_not_found()
# - show_bad_response()
# ============================================= END Noted Response Handler ===================================
from fastapi import Request
from typing import Dict, List, Optional, Union
from core.utils.common import total_pages
import json

# Nilai field ini disamarkan di blok `request` respons (tidak pernah mengembalikan password/token ke client)
SENSITIVE_KEYS = ("password", "passwd", "token", "secret", "otp")
MASK = "***"


def mask_sensitive(data):
    if isinstance(data, dict):
        return {k: (MASK if any(s in str(k).lower() for s in SENSITIVE_KEYS) else mask_sensitive(v)) for k, v in data.items()}
    if isinstance(data, list):
        return [mask_sensitive(v) for v in data]
    return data

msgSuccesDefault = 'Request Berhasil.'
msgBadRequest = 'Request Gagal Dilakukan.'
msgFailedDefault = 'Terjadi Kesalahan Server, Silahkan hubungi Administrator.'
msgSuccessList = 'Data Berhasil Ditampilkan.'
msgFailedList = 'Data Tidak Ditemukan.'
msgSuccessCreate = 'Data Berhasil Ditambahkan.'
msgFailedCreate = 'Data Gagal Ditambahkan.'
msgSuccessUpdate = 'Data Berhasil Diubah.'
msgFailedUpdate = 'Data Gagal Diubah.'
msgSuccessDelete = 'Data Berhasil Dihapus.'
msgFailedDelete = 'Data Gagal Dihapus.'
msgLoginFailedToken = "API Belum Terautentikasi."
msgLoginFailedUser = "User Anda belum terdaftar di sistem, mohon hubungi pihak admin."
msgLoginFailedPassword = 'Username atau Password yang Anda masukkan salah.'
msgValidationFailed = "Request Tidak Valid, Mohon isi data sesuai yang dibutuhkan."
msgErrorEnv = 'Enviorenment Tidak Valid, Mohon cek file .env '
msgErrorMethodApi = "Metode API Tidak diizinkan, Silahkan cek kembali."

def handle_message(code_message):
    messages = {
        'defaultTrue': msgSuccesDefault,
        'defaultFalse': msgFailedDefault,
        'listTrue': msgSuccessList,
        'listFalse': msgFailedList,
        'createTrue': msgSuccessCreate,
        'createFalse': msgFailedCreate,
        'updateTrue': msgSuccessUpdate,
        'updateFalse': msgFailedUpdate,
        'deleteTrue': msgSuccessDelete,
        'deleteFalse': msgFailedDelete,
        'loginFalseToken': msgLoginFailedToken,
        'loginFalseUser': msgLoginFailedUser,
        'loginFalsePassword': msgLoginFailedPassword,
        'validationFalse': msgValidationFailed,
        'errEnv': msgErrorEnv,
        'errMethode': msgErrorMethodApi,
        'badRequest': msgBadRequest,
    }
    return messages.get(code_message, msgFailedDefault)

async def generate_request_data(http_request: Request) -> Dict[str, Union[str, Dict[str, Union[str, str]]]]:
    # Periksa jenis konten request untuk menentukan cara mengambil data
    content_type = http_request.headers.get("Content-Type", "")
    
    # Persiapkan dictionary untuk menyimpan informasi awal
    data_request = {
        "url": str(http_request.url),
        "method": str(http_request.method),
        "parameters": dict(http_request.query_params),
        "body": {},
    }

    try:
        # Baca hanya jika JSON, karena .body() hanya bisa dipanggil sekali
        if "application/json" in content_type:
            # Baca body mentah terlebih dahulu untuk menghindari error saat JSON kosong
            body_bytes = await http_request.body()

            if body_bytes:
                try:
                    # Jika kontennya JSON dan tidak kosong, parse payload JSON
                    json_data = json.loads(body_bytes)
                    data_request["body"] = json_data
                except json.JSONDecodeError:
                    data_request["body"] = {"error": "Invalid JSON format"}
        else:
            # Jika kontennya bukan JSON, gunakan http_request.form() untuk formulir multipart
            form_data = await http_request.form()


            # Persiapkan dictionary untuk menyimpan informasi file dan nilai lainnya
            for key, value in form_data.items():
                try:
                    # Periksa tipe nilai, apakah itu file atau data biasa
                    if hasattr(value, "filename") and value.filename:
                        # Jika ada filename, itu berarti ini adalah file
                        # Anda dapat menangani file sesuai kebutuhan, misalnya, menyimpannya ke sistem file atau menyimpan di database
                        data_request['body'][key] = {
                            "filename": value.filename
                        }
                    else:
                        # Jika tidak ada filename, itu adalah data biasa
                        data_request['body'][key] = value.decode()
                except AttributeError:
                    # Penanganan jika value tidak memiliki atribut filename (bukan file)
                    # Misalnya, jika value adalah int atau str
                    data_request['body'][key] = str(value)

    except RuntimeError as e:
        # Jika stream sudah dikonsumsi, tampilkan error khusus
        data_request["body"] = {"error": f"Cannot read body again: {str(e)}"}

    return mask_sensitive(data_request)

def generate_response_paging(total_data=0, page=1, results_per_page=20):
    total_pages_value = total_pages(total_data, results_per_page)
    response = {
        'page': page,
        'total_pages': total_pages_value,
        'records_per_page': results_per_page,
        'total_records': total_data
    }
    return response

async def show_success_list(
    http_request: Request = None,
    data: Optional[List] = None,
    total_data: int = 0,
    page: int = 1,
    results_per_page: int = 20,
    is_paging: bool = False,
    status_code: int = 200,
    error: str = None,
    message: str = None,
    **kwargs  # Menggunakan **kwargs untuk parameter tambahan
):
    code_message = 'listTrue' if data else 'listFalse'
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data
    }

    if is_paging:
        response['paging'] = generate_response_paging(total_data, page, results_per_page)

    response['error'] = error
    response['request'] = await generate_request_data(http_request=http_request)

    if kwargs:
        response['data_information'] = kwargs  # Menambahkan data_information dengan kwargs

    return response


async def show_success(http_request: Request = None, data: Optional[dict] = None, code_message: str = 'defaultTrue', status_code: int = 200, error: str=None, message: str = None):
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data,
        'error': error
    }

    if http_request:
        response['request'] = await generate_request_data(http_request=http_request)

    return response

def show_unauthorized(http_request: Request = None, data: Optional[dict] = None, code_message: str = 'loginFalseToken', status_code: int = 401, error: str=None, message: str = None):
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data,
        'error': error
    }
    return response

def show_method_not_allowed(http_request: Request = None, data: Optional[dict] = None, code_message: str = 'errMethode', status_code: int = 405, error: str=None, message: str = None):
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data,
        'error': error
    }
    return response

async def show_not_found(http_request: Request = None, data: Optional[dict] = None, code_message: str = 'listFalse', status_code: int = 404, error: str=None, message: str = None):
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data,
        'error': error
    }
    # Tambahkan request ke blok JSON response jika request tidak None
    if http_request:
        response['request'] = await generate_request_data(http_request=http_request)

    return response

def show_validation_response(http_request: Request = None, data: Optional[dict] = None, code_message: str = 'validationFalse', status_code: int = 422, error: Optional[dict] = None, message: str = None):
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data,
        'error': error,
        # 'request': await generate_request_data(http_request=http_request),
    }
    return response

def show_bad_response(http_request: Request = None, data: Optional[dict] = None, code_message: str = 'defaultFalse', status_code: int = 500, error: Optional[dict] = None, message: str = None):
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data,
        'error': error
    }

    # Tambahkan request ke blok JSON response jika request tidak None
    # if http_request:
        # response['request'] = await generate_request_data(http_request=http_request)

    return response

async def show_forbidden_response(http_request: Request = None, data: Optional[dict] = None, code_message: str = 'loginFalsePassword', status_code: int = 403, error: Optional[dict] = None, message: str = None):
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data,
        'error': error
    }

    # Tambahkan request ke blok JSON response jika request tidak None
    # if http_request:
        # response['request'] = await generate_request_data(http_request=http_request)

    return response

async def show_bad_request(http_request: Request = None, data: Optional[dict] = None, code_message: str = 'badRequest', status_code: int = 400, error: Optional[dict] = None, message: str = None):
    if message:
        message = message
    else:
        message = handle_message(code_message)

    response = {
        'status': {
            'code': status_code,
            'message': message
        },
        'data': data,
        'error': error
    }

    # Tambahkan request ke blok JSON response jika request tidak None
    if http_request:
        response['request'] = await generate_request_data(http_request=http_request)

    return response

def get_example_responses(status_codes: Optional[List[int]] = None) -> Dict[int, dict]:
    example_responses = {
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": show_bad_response(status_code=400, error="Bad Request", message="Kesalahan pada request, periksa kembali format request yang dikirimkan")
                }
            }
        },
        401: {
            "description": "Error: Unauthorized",
            "content": {
                "application/json": {
                    "example": show_unauthorized(status_code=401, error="Token tidak valid. Silahkan login kembali.")
                }
            }
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "example": {
                        "status": {
                            "code": 404,
                            "message": "Data Tidak Ditemukan."
                        },
                        "data": "null",
                        "error": "Data NamaModul Tidak Ditemukan",
                        "request": {
                            "url": "http://127.0.0.1:8001/nama_api",
                            "method": "method yang dikirim misal `GET`, `POST`, `POST`, `PUT`, `DELETE` ",
                            "parameters": {},
                            "body": {}
                        }
                    }
                }
            }
        },
        405: {
            "description": "Method Not Allowed",
            "content": {
                "application/json": {
                    "example": show_method_not_allowed(status_code=405, error="Metode Anda: (yang dikirimkan) tidak diizinkan. Seharusnya menggunakan: (yang diizinkan)")
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": show_validation_response(status_code=422, error=[{"loc": ["body", "param_name"], "msg": "error message", "type": "type"}])
                }
            }
        },
        500: {
            "description": "Bad Response",
            "content": {
                "application/json": {
                    "example": show_bad_response(status_code=500, error="Internal Server Error")
                }
            }
        },
        # Tambahkan respons lain jika diperlukan
    }

    if status_codes:
        # Filter respons berdasarkan status code yang diberikan
        filtered_responses = {code: example_responses.get(code, {}) for code in status_codes}
        return filtered_responses

    return example_responses