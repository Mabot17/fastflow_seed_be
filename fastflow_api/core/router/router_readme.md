# core/router — Pengontrol Pendaftaran API

Folder ini adalah **satu-satunya tempat** semua endpoint REST didaftarkan ke FastAPI.
Modul di `core/modules/` hanya berisi kode domain (model, schema, crud, router per fitur);
keputusan *router mana yang aktif, dengan prefix apa, dan dalam kondisi apa* diatur di sini.

## Isi folder

| File / folder | Fungsi |
|---|---|
| `api_router.py` | Import router dari `modules_registry/` lalu `include_router()` dengan prefix-nya. Di-import oleh `main.py`. |
| `modules_registry/<modul>_routers.py` | Daftar router per modul (`auth_routers.py`, `users_routers.py`, ...). **Hanya** di-import oleh `api_router.py`. |
| `api_metadata.py` | Judul, versi, deskripsi API dan `TAGS_METADATA_API` (urutan & deskripsi tag di `/docs`). |
| `api_docs.py` | Halaman `/docs`, `/redoc`, `/rapidoc`, `/version`, `/version/changelog`. |
| `api_middleware.py` | Format respons standar untuk 401/405/422 dan `MaintenanceException` (503). |
| `api_log_middleware.py` | Log setiap request (IP, user dari JWT, durasi) dan blokir path mencurigakan (403). |

## Alur request

```
main.py  (app = Socket.IO yang membungkus fastapi_app)
 └─ FastAPI
     ├─ CORSMiddleware
     ├─ api_middleware_response   → ubah 401/405 ke format standar
     ├─ LoggingMiddleware          → log + blokir path mencurigakan
     └─ api_router.apiSettings
         └─ core/modules/<modul>/<fitur>/router/<fitur>_router.py
             └─ crud → (check, json_helpers) → model → database
```

## Menambah router

Cara utama (otomatis, lihat `fastflow_tools/tools_readme.md`):

```bash
poetry run fastflow module new master/voucher          # generate modul + daftarkan router
poetry run fastflow module register master/voucher     # hanya daftarkan router yang sudah ada
```

Cara manual (hasilnya sama):

1. `modules_registry/master_routers.py` → `from core.modules.master.voucher.router import voucher_router`
2. `api_router.py` → import `voucher_router` dari `master_routers`, lalu
   `apiSettings.include_router(voucher_router.routerVoucher, prefix="/master")`
3. `api_metadata.py` → tambahkan tag yang **namanya sama persis** dengan `tags=[...]` di router.

## Aturan (penting)

- **`__init__.py` di `core/modules/**` harus kosong.** `__init__.py` ikut dijalankan setiap kali *apa pun*
  di bawah paket tsb di-import (termasuk model), sehingga router di sana memicu circular import.
- **Kerangka tidak boleh meng-import `core.modules.*`.** Yang boleh: `api_router.py`, `modules_registry/`,
  dan json helper modul (`shared/json_helpers/<domain>/`). Dijaga oleh `tests/test_kerangka.py`.
- Arah import satu jalur: `router → crud → (check, json_helpers) → model`.
- Fungsi pengecekan data ditaruh di `crud/<fitur>_check.py` yang hanya meng-import model.
- Identitas user di router: `identity: TokenData = Depends(get_current_user)` (`core.utils.token`).

## Respons & status code

- Setiap `JSONResponse` wajib `status_code=result['status']['code']` (HTTP status = body status).
  Dijaga oleh `tests/test_kerangka.py`.
- **HTTP 401 hanya untuk token tidak valid.** `api_middleware_response` mengubah semua 401 menjadi
  "Token tidak valid. Silahkan login kembali." Untuk password salah / user tidak aktif pakai 403.
- Blok `request` di respons berisi salinan request; field bernama `password`, `token`, `secret`, `otp`
  otomatis disamarkan (`***`).

## Maintenance per router

Matikan method tertentu sementara (respons 503) tanpa mengubah kode modul:

```python
apiSettings.include_router(
    users_router.routerUsers,
    prefix="/sistem",
    dependencies=[maintenance_guard({"POST", "PUT", "PATCH", "DELETE"})],
)
```
