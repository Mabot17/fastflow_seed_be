"""
============================================= Start Noted fastflow_tools CLI ===================================
Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
1. Satu pintu masuk untuk semua alat bantu developer: `poetry run fastflow <perintah>`
2. Setiap perintah tinggal di file sendiri di fastflow_tools/, cli.py hanya mendefinisikan argumen & bantuan
3. Panduan lengkap: fastflow_tools/tools_readme.md
============================================= END Noted fastflow_tools CLI ===================================
"""
import argparse
import sys

FMT = argparse.RawDescriptionHelpFormatter

# ============================================= Teks bantuan =============================================
FASTFLOW_DESC = """\
Alat bantu developer FastFlow.

perintah:
  module new        generate modul standar 6 endpoint dari table + daftarkan routernya
  module register   daftarkan router modul yang sudah ada (registry, api_router, metadata)
  release           naikkan versi, tulis CHANGELOG, commit & buat tag

mulai cepat:
  poetry run fastflow module new master/voucher --dry-run    # lihat rencana
  poetry run fastflow module new master/voucher              # generate + register
"""
FASTFLOW_EPILOG = "bantuan per perintah : fastflow <perintah> --help\npanduan lengkap      : fastflow_tools/tools_readme.md"

MODULE_DESC = """\
Kelola modul di fastflow_api/core/modules.

aksi:
  new        generate model, schema, check, crud, router & json helper dari table,
             lalu daftarkan routernya (kecuali --no-register)
  register   daftarkan router yang sudah ada ke modules_registry, api_router & api_metadata
"""

NEW_DESC = """\
Generate modul standar 6 endpoint (list, single, create, put, patch, delete) dari
struktur table di database, lalu daftarkan routernya secara otomatis.

Struktur table dibaca dari INFORMATION_SCHEMA (HANYA BACA, database tidak diubah).
Jalankan dulu SQL pembuatan table-nya (fastflow_updatedb/) sebelum generate.
"""
NEW_EPILOG = """\
contoh:
  # 1 fitur per folder -> core/modules/master/voucher/, table `voucher`
  poetry run fastflow module new master/voucher

  # lihat rencana file & registrasi tanpa menulis apa pun
  poetry run fastflow module new master/voucher --dry-run

  # banyak fitur dalam 1 folder -> core/modules/master/kendaraan/, file kendaraan_gps_*
  poetry run fastflow module new master/kendaraan --fitur kendaraan_gps

  # generate saja, daftarkan router belakangan
  poetry run fastflow module new master/voucher --no-register
  poetry run fastflow module register master/voucher

catatan Git Bash:
  argumen yang diawali '/' (mis. --api-prefix /master) diubah Git Bash menjadi path Windows.
  Jalankan dengan MSYS_NO_PATHCONV=1 poetry run fastflow ...  atau gunakan PowerShell/CMD.

file yang dibuat (contoh master/voucher):
  fastflow_api/core/modules/master/voucher/{model,schema,crud,router}/voucher_*.py
  fastflow_api/core/modules/master/voucher/crud/voucher_check.py
  fastflow_api/core/shared/json_helpers/master/json_voucher.py

registrasi yang dilakukan:
  core/router/modules_registry/master_routers.py   import voucher_router
  core/router/api_router.py                         import + include_router(prefix="/master")
  core/router/api_metadata.py                       tag "Master - Voucher"
"""

REGISTER_DESC = """\
Daftarkan router modul yang sudah ada ke 3 tempat:
  core/router/modules_registry/<domain>_routers.py   import router
  core/router/api_router.py                          import + include_router
  core/router/api_metadata.py                        tag dokumentasi (TAGS_METADATA_API)

Nama variabel APIRouter dan tag dibaca langsung dari file router.
Aman dijalankan berulang: yang sudah terdaftar dilewati.
"""
REGISTER_EPILOG = """\
contoh:
  poetry run fastflow module register master/voucher
  poetry run fastflow module register master/voucher --dry-run
  poetry run fastflow module register master/kendaraan --fitur kendaraan_gps
  poetry run fastflow module register esb --fitur esb_promo --api-prefix ""      # tanpa prefix
"""

# ============================================= Parser =============================================
def _indonesia(p):
    """Label bawaan argparse -> Bahasa Indonesia, -h dengan teks sendiri."""
    p._positionals.title = "argumen"
    p._optionals.title = "opsi"
    p.add_argument("-h", "--help", action="help", help="tampilkan bantuan ini")
    return p


