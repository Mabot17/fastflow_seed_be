"""
============================================= Start Noted module_registry ===================================
Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
1. `erp module register` -> daftarkan router modul ke 3 tempat:
   - core/router/modules_registry/<domain>_routers.py  (import router)
   - core/router/api_router.py                          (import + include_router)
   - core/router/api_metadata.py                        (tag di TAGS_METADATA_API)
2. Aman dijalankan berulang: yang sudah terdaftar dilewati, tidak dobel
3. Dipanggil otomatis oleh `erp module new` (kecuali --no-register)
============================================= END Noted module_registry ===================================
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "erp_api" / "core"
REGISTRY_DIR = CORE / "router" / "modules_registry"
API_ROUTER = CORE / "router" / "api_router.py"
API_METADATA = CORE / "router" / "api_metadata.py"
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


API_PREFIX_RE = re.compile(r"^(/[A-Za-z0-9_\-/]*)?$")


def validate_api_prefix(api_prefix):
    """Tolak prefix yang bukan path URL (mis. diubah Git Bash menjadi C:/Program Files/Git/...)."""
    if api_prefix is not None and not API_PREFIX_RE.match(api_prefix):
        raise RegistryError(
            f"--api-prefix `{api_prefix}` bukan path URL yang valid (contoh: /master).\n"
            "        Di Git Bash, argumen yang diawali '/' diubah menjadi path Windows. Jalankan dengan\n"
            "        MSYS_NO_PATHCONV=1 poetry run erp ...   atau dari PowerShell/CMD."
        )

REGISTRY_HEADER = '''"""
============================================= Start Noted {d}_routers ===================================
Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
1. Daftar router modul `{d}` (core/modules/{d}), hanya di-import oleh core/router/api_router.py
2. Sengaja TIDAK ditaruh di core/modules/{d}/__init__.py: __init__.py ikut dijalankan setiap kali
   apa pun di bawah paket tsb di-import (termasuk model/crud) -> memuat semua router -> circular import.
3. Pemanggilan di api_router.py:
    from core.router.modules_registry.{d}_routers import nama_router
4. Panduan lengkap: core/router/router_readme.md
============================================= END Noted {d}_routers ===================================
"""
'''


class RegistryError(Exception):
    pass


def title(s):
    return " ".join(w.capitalize() for w in s.split("_"))


def rel(p):
    return p.relative_to(ROOT).as_posix()


# ============================================= Baca / tulis file (pertahankan line ending) =============================================
class SourceFile:
    def __init__(self, path):
        self.path = path
        self.exists = path.exists()
        raw = path.read_bytes().decode("utf-8") if self.exists else ""
        self.nl = "\r\n" if "\r\n" in raw else ("\n" if raw else _repo_newline())
        self.lines = raw.split(self.nl) if raw else []
        self.original = raw

    @property
    def text(self):
        return self.nl.join(self.lines)

    def tree(self):
        return ast.parse(self.text)

    def changed(self):
        return self.text != self.original

    def save(self):
        ast.parse(self.text)    # jangan pernah menulis python yang rusak
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(self.text.encode("utf-8"))


def _repo_newline():
    raw = API_ROUTER.read_bytes() if API_ROUTER.exists() else b""
    return "\r\n" if b"\r\n" in raw else "\n"


# ============================================= Info router =============================================
def router_info(module_path, fitur):
    """Cari nama variabel APIRouter dan tag pertamanya dari file router."""
    path = CORE / "modules" / Path(*module_path.split(".")) / "router" / f"{fitur}_router.py"
    if not path.exists():
        raise RegistryError(f"file router tidak ditemukan: {rel(path)}\n"
                            "        Generate dulu dengan `erp module new`, atau cek --fitur.")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", "") == "APIRouter"):
            var = node.targets[0].id
            tag = None
            for kw in node.value.keywords:
                if kw.arg == "tags" and isinstance(kw.value, ast.List) and kw.value.elts:
                    tag = ast.literal_eval(kw.value.elts[0])
            return var, tag
    raise RegistryError(f"tidak ada `xxx = APIRouter(...)` di {rel(path)}")


# ============================================= 1. modules_registry/<domain>_routers.py =============================================
def plan_registry(domain, module_path, name):
    f = SourceFile(REGISTRY_DIR / f"{domain}_routers.py")
    line = f"from core.modules.{module_path}.router import {name}"
    if f.exists:
        names = {a.asname or a.name for n in f.tree().body if isinstance(n, ast.ImportFrom) for a in n.names}
        if name in names:
            return f, None
        while f.lines and f.lines[-1].strip() == "":
            f.lines.pop()
        f.lines += [line, ""]
    else:
        f.lines = REGISTRY_HEADER.format(d=domain).split("\n") + [line, ""]
    return f, line


# ============================================= 2. api_router.py =============================================
def plan_api_router(domain, name, router_var, api_prefix):
    f = SourceFile(API_ROUTER)
    tree = f.tree()
    registry_mod = f"core.router.modules_registry.{domain}_routers"
    actions = []

    # --- import ---
    imports = [n for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == registry_mod]
    if any(name in {a.asname or a.name for a in n.names} for n in imports):
        pass
    elif imports:
        node = imports[-1]
        last = node.end_lineno - 1
        if node.end_lineno > node.lineno and f.lines[last].strip() == ")":
            # blok bertingkat: sisipkan sebelum ")" dan pastikan item sebelumnya diakhiri koma
            prev = last - 1
            while f.lines[prev].strip() == "" or f.lines[prev].strip().startswith("#"):
                prev -= 1
            code, _, comment = f.lines[prev].partition("#")
            if not code.rstrip().endswith((",", "(")):
                f.lines[prev] = code.rstrip() + "," + (("  #" + comment) if comment else "")
            f.lines.insert(last, f"    {name},")
        else:
            line = f.lines[last].rstrip()
            f.lines[last] = (line[:-1].rstrip(", ") + f", {name})") if line.endswith(")") else f"{line}, {name}"
        actions.append(f"import `{name}` dari {domain}_routers")
    else:
        anchors = [n for n in tree.body if isinstance(n, ast.ImportFrom)
                   and (n.module or "").startswith("core.router.modules_registry.")]
        at = anchors[-1].end_lineno if anchors else max(n.end_lineno for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)))
        f.lines[at:at] = ["", f"from {registry_mod} import (", f"    {name},", ")"]
        actions.append(f"import baru dari {domain}_routers (`{name}`)")

    # --- include_router ---
    include_re = re.compile(r"^apiSettings\.include_router\((\w+)\.(\w+)")
    if any((m := include_re.match(l)) and m.group(1) == name for l in f.lines):
        return f, actions
    prefix_part = f', prefix="{api_prefix}"' if api_prefix else ""
    new_line = f"apiSettings.include_router({name}.{router_var}{prefix_part})"
    single = [i for i, l in enumerate(f.lines) if include_re.match(l) and l.rstrip().endswith(")")]
    same_prefix = [i for i in single if f'prefix="{api_prefix}")' in f.lines[i]] if api_prefix else []
    domain_names = {a.asname or a.name for n in f.tree().body if isinstance(n, ast.ImportFrom) and n.module == registry_mod for a in n.names}
    same_domain = [i for i in single if include_re.match(f.lines[i]).group(1) in domain_names]
    target = (same_prefix or same_domain or single or [len(f.lines) - 1])[-1]
    f.lines.insert(target + 1, new_line)
    actions.append(new_line)
    return f, actions


# ============================================= 3. api_metadata.py =============================================
def plan_metadata(domain, tag, description):
    f = SourceFile(API_METADATA)
    tree = f.tree()
    node = next((n for n in tree.body if isinstance(n, ast.Assign)
                 and getattr(n.targets[0], "id", "") == "TAGS_METADATA_API"), None)
    if node is None or not isinstance(node.value, ast.List):
        raise RegistryError("TAGS_METADATA_API tidak ditemukan di api_metadata.py")
    entries = []
    for e in node.value.elts:
        if isinstance(e, ast.Dict):
            d = {k.value: v for k, v in zip(e.keys, e.values) if isinstance(k, ast.Constant)}
            if isinstance(d.get("name"), ast.Constant):
                entries.append((d["name"].value, e))
    if any(n == tag for n, _ in entries):
        return f, None
    group = f"{title(domain)} - "
    same = [e for n, e in entries if n.startswith(group)]
    target = (same or [e for _, e in entries])[-1] if entries else None
    if target is None:
        raise RegistryError("TAGS_METADATA_API kosong, tambahkan tag secara manual")
    end = target.end_lineno - 1
    if not f.lines[end].rstrip().endswith(","):
        f.lines[end] = f.lines[end].rstrip() + ","
    block = [
        "    {",
        f'        "name": "{tag}",',
        '        "description": """',
        f"    {description}",
        '        """',
        "    },",
    ]
    f.lines[end + 1:end + 1] = block
    return f, f'{{"name": "{tag}", ...}}'


