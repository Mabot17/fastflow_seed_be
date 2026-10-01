# fastflow_tools — Alat Bantu Developer

Alat untuk tim developer. **Bukan** bagian dari aplikasi yang di-deploy.
Semua perintah dijalankan dari root repo lewat satu pintu masuk:

```bash
poetry run fastflow --help
```

> Setelah `git pull` yang mengubah `pyproject.toml`, jalankan `poetry install` sekali
> supaya perintah `fastflow` terdaftar.

> **Pengguna Git Bash:** argumen yang diawali `/` (mis. `--api-prefix /master`) diubah Git Bash menjadi
> path Windows (`C:/Program Files/Git/master`). Generator akan menolaknya dengan pesan error.
> Jalankan dengan `MSYS_NO_PATHCONV=1 poetry run fastflow ...` atau gunakan PowerShell/CMD.

## Ringkasan perintah

| Perintah | Fungsi |
|---|---|
| `fastflow module new <path>` | Generate modul standar 6 endpoint dari table **+ daftarkan routernya** |
| `fastflow module register <path>` | Daftarkan router modul yang sudah ada (manual) |
| `fastflow release` | Naikkan versi, tulis CHANGELOG, commit & buat tag |

Bantuan lengkap tiap perintah: `poetry run fastflow <perintah> --help`, misal `poetry run fastflow module new --help`.

---

## Alur membuat modul baru

Contoh: master voucher.

1. **Buat table** lewat SQL di `fastflow_updatedb/` lalu jalankan di database (seperti biasa).
2. **Cek rencana** (tidak menulis apa pun):
   ```bash
   poetry run fastflow module new master/voucher --dry-run
   ```
3. **Generate + register**:
   ```bash
   poetry run fastflow module new master/voucher
   ```
4. **Jalankan aplikasi**, buka `/docs`, cek tag `Master - Voucher`.
5. **Lengkapi** deskripsi tag di `core/router/api_metadata.py` dan logika bisnis di crud/router bila perlu.

Hasil langkah 3:

```
fastflow_api/core/modules/master/voucher/
├── model/voucher_model.py       ← kolom dibaca dari table
├── schema/voucher_schema.py     ← BaseData, List, Single, RequestList, Req, Put, Patch
├── crud/voucher_check.py        ← check_voucher (+ cek duplikat)
├── crud/voucher_crud.py         ← list, by id, create, update, partial update, delete
└── router/voucher_router.py     ← 6 endpoint
fastflow_api/core/shared/json_helpers/master/json_voucher.py

+ registrasi:
core/router/modules_registry/master_routers.py   from core.modules.master.voucher.router import voucher_router
core/router/api_router.py                         import + include_router(voucher_router.routerVoucher, prefix="/master")
core/router/api_metadata.py                       tag "Master - Voucher"
```

Endpoint yang tersedia: `GET /master/voucher`, `GET /master/voucher/{voucher_id}`, `POST /master/voucher`,
`PUT /master/voucher/{voucher_id}`, `PATCH /master/voucher/{voucher_id}`, `DELETE /master/voucher/{voucher_id}`.

---

## `fastflow module new`

Generate modul standar dari struktur table. Struktur dibaca dari `INFORMATION_SCHEMA`
(**hanya baca**, database tidak diubah). Setelah file dibuat, router langsung didaftarkan
(sama seperti `fastflow module register`), kecuali memakai `--no-register`.

```bash
poetry run fastflow module new master/voucher                          # 1 fitur per folder
poetry run fastflow module new master/kendaraan --fitur kendaraan_gps  # banyak fitur dalam 1 folder
poetry run fastflow module new master/voucher --dry-run                # rencana saja
poetry run fastflow module new master/voucher --no-register            # generate tanpa register
poetry run fastflow module new master/voucher --schema-file voucher.json        # struktur dari file JSON (tanpa DB)
```

| Opsi | Default | Keterangan |
|---|---|---|
| `module_path` | (wajib) | Folder di bawah `core/modules`, boleh bertingkat: `master/voucher`, `master/kendaraan` |
| `--fitur` | segmen terakhir `module_path` | Prefix nama file, fungsi & class (`voucher` → `voucher_router.py`, `VoucherModel`) |
| `--table` | sama dengan `--fitur` | Nama table di database |
| `--env-key` | `DB_CONNECTION_URL` | Variabel koneksi database di `fastflow_api/core/.env` |
| `--schema-file` | - | Baca struktur kolom dari file JSON (offline/tes), bukan dari database |
| `--unique` | `auto` | Kolom cek duplikat saat create/put/patch. `auto` = `<fitur>_kode` lalu `<fitur>_nama`; `none` = tanpa cek |
| `--tag` | `<Domain> - <Fitur>` | Tag dokumentasi |
| `--api-prefix` | `/<domain>` | Prefix `include_router`. `""` = tanpa prefix |
| `--no-register` | - | Jangan daftarkan router |
| `--description` | otomatis | Deskripsi tag di `api_metadata.py` |
| `--dry-run` | - | Tampilkan rencana file & registrasi tanpa menulis apa pun |
| `--force` | - | Timpa file yang sudah ada & lewati cek "table sudah punya model" |

**Dibaca otomatis dari table:**

