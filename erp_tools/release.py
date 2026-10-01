#!/usr/bin/env python3
"""Auto release versi ERP API.

Cara pakai:
    poetry run release                            # bump patch otomatis (alias lama)
    poetry run erp release                        # sama, lewat CLI erp_tools
    poetry run release --version 0.1              # target custom: 0.1.0 (minor, patch reset 0)
    poetry run release --dry-run                  # preview tanpa mengubah apa pun
    python erp_tools/release.py                   # fallback tanpa poetry

Alur:
    1. Validasi working tree bersih.
    2. Cari versi tertinggi dari api_metadata.py, pyproject.toml, CHANGELOG.md,
       dan tag yang REACHABLE dari HEAD (tag stale hasil reset diabaikan).
    3. Tentukan target: bump patch (+1) atau --version custom.
    4. Kumpulkan subject commit fitur sejak release terakhir.
    5. Update pyproject.toml + api_metadata.py.
    6. Append section baru di CHANGELOG.md.
    7. Commit "[API - UP Versi x.y.z]" lalu "API Changelog x.y.z".
    8. Buat git tag vx.y.z (tag stale dengan nama sama dihapus dulu). Tanpa push.
"""
import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

def _find_root():
    current = Path(__file__).resolve().parent
    for _ in range(6):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent   # erp_tools/ -> root repo


ROOT = _find_root()
PYPROJECT = ROOT / "pyproject.toml"
API_METADATA = ROOT / "erp_api" / "core" / "router" / "api_metadata.py"
CHANGELOG = ROOT / "CHANGELOG.md"

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
RE_VERSION_TOML = re.compile(r"^(version\s*=\s*)\"([^\"]*)\"", re.MULTILINE)
RE_VERSION_META = re.compile(r"(VERSI_API\s*=\s*)\"([^\"]*)\"")
RE_CHG_VERSION = re.compile(r"^##\s*\[([0-9]+\.[0-9]+\.[0-9]+)\]", re.MULTILINE)
RE_RELEASE_MSG = re.compile(r"(API Changelog|UP Versi)\s+((?:0|1)\.\d+\.\d+)")
RE_TAG = re.compile(r"^v?([0-9]+\.[0-9]+\.[0-9]+)$")
RE_PARTIAL = re.compile(r"^\d+(?:\.\d+){0,2}$")


def fail(msg):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def git(args, allow_fail=False):
    proc = subprocess.run(
        ["git"] + args, cwd=ROOT, capture_output=True, text=True
    )
    if proc.returncode != 0 and not allow_fail:
        fail(f"git {' '.join(args)} gagal:\n{proc.stderr.strip()}")
    return proc


def parse_version(raw):
    m = SEMVER.match(str(raw).strip())
    if not m:
        return None
    return tuple(int(x) for x in m.groups())


def read_versions():
    found = []

    if PYPROJECT.exists():
        m = RE_VERSION_TOML.search(PYPROJECT.read_text(encoding="utf-8"))
        if m:
            found.append(("pyproject.toml", m.group(2)))
    if API_METADATA.exists():
        m = RE_VERSION_META.search(API_METADATA.read_text(encoding="utf-8"))
        if m:
            found.append(("api_metadata.py", m.group(2)))
    if CHANGELOG.exists():
        versions = RE_CHG_VERSION.findall(
            CHANGELOG.read_text(encoding="utf-8", errors="replace"))
        if versions:
            found.append(("CHANGELOG.md", versions[-1]))

    tags = git(["tag", "--merged", "HEAD"], allow_fail=True)
    if tags and tags.returncode == 0:
        for tag in tags.stdout.splitlines():
            m = RE_TAG.match(tag.strip())
            if m:
                found.append((f"tag {tag.strip()}", m.group(1)))

    parsed = []
    for src, raw in found:
        v = parse_version(raw)
        if v:
            parsed.append((src, v))
        else:
            print(f"[WARN] format versi tidak dikenal di {src}: {raw!r}")

    if not parsed:
        fail("tidak ada versi valid ditemukan.")

    latest_src, latest = max(parsed, key=lambda x: x[1])
    mismatched = {src for src, v in parsed if v != latest}
    if len(mismatched) > 1:
        print(f"[WARN] versi tidak seragam: {parsed}")
    print(f"[INFO] versi tertinggi saat ini: {'.'.join(map(str, latest))} (dari {latest_src})")
    return latest_src, latest


def bump(v):
    major, minor, patch = v
    return (major, minor, patch + 1)


def parse_custom_version(raw):
    raw = str(raw).strip()
    if not RE_PARTIAL.match(raw):
        return None
    parts = raw.split(".")
    parts += ["0"] * (3 - len(parts))
    return tuple(int(x) for x in parts)


