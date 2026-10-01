"""Test kerangka: aplikasi boot, dokumentasi, format error standar, dan aturan arsitektur seed."""
import ast
from pathlib import Path

from conftest import ROOT, assert_status_match
from core.router.api_metadata import VERSI_API

CORE = ROOT / "fastflow_api" / "core"


def test_version(client):
    r = client.get("/version")
    assert r.status_code == 200
    assert r.json() == {"version": VERSI_API}


def test_changelog(client):
    r = client.get("/version/changelog")
    assert r.status_code == 200
    assert "Changelog" in r.text


def test_halaman_dokumentasi(client):
    for path in ("/docs", "/redoc", "/rapidoc"):
        assert client.get(path).status_code == 200, path


def test_openapi_berisi_modul_dan_ref_error(client):
    spec = client.get("/openapi.json").json()
    assert "/login" in spec["paths"]
    assert "/sistem/users" in spec["paths"]
    assert "/sistem/users/{user_id}" in spec["paths"]
    # contoh error identik dipindah ke components/responses (optimasi openapi)
    assert spec["components"]["responses"]
    assert spec["paths"]["/sistem/users"]["get"]["responses"]["401"] == {"$ref": "#/components/responses/Error401"}
    tags = [t["name"] for t in spec["tags"]]
    assert "Sistem - Users" in tags and "Authentication" in tags


def test_tanpa_token_401_format_standar(client):
    r = client.get("/sistem/users")
    assert r.status_code == 401
    assert r.json()["status"]["code"] == 401
    assert r.json()["error"] == "Token tidak valid. Silahkan login kembali."


def test_token_tidak_valid_401(client):
    r = client.get("/sistem/users", headers={"Authorization": "Bearer token-ngawur"})
    assert r.status_code == 401
    assert_status_match(r)


def test_method_salah_405_format_standar(client):
    r = client.delete("/version")
    assert r.status_code == 405
    assert_status_match(r)


def test_path_mencurigakan_diblokir(client):
    assert client.get("/static/..%2F..%2Fcore/.env").status_code in (403, 404)


def test_socket_app_membungkus_fastapi():
    import main
    assert main.app.other_asgi_app is main.fastapi_app


# ============================================= Aturan arsitektur =============================================
def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module, node.lineno
        elif isinstance(node, ast.Import):
            for a in node.names:
                yield a.name, node.lineno


def _milik_modul(p: Path) -> bool:
    """File milik modul: core/modules/**, modules_registry, api_router, dan json helper modul (json_helpers/<domain>/)."""
    parts = p.relative_to(CORE).parts
    return ("modules" in parts or "modules_registry" in parts or p.name == "api_router.py"
            or (parts[:2] == ("shared", "json_helpers") and len(parts) > 3))


def test_kerangka_tidak_bergantung_pada_modul():
    """File kerangka tidak boleh meng-import core.modules.* (supaya seed tetap bersih & bisa dipakai ulang)."""
    kerangka = [p for p in CORE.rglob("*.py") if not _milik_modul(p)]
    kerangka += [ROOT / "fastflow_api" / "database.py"]
    pelanggaran = [f"{p.relative_to(ROOT)}:{ln} -> {mod}"
                   for p in kerangka for mod, ln in _imports(p) if mod.startswith("core.modules")]
    assert not pelanggaran, "\n".join(pelanggaran)


def test_init_modul_kosong():
    """__init__.py di core/modules harus kosong (router didaftarkan di modules_registry)."""
    isi = [str(p.relative_to(ROOT)) for p in (CORE / "modules").rglob("__init__.py")
           if p.read_text(encoding="utf-8").strip()]
    assert not isi, isi


def test_jsonresponse_selalu_pakai_status_code():
    pelanggaran = []
    for p in (CORE / "modules").rglob("*.py"):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "JSONResponse":
                if not any(k.arg == "status_code" for k in node.keywords):
                    pelanggaran.append(f"{p.relative_to(ROOT)}:{node.lineno}")
    assert not pelanggaran, pelanggaran


def test_tidak_ada_check_data_model():
    assert not (CORE / "shared" / "check_data_model.py").exists()
