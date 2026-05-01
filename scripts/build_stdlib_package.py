"""Build pure-Python wheel and sdist artifacts with only the Python stdlib.

This is used by local release validation in environments where the setuptools
build frontend hangs before reaching the project backend.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import tarfile
import tomllib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _hash_record(data: bytes) -> tuple[str, str]:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
    return f"sha256={digest}", str(len(data))


def _metadata(project: dict) -> str:
    lines = [
        "Metadata-Version: 2.4",
        f"Name: {project['name']}",
        f"Version: {project['version']}",
        f"Summary: {project.get('description', '')}",
        "License-Expression: Apache-2.0",
        f"Requires-Python: {project.get('requires-python', '')}",
        "Description-Content-Type: text/markdown",
        "License-File: LICENSE",
    ]
    for extra, deps in project.get("optional-dependencies", {}).items():
        lines.append(f"Provides-Extra: {extra}")
        for dep in deps:
            lines.append(f'Requires-Dist: {dep}; extra == "{extra}"')
    lines.append("")
    lines.append((ROOT / "README.md").read_text(encoding="utf-8"))
    return "\n".join(lines) + "\n"


def _build_wheel(out_dir: Path, project: dict) -> Path:
    name = project["name"]
    version = project["version"]
    dist_name = name.replace("-", "_")
    dist_info = f"{dist_name}-{version}.dist-info"

    entries: dict[str, bytes] = {}
    for path in sorted((ROOT / "stem_ai").glob("*.py")):
        entries[f"stem_ai/{path.name}"] = path.read_bytes()
    entries[f"{dist_info}/METADATA"] = _metadata(project).encode("utf-8")
    entries[f"{dist_info}/WHEEL"] = (
        b"Wheel-Version: 1.0\n"
        b"Generator: stem-ai-stdlib-build\n"
        b"Root-Is-Purelib: true\n"
        b"Tag: py3-none-any\n"
    )
    entries[f"{dist_info}/entry_points.txt"] = b"[console_scripts]\nstem = stem_ai.cli:main\n"
    entries[f"{dist_info}/top_level.txt"] = b"stem_ai\n"
    entries[f"{dist_info}/licenses/LICENSE"] = (ROOT / "LICENSE").read_bytes()

    rows = []
    for arcname, data in entries.items():
        digest, size = _hash_record(data)
        rows.append([arcname, digest, size])
    rows.append([f"{dist_info}/RECORD", "", ""])
    record = io.StringIO()
    csv.writer(record, lineterminator="\n").writerows(rows)
    entries[f"{dist_info}/RECORD"] = record.getvalue().encode("utf-8")

    wheel_path = out_dir / f"{dist_name}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as wheel:
        for arcname, data in entries.items():
            wheel.writestr(arcname, data)
    return wheel_path


def _build_sdist(out_dir: Path, project: dict) -> Path:
    name = project["name"].replace("-", "_")
    version = project["version"]
    prefix = f"{name}-{version}"
    files = [
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "MANIFEST.in",
        "README.md",
        "pyproject.toml",
        "requirements.txt",
    ]
    files += [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "stem_ai").glob("*.py"))]
    files += [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "tests").glob("*.py"))]

    sdist_path = out_dir / f"{prefix}.tar.gz"
    with tarfile.open(sdist_path, "w:gz") as sdist:
        for rel in files:
            path = ROOT / rel
            if path.exists():
                sdist.add(path, arcname=f"{prefix}/{rel}")
    return sdist_path


def main() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    out_dir = ROOT / "dist"
    out_dir.mkdir(exist_ok=True)
    wheel = _build_wheel(out_dir, project)
    sdist = _build_sdist(out_dir, project)
    print(wheel)
    print(sdist)


if __name__ == "__main__":
    main()