def _add_naming_args(group, with_tag=True):
    group.add_argument("--fitur", metavar="NAMA",
                       help="nama fitur = prefix file, fungsi & class. default: segmen terakhir module_path")
    group.add_argument("--api-prefix", metavar="PREFIX",
                       help='prefix saat include_router. default: /<domain> (contoh /master). "" = tanpa prefix')
    if with_tag:
        group.add_argument("--tag", metavar="TEKS",
                           help='tag dokumentasi. default: "<Domain> - <Fitur>", contoh "Master - Voucher"')


def build_parser():
    parser = _indonesia(argparse.ArgumentParser(prog="fastflow", usage="fastflow <perintah> [opsi]", description=FASTFLOW_DESC,
                                                epilog=FASTFLOW_EPILOG, formatter_class=FMT, add_help=False))
    sub = parser.add_subparsers(dest="command", metavar="<perintah>", help=argparse.SUPPRESS)

    # ---------- fastflow release ----------
    sub.add_parser("release", add_help=False)

    # ---------- fastflow module ----------
    module = _indonesia(sub.add_parser("module", usage="fastflow module <aksi> [opsi]", description=MODULE_DESC,
                                       epilog="bantuan per aksi: fastflow module <aksi> --help",
                                       formatter_class=FMT, add_help=False))
    module_sub = module.add_subparsers(dest="module_command", metavar="<aksi>", help=argparse.SUPPRESS)

    # ---------- fastflow module new ----------
    new = _indonesia(module_sub.add_parser("new", usage="fastflow module new <module_path> [opsi]",
                                           description=NEW_DESC, epilog=NEW_EPILOG, formatter_class=FMT,
                                           add_help=False))
    new.add_argument("module_path", help="folder di bawah core/modules, boleh bertingkat: master/voucher, master/kendaraan")
    g = new.add_argument_group("sumber struktur table")
    g.add_argument("--table", metavar="NAMA", help="nama table di database. default: sama dengan --fitur")
    g.add_argument("--env-key", metavar="VAR", default="DB_CONNECTION_URL",
                   help="variabel koneksi DB di fastflow_api/core/.env. default: DB_CONNECTION_URL")
    g.add_argument("--schema-file", metavar="FILE.json", help="baca struktur kolom dari file JSON (offline/tes)")
    g = new.add_argument_group("penamaan & endpoint")
    _add_naming_args(g)
    g.add_argument("--unique", metavar="KOLOM", default="auto",
                   help="kolom cek duplikat saat create/put/patch. default: auto (<fitur>_kode lalu <fitur>_nama). "
                        "none = tanpa cek")
    g = new.add_argument_group("registrasi router")
    g.add_argument("--no-register", action="store_true",
                   help="jangan daftarkan router (daftarkan manual nanti dengan `fastflow module register`)")
    g.add_argument("--description", metavar="TEKS", help="deskripsi tag di api_metadata.py")
    g = new.add_argument_group("eksekusi")
    g.add_argument("--dry-run", action="store_true", help="tampilkan rencana file & registrasi tanpa menulis apa pun")
    g.add_argument("--force", action="store_true",
                   help="timpa file yang sudah ada & lewati cek 'table sudah punya model'")

    # ---------- fastflow module register ----------
    reg = _indonesia(module_sub.add_parser("register", usage="fastflow module register <module_path> [opsi]",
                                           description=REGISTER_DESC, epilog=REGISTER_EPILOG, formatter_class=FMT,
                                           add_help=False))
    reg.add_argument("module_path", help="folder modul di bawah core/modules, contoh: master/voucher")
    g = reg.add_argument_group("penamaan & endpoint")
    _add_naming_args(g, with_tag=False)
    g.add_argument("--description", metavar="TEKS", help="deskripsi tag di api_metadata.py")
    g = reg.add_argument_group("eksekusi")
    g.add_argument("--dry-run", action="store_true", help="tampilkan rencana tanpa menulis apa pun")

    return parser, module


def _run_release(rest):
    from fastflow_tools import release

    # release.main() membaca argumennya sendiri dari sys.argv
    sys.argv = ["fastflow release", *rest]
    release.main()


def main():
    parser, module_parser = build_parser()
    args, rest = parser.parse_known_args()

    if args.command == "release":
        _run_release(rest)
        return

    if rest:
        parser.error(f"argumen tidak dikenal: {' '.join(rest)}")

    if args.command == "module":
        if args.module_command == "new":
            from fastflow_tools import module_generator
            module_generator.main(args)
        elif args.module_command == "register":
            from fastflow_tools import module_registry
            module_registry.main(args)
        else:
            module_parser.print_help()
            sys.exit(1)
        return

    parser.print_help()
    sys.exit(0 if args.command is None else 1)


if __name__ == "__main__":
    main()
