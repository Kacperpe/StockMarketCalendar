#!/usr/bin/env python
"""
Build a requirements file containing only packages that are missing
or do not match pinned versions.

Usage:
  python filter_missing_requirements.py <requirements_in> <requirements_out>
"""

from __future__ import annotations

import re
import sys
from importlib import metadata as importlib_metadata


_REQ_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(.*)$")
_CANON_RE = re.compile(r"[-_.]+")


def _canon(name: str) -> str:
    return _CANON_RE.sub("-", name).lower()


def _iter_requirements(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if " #" in line:
                line = line.split(" #", 1)[0].rstrip()
            yield line


def _installed_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for dist in importlib_metadata.distributions():
        name = dist.metadata.get("Name")
        if name:
            versions[_canon(name)] = dist.version
    return versions


def _is_satisfied(requirement: str, installed: dict[str, str]) -> bool:
    match = _REQ_RE.match(requirement)
    if not match:
        return False

    package_name, spec = match.groups()
    current = installed.get(_canon(package_name))
    if current is None:
        return False

    spec = spec.strip()
    if ";" in spec:
        spec = spec.split(";", 1)[0].strip()
    if not spec:
        return True
    if spec.startswith("=="):
        expected = spec[2:].strip()
        return current == expected

    # Unsupported specifier style: install/update via pip for safety.
    return False


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: filter_missing_requirements.py <requirements_in> <requirements_out>")
        return 2

    req_in, req_out = sys.argv[1], sys.argv[2]
    installed = _installed_versions()
    requirements = list(_iter_requirements(req_in))
    missing = [req for req in requirements if not _is_satisfied(req, installed)]

    with open(req_out, "w", encoding="utf-8", newline="\n") as out:
        for req in missing:
            out.write(req + "\n")

    satisfied = len(requirements) - len(missing)
    print(
        f"Requirements scan: total={len(requirements)}, "
        f"satisfied={satisfied}, missing_or_mismatch={len(missing)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