def tag_exists(tag):
    return git(["rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
               allow_fail=True).returncode == 0


def tag_reachable(tag):
    return git(["merge-base", "--is-ancestor", tag, "HEAD"],
               allow_fail=True).returncode == 0


def ensure_tag_available(tag):
    if not tag_exists(tag):
        return
    if tag_reachable(tag):
        fail(f"tag {tag} sudah ada dan reachable dari HEAD (sudah dirilis).")
    print(f"[WARN] hapus tag stale {tag} (tidak reachable dari HEAD)...")
    git(["tag", "-d", tag])


def find_boundary(newest):
    patterns = [
        f"API Changelog {newest[0]}.{newest[1]}.{newest[2]}",
        f"UP Versi {newest[0]}.{newest[1]}.{newest[2]}",
    ]
    args = ["log", "--format=%H%x09%s", "--no-merges"]
    for p in patterns:
        args += ["--fixed-strings", "--grep", p]
    proc = git(args)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if lines:
        return lines[0]

    proc = git(["log", "--format=%H%x09%s", "--no-merges",
                "--grep", "UP Versi"])
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if lines:
        return lines[0]
    return None


def parse_bullets(subject):
    text = subject.strip()
    if re.match(r"^Merge\b", text, re.IGNORECASE):
        return []
    if RE_RELEASE_MSG.search(text):
        return []
    first_close = text.find("]")
    if text.startswith("[") and first_close >= 0:
        text = text[first_close + 1:]
    parts = re.split(r"\s+-\s+|\s*[·\u2013|]\s*", text)
    bullets = []
    seen = set()
    for part in parts:
        part = re.sub(r'^Revert\s*"?|"\s*$', "", part.strip(), flags=re.IGNORECASE)
        part = part.strip()
        if not part or part in seen:
            continue
        seen.add(part)
        bullets.append(part)
    return bullets


def collect_changes(boundary_line):
    if not boundary_line:
        return []
    boundary_hash = boundary_line.split("\t", 1)[0]
    proc = git(["log", "--format=%s", f"{boundary_hash}..HEAD"])
    changes = []
    seen = set()
    for subject in proc.stdout.splitlines():
        for bullet in parse_bullets(subject):
            if bullet in seen:
                continue
            seen.add(bullet)
            changes.append(bullet)
    return changes


def update_pyproject(new_text):
    path = PYPROJECT
    content = path.read_text(encoding="utf-8")
    new_content, count = RE_VERSION_TOML.subn(
        lambda m: f'{m.group(1)}"{new_text}"', content, count=1
    )
    if count != 1:
        fail("gagal update versi di pyproject.toml")
    path.write_text(new_content, encoding="utf-8")


def update_api_metadata(new_text):
    path = API_METADATA
    content = path.read_text(encoding="utf-8")
    new_content, count = RE_VERSION_META.subn(
        lambda m: f'{m.group(1)}"{new_text}"', content, count=1
    )
    if count != 1:
        fail("gagal update versi di api_metadata.py")
    path.write_text(new_content, encoding="utf-8")


def append_changelog(new_text, changes):
    section = [f"\n## [{new_text}] - {date.today().isoformat()}"]
    section += [f"- {c}" for c in changes]
    block = "\n".join(section) + "\n"
    with CHANGELOG.open("a", encoding="utf-8") as fh:
        fh.write(block)
    return block


def commit(paths, message):
    git(["add", "--"] + paths)
    git(["commit", "-m", message])


def main():
    parser = argparse.ArgumentParser(description="Auto release versi ERP API")
    parser.add_argument("--dry-run", action="store_true",
                        help="jalankan mode preview tanpa mengubah apa pun")
    parser.add_argument("--version", dest="custom_version", default=None,
                        help="target versi custom (contoh: 0.1 -> 0.1.0, 0.1.5). "
                             "Tanpa opsi ini, patch naik otomatis (+1).")
    args = parser.parse_args()

    proc = git(["status", "--porcelain"], allow_fail=True)
    dirty = [ln for ln in proc.stdout.splitlines()
             if ln.strip() and not ln.startswith("??")]
    if dirty:
        fail("working tree tidak bersih. Commit atau stash dulu:\n" + "\n".join(dirty))

    latest_src, latest = read_versions()
    if args.custom_version is not None:
        new = parse_custom_version(args.custom_version)
        if new is None:
            fail(f"format --version tidak dikenal: {args.custom_version!r}. "
                 "Contoh valid: 0.1, 0.1.5, 1")
        if new < latest:
            fail(f"--version {'.'.join(map(str, new))} lebih kecil dari versi "
                 f"sekarang {'.'.join(map(str, latest))}. Cegah downgrade.")
    else:
        new = bump(latest)
    new_text = ".".join(map(str, new))
    tag_name = f"v{new_text}"

    boundary = find_boundary(latest)
    changes = collect_changes(boundary)
    if boundary:
        boundary_subject = boundary.split("\t", 1)[1]
        print(f"[INFO] sejak commit: {boundary_subject}")
    print(f"[INFO] versi baru: {new_text} ({len(changes)} item changelog)")

    if args.dry_run:
        print("\n--- CHANGELOG yang akan ditambahkan ---")
        for c in changes:
            print(f"- {c}")
        print(f"\n--- Commit yang akan dibuat ---")
        print(f"[API - UP Versi {new_text}]  -> pyproject.toml, api_metadata.py")
        print(f"API Changelog {new_text}      -> CHANGELOG.md")
        if tag_exists(tag_name):
            if tag_reachable(tag_name):
                print(f"git tag {tag_name} sudah ada & reachable -> ERROR (sudah dirilis)")
            else:
                print(f"git tag {tag_name} ada tapi stale -> akan dihapus lalu "
                      f"buat ulang v{new_text}")
        else:
            print(f"git tag -a {tag_name} -m \"Release {new_text}\" (baru)")
        return

    update_pyproject(new_text)
    update_api_metadata(new_text)
    block = append_changelog(new_text, changes)

    commit([str(PYPROJECT), str(API_METADATA)], f"[API - UP Versi {new_text}]")
    commit([str(CHANGELOG)], f"API Changelog {new_text}")
    ensure_tag_available(tag_name)
    git(["tag", "-a", tag_name, "-m", f"Release {new_text}"])

    print("\n[OK] Release selesai:")
    print(f"  v{new_text}")
    print(f"[INFO] CHANGELOG ditambahkan:\n{block}")
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    print(f"[INFO] Push manual: git push origin {branch} --tags")


if __name__ == "__main__":
    main()