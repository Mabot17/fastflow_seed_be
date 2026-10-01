"""Test fastflow_tools: generator (render di memori, tidak menulis file) & CLI."""
import json
import subprocess
import sys

from conftest import ROOT
from fastflow_tools import module_generator as g


def kolom(name, dtype, ctype=None, null="YES", default=None, key="", length=None, extra=""):
    return dict(COLUMN_NAME=name, DATA_TYPE=dtype, COLUMN_TYPE=ctype or dtype, IS_NULLABLE=null,
                COLUMN_DEFAULT=default, COLUMN_KEY=key, CHARACTER_MAXIMUM_LENGTH=length,
                NUMERIC_PRECISION=18, NUMERIC_SCALE=2, EXTRA=extra)


TABLE_VOUCHER = [
    kolom("voucher_id", "int", null="NO", key="PRI", extra="auto_increment"),
    kolom("voucher_kode", "varchar", null="NO", length=30),
    kolom("voucher_nilai", "decimal", "decimal(18,2)", null="NO", default="0.00"),
    kolom("voucher_berlaku", "date"),
    kolom("voucher_aktif", "enum", "enum('Aktif','Tidak Aktif')", default="Aktif"),
    kolom("voucher_secret_token", "varchar", length=100),
    kolom("voucher_created_at", "datetime"), kolom("voucher_created_by", "varchar", length=50),
    kolom("voucher_deleted_at", "datetime"), kolom("voucher_deleted_by", "varchar", length=50),
]


def test_generator_render_valid_dan_aturan_kolom():
    ctx, warnings = g.build_context("master.voucher", "voucher", "voucher", TABLE_VOUCHER)
    files = g.render(ctx)                                    # compile() di dalam render -> python valid
    assert len(files) == 6
    attrs = {c["name"]: c["attr"] for c in ctx["columns"]}
    assert attrs["voucher_created_at"] == "created_at" and attrs["voucher_deleted_by"] == "deleted_by"
    assert ctx["has_deleted_at"] and ctx["has_created"]
    data = {c["name"] for c in ctx["data_columns"]}
    assert "voucher_secret_token" not in data                # kolom sensitif dikecualikan
    assert any("sensitif" in w for w in warnings)
    assert ctx["unique_column"] == "voucher_kode"
    assert ctx["aktif_column"]["name"] == "voucher_aktif"
    router = next(code for path, code in files.items() if path.name == "voucher_router.py")
    assert "identity: TokenData = Depends(get_current_user)" in router
    assert "core.modules.users" not in "".join(files.values())     # modul baru tidak bergantung pada users


def test_generator_dry_run_tidak_menulis(tmp_path):
    schema = tmp_path / "voucher.json"
    schema.write_text(json.dumps(TABLE_VOUCHER))
    nama = "uji_dryrun_xyz"                                  # nama unik: aman di proyek turunan mana pun
    r = subprocess.run([sys.executable, "-m", "fastflow_tools.cli", "module", "new", nama, "--table", nama,
                        "--schema-file", str(schema), "--api-prefix=/uji", "--dry-run"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "dry-run" in r.stdout
    assert not (ROOT / "fastflow_api" / "core" / "modules" / nama).exists()
    assert not (ROOT / "fastflow_api" / "core" / "router" / "modules_registry" / f"{nama}_routers.py").exists()


def test_cli_help():
    r = subprocess.run([sys.executable, "-m", "fastflow_tools.cli", "--help"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and "module new" in r.stdout
