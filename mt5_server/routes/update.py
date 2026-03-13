import subprocess
from pathlib import Path
from typing import Iterable, Optional

import requests
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["update"])

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LOCAL_VERSION_FILES = (
    _REPO_ROOT / "VERSION",
    _REPO_ROOT / "version.txt",
)
_REMOTE_VERSION_URLS = (
    "https://raw.githubusercontent.com/Kacperpe/StockMarketCalendar/main/VERSION",
    "https://raw.githubusercontent.com/Kacperpe/StockMarketCalendar/main/version.txt",
)
_LOCALHOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}


def _read_first_non_empty(paths: Iterable[Path]) -> Optional[str]:
    for path in paths:
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if value:
            return value
    return None


def _read_local_version() -> str:
    return _read_first_non_empty(_LOCAL_VERSION_FILES) or "unknown"


def _read_remote_version() -> str:
    errors = []
    for url in _REMOTE_VERSION_URLS:
        try:
            response = requests.get(url, timeout=5)
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc}")
            continue

        if response.status_code != 200:
            errors.append(f"{url}: HTTP {response.status_code}")
            continue

        value = response.text.strip()
        if value:
            return value
        errors.append(f"{url}: empty response")

    raise RuntimeError("; ".join(errors) or "remote version unavailable")


def _is_local_request(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in _LOCALHOSTS or host.startswith("127.")


@router.get("/api/check-update")
def check_update():
    local = _read_local_version()
    remote = None
    error = None
    try:
        remote = _read_remote_version()
    except Exception as exc:
        error = str(exc)

    return {
        "local": local,
        "remote": remote,
        "update_available": bool(remote and remote != local),
        "error": error,
    }


@router.post("/api/update")
def update_app(request: Request):
    if not _is_local_request(request):
        raise HTTPException(status_code=403, detail="update is allowed only from localhost")

    try:
        result = subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError:
        return {"success": False, "output": "git command not found in PATH"}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "git pull timed out"}

    lines = []
    if result.stdout:
        lines.append(result.stdout.strip())
    if result.stderr:
        lines.append(result.stderr.strip())
    output = "\n".join(line for line in lines if line).strip()

    return {
        "success": result.returncode == 0,
        "output": output or "no output",
        "local": _read_local_version(),
    }