- Primary key (wajib tepat 1, composite key belum didukung).
- Tipe kolom → tipe model & schema: `varchar`, `text`, `int`, `decimal`, `float`, `double`, `date`, `datetime`, `time`, `enum`, `json`.
- Kolom `NOT NULL` tanpa default → field wajib di POST/PUT.
- `enum(...)` → `Literal[...]`; kolom `<fitur>_aktif` bertipe enum → filter status di list.
- Ada `deleted_at`/`deleted_by` → soft delete; tidak ada → hapus permanen.
- `created_*`, `updated_*`, `<table>_revised` → diisi otomatis saat create/update.
  Kolom audit berprefix juga dikenali, mis. `user_created_at` → atribut model `created_at`.
- Kolom sensitif (nama mengandung `passwd`, `password`, `token`, `secret`, `otp`) **tidak** dijadikan input,
  pencarian, maupun JSON respons. Generator mencetak peringatan; tambahkan manual bila memang perlu
  (contoh: modul `users` meng-hash `password` ke `user_passwd_sha`).
- Identitas user di modul baru memakai `TokenData` (`core.utils.token`), jadi modul baru tidak bergantung
  pada modul `users`.

**Dibatalkan dengan `[ERROR]` bila:**

- Table sudah punya model di `core/` (dua model untuk 1 table membuat aplikasi gagal start).
- File tujuan sudah ada (kecuali `--force`).
- Nama folder/fitur tidak valid (huruf kecil, angka, underscore, diawali huruf).
- Table tidak ditemukan, tidak punya tepat 1 primary key, atau `--unique` bukan kolom table.

Aturan & variabel template: `fastflow_tools/modules_template/modules_template_readme.md`.

---

## `fastflow module register`

Daftarkan router modul yang **sudah ada** ke 3 tempat. Dipakai setelah `--no-register`,
atau untuk router yang ditulis tangan.

```bash
poetry run fastflow module register master/voucher
poetry run fastflow module register master/voucher --dry-run
poetry run fastflow module register master/kendaraan --fitur kendaraan_gps
poetry run fastflow module register esb --fitur esb_promo --api-prefix ""     # tanpa prefix
```

| Yang ditambahkan | Lokasi |
|---|---|
| `from core.modules.<path>.router import <fitur>_router` | `core/router/modules_registry/<domain>_routers.py` (dibuat bila domain baru) |
| import `<fitur>_router` + `apiSettings.include_router(...)` | `core/router/api_router.py` (di bawah router lain dengan prefix yang sama) |
| `{"name": "<tag>", "description": ...}` | `core/router/api_metadata.py` (di bawah tag lain dengan domain yang sama) |

- Nama variabel `APIRouter` dan tag dibaca langsung dari file router.
- Aman dijalankan berulang: yang sudah terdaftar ditandai `[LEWATI]`, tidak dobel.
- File python yang disunting selalu divalidasi dulu, tidak pernah menulis kode yang rusak.

| Opsi | Default | Keterangan |
|---|---|---|
| `module_path` | (wajib) | Folder modul di bawah `core/modules` |
| `--fitur` | segmen terakhir `module_path` | Nama file router: `<fitur>_router.py` |
| `--api-prefix` | `/<domain>` | Prefix `include_router`. `""` = tanpa prefix |
| `--description` | otomatis | Deskripsi tag baru di `api_metadata.py` |
| `--dry-run` | - | Tampilkan rencana tanpa menulis apa pun |

Aturan routing & penempatan router: `fastflow_api/core/router/router_readme.md`.

---

## `fastflow release`

Naikkan versi API (`pyproject.toml` + `api_metadata.py`), tambah section `CHANGELOG.md`,
commit, lalu buat tag `vX.Y.Z`. Tidak melakukan push. Working tree harus bersih
(file baru yang belum di-track diabaikan).

```bash
poetry run fastflow release --dry-run        # preview tanpa mengubah apa pun
poetry run fastflow release                  # bump patch otomatis (0.0.98 -> 0.0.99)
poetry run fastflow release --version 0.1    # target custom -> 0.1.0
```

Alias lama tetap jalan: `poetry run release ...`.

---

## Test

```bash
poetry run pytest            # semua test (SQLite in-memory, tidak menyentuh MySQL)
poetry run pytest -k users   # test tertentu
```

`tests/test_kerangka.py` juga menjaga aturan arsitektur: kerangka tidak meng-import modul,
`__init__.py` modul kosong, dan setiap `JSONResponse` memakai `status_code`.

---

## Isi folder

| File | Fungsi |
|---|---|
| `cli.py` | Pintu masuk `fastflow`: definisi perintah, opsi & teks bantuan |
| `module_generator.py` | `fastflow module new`: baca struktur table, render template, tulis file |
| `module_registry.py` | `fastflow module register`: sunting registry, api_router & api_metadata |
| `modules_template/` | Template Jinja2 modul standar + `modules_template_readme.md` |
| `release.py` | `fastflow release` |

## Menambah perintah baru

1. Buat file perintah di `fastflow_tools/` dengan fungsi `main(args)`.
2. Daftarkan subcommand, opsi & teks bantuannya di `cli.py`.
3. Dokumentasikan di file ini (ringkasan perintah + bagian sendiri).