# ============================================= Proses register =============================================
def register(module_path, fitur, router_var, tag, api_prefix, description=None, dry_run=False):
    domain = module_path.split(".")[0]
    name = f"{fitur}_router"
    description = description or f"API {title(fitur)} (dibuat oleh erp module, silakan lengkapi deskripsinya)"

    plans = []
    reg_file, reg_line = plan_registry(domain, module_path, name)
    plans.append((reg_file, [("file baru, " if not reg_file.exists else "") + reg_line] if reg_line else []))
    api_file, api_actions = plan_api_router(domain, name, router_var, api_prefix)
    plans.append((api_file, api_actions))
    meta_file, meta_action = plan_metadata(domain, tag, description)
    plans.append((meta_file, [f"tag {meta_action}"] if meta_action else []))

    print("\nRegistrasi router" + (" (dry-run, tidak ada yang ditulis):" if dry_run else ":"))
    for f, actions in plans:
        if actions:
            for a in actions:
                print(f"  [TAMBAH] {rel(f.path)}: {a}")
        else:
            print(f"  [LEWATI] {rel(f.path)}: sudah terdaftar")

    if not dry_run:
        for f, actions in plans:
            if actions and f.changed():
                f.save()
    return any(a for _, a in plans)


# ============================================= Perintah: erp module register =============================================
def cmd_register(args):
    parts = args.module_path.strip("/").replace("\\", "/").split("/")
    for p in parts:
        if not NAME_RE.match(p):
            raise RegistryError(f"nama folder `{p}` tidak valid")
    module_path = ".".join(parts)
    fitur = args.fitur or parts[-1]
    validate_api_prefix(args.api_prefix)
    router_var, router_tag = router_info(module_path, fitur)
    tag = router_tag or f"{title(parts[0])} - {title(fitur)}"
    api_prefix = args.api_prefix if args.api_prefix is not None else f"/{parts[0]}"
    print(f"[INFO] router: core/modules/{'/'.join(parts)}/router/{fitur}_router.py -> {router_var}")
    print(f"[INFO] prefix: {api_prefix or '(tanpa prefix)'}  | tag: {tag}")
    changed = register(module_path, fitur, router_var, tag, api_prefix, args.description, args.dry_run)
    if changed and not args.dry_run:
        print("\nSelesai. Jalankan aplikasi lalu cek /docs.")


def main(args):
    try:
        cmd_register(args)
    except RegistryError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
