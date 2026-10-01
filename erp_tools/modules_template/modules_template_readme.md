# modules_template — Template Modul Standar

Template Jinja2 untuk `erp module new`. Satu modul standar = 6 endpoint:
**list, single, create (POST), update (PUT), partial update (PATCH), delete**.

## File yang dihasilkan

| Template | Hasil |
|---|---|
| `model.py.jinja` | `core/modules/<module_path>/model/<fitur>_model.py` |
| `schema.py.jinja` | `core/modules/<module_path>/schema/<fitur>_schema.py` |
| `check.py.jinja` | `core/modules/<module_path>/crud/<fitur>_check.py` |
| `crud.py.jinja` | `core/modules/<module_path>/crud/<fitur>_crud.py` |
| `router.py.jinja` | `core/modules/<module_path>/router/<fitur>_router.py` |
| `json.py.jinja` | `core/shared/json_helpers/<domain>/json_<fitur>.py` |

`<module_path>` boleh bertingkat, misal `master/meja` (1 fitur per folder) atau
`master/kendaraan` dengan fitur `kendaraan_gps` (banyak fitur dalam 1 folder).

## Aturan yang sudah tertanam di template

- `JSONResponse` selalu `status_code=result['status']['code']` (HTTP status = body status).
- Semua endpoint memakai `get_current_user` (wajib token); identitas bertipe `TokenData` (`core.utils.token`),
  sehingga modul baru tidak bergantung pada modul `users`.
- Kolom sensitif (`*passwd*`, `*password*`, `*token*`, `*secret*`, `*otp*`) tidak dijadikan input/pencarian/JSON.
- Fungsi check di file sendiri (`<fitur>_check.py`) yang hanya meng-import model,
  bukan di `check_data_model.py` dan bukan di `*_crud.py` (mencegah circular import).
- Import di atas file, tanpa import lokal. Tanpa `print()`.
- Error di crud selalu `db.rollback()` lalu `return None` (tidak pernah mengembalikan objek exception).
- Delete: soft delete bila table punya `deleted_at`, hapus permanen bila tidak.
- JSON: kolom `date`/`datetime` lewat `json_format_date`, `Decimal` lewat `float()` (siap diserialisasi).

## Variabel template (kontrak dengan generator)

| Variabel | Contoh | Keterangan |
|---|---|---|
| `module_path` | `master.meja` | Path paket di bawah `core.modules` (titik) |
| `domain` | `master` | Segmen pertama module_path, untuk folder json_helpers & registry |
| `fitur` | `meja` | Nama fitur (snake_case), prefix nama file & fungsi |
| `Fitur` | `Meja` | PascalCase, prefix nama class |
| `fitur_camel` | `meja` | camelCase, alias query di crud |
| `fitur_title` | `Meja` | Judul untuk komentar & dokumentasi |
| `table` | `meja` | Nama table di database |
| `pk` / `pk_path` | `meja_id` / `/{meja_id}` | Primary key & path parameter |
| `api_prefix` / `url_prefix` | `/master` / `/meja` | Prefix di api_router & prefix APIRouter |
| `tag` | `Master - Meja` | Tag dokumentasi (harus sama dengan `TAGS_METADATA_API`) |
| `columns` | semua kolom | `name`, `attr`, `sa_type`, `is_pk` |
| `data_columns` | kolom selain pk & audit | `name`, `attr`, `py` (`str`/`int`/`Decimal`/`date`/`datetime`/...), `annotation`, `optional_annotation`, `default_repr`, `doc` |
| `sa_imports` | `["String", "Integer", "DateTime"]` | Tipe SQLAlchemy yang dipakai model |
| `needs_datetime` / `needs_decimal` | `False` | Import tambahan di schema |
| `search_columns` | `["meja_nama", "meja_keterangan"]` | Kolom teks untuk pencarian `keywords` |
| `aktif_column` | `meja_aktif` atau `None` | Filter status di list (`name`, `literal_values`, `has_tidak_aktif`) |
| `unique_column` / `unique_suffix` / `unique_title` | `meja_nama` / `nama` / `Meja Nama` | Cek duplikat saat create/update, atau `None` |
| `has_deleted_at` / `has_deleted_by` | `True` | Soft delete |
| `has_created` / `has_updated` / `has_revised` | `True` | Kolom audit |

Kolom audit yang dikenali (juga versi berprefix, mis. `user_created_at` → `created_at`):
`created_by`, `created_at`, `updated_by`, `updated_at`,
`deleted_by`, `deleted_at`, dan `<table>_revised` / `revised` (atribut model: `revised`).
