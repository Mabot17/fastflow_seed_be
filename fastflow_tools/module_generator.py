"""
============================================= Start Noted module_generator ===================================
Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
1. `fastflow module new` -> generate modul standar (6 endpoint) dari struktur table di database
2. Struktur table dibaca dari INFORMATION_SCHEMA (HANYA BACA, tidak ada perubahan ke database)
3. Template ada di fastflow_tools/modules_template/, aturan & variabelnya di modules_template_readme.md
4. Tidak pernah menimpa file yang sudah ada kecuali memakai --force
============================================= END Noted module_generator ===================================
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "fastflow_api"
TEMPLATE_DIR = Path(__file__).resolve().parent / "modules_template"
ENV_FILE = API_DIR / "core" / ".env"

AUDIT_COLUMNS = {"created_by", "created_at", "updated_by", "updated_at", "deleted_by", "deleted_at"}


def audit_attr(column_name):
    """Nama atribut model untuk kolom audit. Mendukung kolom berprefix: user_created_at -> created_at."""
    if column_name in AUDIT_COLUMNS:
        return column_name
    for audit in AUDIT_COLUMNS:
        if column_name.endswith("_" + audit):
            return audit
    if column_name == "revised" or column_name.endswith("_revised"):
        return "revised"
    return None
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# Kolom dengan nama ini tidak dijadikan input API, pencarian, maupun JSON respons (isi manual bila perlu)
SENSITIVE_PARTS = ("passwd", "password", "token", "secret", "otp")


API_PREFIX_RE = re.compile(r"^(/[A-Za-z0-9_\-/]*)?$")


def validate_api_prefix(api_prefix):
    """Tolak prefix yang bukan path URL (mis. diubah Git Bash menjadi C:/Program Files/Git/...)."""
    if api_prefix is not None and not API_PREFIX_RE.match(api_prefix):
        raise GeneratorError(
            f"--api-prefix `{api_prefix}` bukan path URL yang valid (contoh: /master).\n"
            "        Di Git Bash, argumen yang diawali '/' diubah menjadi path Windows. Jalankan dengan\n"
            "        MSYS_NO_PATHCONV=1 poetry run fastflow ...   atau dari PowerShell/CMD."
        )

# MySQL DATA_TYPE -> (tipe SQLAlchemy, tipe python di schema)
INT_TYPES = {"int": "Integer", "integer": "Integer", "mediumint": "Integer", "smallint": "SmallInteger",
             "tinyint": "SmallInteger", "bigint": "BigInteger", "year": "Integer"}
TEXT_TYPES = {"text", "tinytext", "mediumtext", "longtext"}

DOC_BY_TYPE = {
    "str": "text biasa", "int": "angka", "float": "angka desimal", "Decimal": "angka desimal",
    "date": "tanggal (YYYY-MM-DD)", "datetime": "tanggal & jam (YYYY-MM-DD HH:MM:SS)",
    "time": "jam (HH:MM:SS)", "dict": "objek JSON",
}


class GeneratorError(Exception):
    pass


# ============================================= Naming =============================================
def pascal(s):
    return "".join(w.capitalize() for w in s.split("_"))


def camel(s):
    p = pascal(s)
    return p[0].lower() + p[1:]


def title(s):
    return " ".join(w.capitalize() for w in s.split("_"))


# ============================================= Baca struktur table =============================================
def read_columns_from_db(table, env_key):
    """Baca kolom table dari INFORMATION_SCHEMA (read-only)."""
    from dotenv import dotenv_values
    from sqlalchemy import create_engine, text

    if not ENV_FILE.exists():
        raise GeneratorError(f"File .env tidak ditemukan: {ENV_FILE}")
    url = dotenv_values(ENV_FILE).get(env_key)
    if not url:
        raise GeneratorError(f"{env_key} tidak ada di {ENV_FILE}")

    engine = create_engine(url, pool_pre_ping=True)
    sql = text("""
        SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY,
               CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, EXTRA
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table
        ORDER BY ORDINAL_POSITION
    """)
    try:
        with engine.connect() as conn:
            rows = [dict(r._mapping) for r in conn.execute(sql, {"table": table})]
    finally:
        engine.dispose()
    if not rows:
        raise GeneratorError(f"Table `{table}` tidak ditemukan di database ({env_key}). "
                             "Pastikan SQL di fastflow_updatedb/ sudah dijalankan.")
    return rows


def read_columns_from_file(path):
    """Baca struktur kolom dari file JSON (format sama dgn baris INFORMATION_SCHEMA), untuk offline/tes."""
    if not Path(path).is_file():
        raise GeneratorError(f"file schema tidak ditemukan: {path}")
    try:
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise GeneratorError(f"file schema bukan JSON yang valid: {path} ({e})")
    if not rows:
        raise GeneratorError(f"File schema kosong: {path}")
    return rows


def parse_enum(column_type):
    inside = re.match(r"enum\((.*)\)$", column_type, re.I).group(1)
    return [v.replace("''", "'") for v in re.findall(r"'((?:[^']|'')*)'", inside)]


def map_column(row, warnings):
    """Ubah 1 baris INFORMATION_SCHEMA menjadi definisi kolom untuk template."""
    name, dtype = row["COLUMN_NAME"], row["DATA_TYPE"].lower()
    ctype = (row.get("COLUMN_TYPE") or dtype).lower()
    length = row.get("CHARACTER_MAXIMUM_LENGTH")
    enum = None

    if dtype in INT_TYPES:
        sa, py = INT_TYPES[dtype], "int"
    elif dtype in ("varchar", "char"):
        sa, py = f"String({length})" if length else "String", "str"
    elif dtype in TEXT_TYPES:
        sa, py = "Text", "str"
    elif dtype == "enum":
        enum = parse_enum(row.get("COLUMN_TYPE") or "")
        sa, py = f"String({max((len(v) for v in enum), default=50)})", "str"
    elif dtype in ("decimal", "numeric"):
        sa, py = f"Numeric({row.get('NUMERIC_PRECISION') or 18}, {row.get('NUMERIC_SCALE') or 0})", "Decimal"
    elif dtype == "float":
        sa, py = "Float", "float"
    elif dtype in ("double", "real"):
        sa, py = "Double", "float"
    elif dtype == "date":
        sa, py = "Date", "date"
    elif dtype in ("datetime", "timestamp"):
        sa, py = "DateTime", "datetime"
    elif dtype == "time":
        sa, py = "Time", "time"
    elif dtype == "json":
        sa, py = "JSON", "dict"
    else:
        sa, py = "String", "str"
        warnings.append(f"kolom `{name}` bertipe `{ctype}` belum dikenali, dipetakan ke String/str (cek manual)")

    nullable = str(row.get("IS_NULLABLE", "YES")).upper() == "YES"
    default = row.get("COLUMN_DEFAULT")
    if isinstance(default, str):
        default = default.strip("'")
        if default.upper() in ("NULL", "") or "CURRENT_TIMESTAMP" in default.upper() or py in ("date", "datetime", "time", "dict"):
            default = None
        elif py == "int":
            default = int(default) if re.fullmatch(r"-?\d+", default) else None
        elif py in ("float", "Decimal"):
            default = float(default) if re.fullmatch(r"-?\d+(\.\d+)?", default) else None

    return {
        "name": name, "sa_type": sa, "py": py, "enum": enum, "nullable": nullable, "default": default,
        "is_pk": row.get("COLUMN_KEY") == "PRI",
        "auto_increment": "auto_increment" in str(row.get("EXTRA") or "").lower(),
    }


# ============================================= Context template =============================================
def build_context(module_path, fitur, table, raw_columns, api_prefix=None, tag=None, unique="auto"):
    warnings = []
    cols = [map_column(r, warnings) for r in raw_columns]
    pks = [c for c in cols if c["is_pk"]]
    if len(pks) != 1:
        raise GeneratorError(f"Table `{table}` harus punya tepat 1 primary key (ditemukan {len(pks)}). "
                             "Composite key belum didukung template standar.")
    pk = pks[0]
    if not pk["auto_increment"]:
        warnings.append(f"primary key `{pk['name']}` bukan AUTO_INCREMENT: nilai id perlu diisi manual saat create")

    names = {c["name"] for c in cols}
    columns, data_columns, sa_imports, sensitive = [], [], set(), []
    for c in cols:
        audit = audit_attr(c["name"]) if not c["is_pk"] else None
        attr = audit or c["name"]
        sa_imports.add(re.match(r"\w+", c["sa_type"]).group(0))
        columns.append({"name": c["name"], "attr": attr, "sa_type": c["sa_type"], "is_pk": c["is_pk"]})
        if c["is_pk"] or audit:
            continue
        if any(s in c["name"].lower() for s in SENSITIVE_PARTS):
            sensitive.append(c["name"])
            continue
        base = f"Literal[{', '.join(repr(v) for v in c['enum'])}]" if c["enum"] else c["py"]
        required = not c["nullable"] and c["default"] is None
        if c["enum"] and c["default"] not in (None, *c["enum"]):
            c["default"] = None
        data_columns.append({
            "name": c["name"], "attr": attr, "py": c["py"], "enum": c["enum"],
            "annotation": base if required else f"Optional[{base}]",
            "optional_annotation": f"Optional[{base}]",
            "default_repr": None if required else repr(c["default"]),
            "doc": (f"ENUM pilihan {'/'.join(f'`{v}`' for v in c['enum'])}" if c["enum"]
                    else DOC_BY_TYPE.get(c["py"], c["py"])) + (" (wajib)" if required else ""),
        })
    if sensitive:
        warnings.append("kolom sensitif tidak dijadikan input/pencarian/JSON: " + ", ".join(sensitive) + " (tambahkan manual bila memang dibutuhkan, mis. hash password)")
    if not data_columns:
        warnings.append("table tidak punya kolom data selain primary key & kolom audit")

    attrs = {c["attr"] for c in columns}
    data_names = {c["name"] for c in data_columns}
    if unique == "auto":
        unique_column = next((n for n in (f"{fitur}_kode", f"{fitur}_nama")
                              if n in data_names and next(c for c in data_columns if c["name"] == n)["py"] == "str"), None)
    elif unique in (None, "none", ""):
        unique_column = None
    else:
        if unique not in data_names:
            raise GeneratorError(f"--unique `{unique}` bukan kolom data table `{table}`. Kolom: {', '.join(sorted(data_names))}")
        unique_column = unique

    aktif = next((c for c in data_columns if c["name"].endswith("_aktif") and c["enum"]), None)
    domain = module_path.split(".")[0]
    unique_suffix = None
    if unique_column:
        unique_suffix = unique_column[len(fitur) + 1:] if unique_column.startswith(fitur + "_") else unique_column

    ctx = {
        "module_path": module_path, "domain": domain, "fitur": fitur, "Fitur": pascal(fitur),
        "fitur_camel": camel(fitur), "fitur_title": title(fitur), "table": table,
        "pk": pk["name"], "pk_path": "/{" + pk["name"] + "}",
        "api_prefix": api_prefix if api_prefix is not None else f"/{domain}", "url_prefix": f"/{fitur}",
        "tag": tag or f"{title(domain)} - {title(fitur)}",
        "columns": columns, "data_columns": data_columns, "sa_imports": sorted(sa_imports - {"Column"}),
        "needs_datetime": any(c["py"] in ("date", "datetime", "time") for c in data_columns),
        "needs_decimal": any(c["py"] == "Decimal" for c in data_columns),
        "search_columns": [c["name"] for c in data_columns if c["py"] == "str" and not c["enum"]],
        "aktif_column": {"name": aktif["name"], "literal_values": ", ".join(repr(v) for v in aktif["enum"]),
                         "has_tidak_aktif": "Tidak Aktif" in aktif["enum"]} if aktif else None,
        "unique_column": unique_column, "unique_suffix": unique_suffix,
        "unique_title": title(unique_column) if unique_column else None,
        "has_deleted_at": "deleted_at" in attrs, "has_deleted_by": "deleted_by" in attrs,
        "has_created": "created_at" in attrs and "created_by" in attrs,
        "has_updated": "updated_at" in attrs and "updated_by" in attrs,
        "has_revised": any(c["attr"] == "revised" for c in columns),
    }
    return ctx, warnings


# ============================================= Render & tulis file =============================================
def output_files(ctx):
    base = API_DIR / "core" / "modules" / Path(*ctx["module_path"].split("."))
    f = ctx["fitur"]
    return {
        "model.py.jinja": base / "model" / f"{f}_model.py",
        "schema.py.jinja": base / "schema" / f"{f}_schema.py",
        "check.py.jinja": base / "crud" / f"{f}_check.py",
        "crud.py.jinja": base / "crud" / f"{f}_crud.py",
        "router.py.jinja": base / "router" / f"{f}_router.py",
        "json.py.jinja": API_DIR / "core" / "shared" / "json_helpers" / ctx["domain"] / f"json_{f}.py",
    }


def package_inits(ctx):
    """__init__.py yang perlu ada supaya semua folder baru menjadi paket python (dibuat kosong)."""
    modules_root = API_DIR / "core" / "modules"
    inits, cur = [], modules_root
    for part in ctx["module_path"].split("."):
        cur = cur / part
        inits.append(cur / "__init__.py")
    base = cur
    inits += [base / sub / "__init__.py" for sub in ("model", "schema", "crud", "router")]
    inits.append(API_DIR / "core" / "shared" / "json_helpers" / ctx["domain"] / "__init__.py")
    return inits


def find_existing_model(table):
    pattern = re.compile(r"__tablename__\s*=\s*[\"']" + re.escape(table) + r"[\"']")
    for p in (API_DIR / "core").rglob("*_model.py"):
        if pattern.search(p.read_text(encoding="utf-8", errors="ignore")):
            return p
    return None


def render(ctx):
    import jinja2
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)), trim_blocks=True,
                             lstrip_blocks=True, keep_trailing_newline=True, undefined=jinja2.StrictUndefined)
    out = {}
    for tpl, path in output_files(ctx).items():
        code = env.get_template(tpl).render(**ctx)
        compile(code, str(path), "exec")       # pastikan hasil render valid python
        out[path] = code
    return out


def rel(p):
    return p.relative_to(ROOT).as_posix()


# ============================================= Perintah: fastflow module new =============================================
def cmd_new(args):
    parts = args.module_path.strip("/").replace("\\", "/").split("/")
    for p in parts:
        if not NAME_RE.match(p):
            raise GeneratorError(f"nama folder `{p}` tidak valid (huruf kecil, angka, underscore; diawali huruf)")
    module_path = ".".join(parts)
    fitur = args.fitur or parts[-1]
    if not NAME_RE.match(fitur):
        raise GeneratorError(f"nama fitur `{fitur}` tidak valid")
    table = args.table or fitur
    validate_api_prefix(args.api_prefix)

    existing_model = find_existing_model(table)
    if existing_model and not args.force:
        raise GeneratorError(f"table `{table}` sudah punya model: {rel(existing_model)}\n"
                             "        Dua model untuk table yang sama akan membuat aplikasi gagal start.")

    if args.schema_file:
        raw = read_columns_from_file(args.schema_file)
        source = f"file {args.schema_file}"
    else:
        raw = read_columns_from_db(table, args.env_key)
        source = f"database ({args.env_key})"

    ctx, warnings = build_context(module_path, fitur, table, raw, api_prefix=args.api_prefix,
                                  tag=args.tag, unique=args.unique)
    files = render(ctx)

    exists = [p for p in files if p.exists()]
    if exists and not args.force:
        raise GeneratorError("file berikut sudah ada (pakai --force untuk menimpa):\n" +
                             "\n".join(f"        - {rel(p)}" for p in exists))

    print(f"[INFO] table      : {table} (dibaca dari {source})")
    print(f"[INFO] modul      : core/modules/{'/'.join(parts)}  | fitur: {fitur}")
    print(f"[INFO] primary key: {ctx['pk']}  | kolom data: {len(ctx['data_columns'])}")
    print(f"[INFO] soft delete: {'ya' if ctx['has_deleted_at'] else 'tidak (hapus permanen)'}"
          f"  | filter aktif: {ctx['aktif_column']['name'] if ctx['aktif_column'] else '-'}"
          f"  | cek duplikat: {ctx['unique_column'] or '-'}")
    print(f"[INFO] endpoint   : {ctx['api_prefix']}{ctx['url_prefix']}  | tag: {ctx['tag']}")
    for w in warnings:
        print(f"[PERINGATAN] {w}")

    print("\nFile yang " + ("AKAN dibuat (dry-run, tidak ada yang ditulis):" if args.dry_run else "dibuat:"))
    for p in files:
        print(f"  {'[timpa] ' if p.exists() else ''}{rel(p)}")

    if not args.dry_run:
        for init in package_inits(ctx):
            if not init.exists():
                init.parent.mkdir(parents=True, exist_ok=True)
                init.write_text("", encoding="utf-8")
        for path, code in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(code, encoding="utf-8")

    if args.no_register:
        print_manual_steps(ctx, args)
        return

    from fastflow_tools import module_registry
    try:
        module_registry.register(ctx["module_path"], ctx["fitur"], f"router{ctx['Fitur']}", ctx["tag"],
                                 ctx["api_prefix"], args.description, dry_run=args.dry_run)
    except module_registry.RegistryError as e:
        raise GeneratorError(f"file modul sudah dibuat, tapi registrasi gagal: {e}\n"
                             f"        Perbaiki lalu jalankan: fastflow module register {args.module_path}"
                             + (f" --fitur {ctx['fitur']}" if args.fitur else ""))

    if not args.dry_run:
        print(f"""
Selesai. Langkah berikutnya:
  1. Jalankan aplikasi lalu cek /docs (tag "{ctx['tag']}")
  2. Lengkapi deskripsi tag di core/router/api_metadata.py
  3. Sesuaikan logika bisnis di crud/router bila perlu""")


def print_manual_steps(ctx, args):
    if args.dry_run:
        return
    register_cmd = f"poetry run fastflow module register {args.module_path}" + (f" --fitur {ctx['fitur']}" if args.fitur else "")
    if args.api_prefix:
        register_cmd += f" --api-prefix {args.api_prefix}"
    print(f"""
Router BELUM didaftarkan (--no-register). Daftarkan dengan:
  {register_cmd}
""")


def main(args):
    try:
        if args.module_command == "new":
            cmd_new(args)
    except GeneratorError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
