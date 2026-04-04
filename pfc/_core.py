"""
pfc._core — Binary finder and subprocess runner.

Locates the pfc_jsonl binary and provides a thin wrapper
for calling it as a subprocess. No algorithm logic here.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_binary() -> str:
    """Locate the pfc_jsonl binary.

    Search order:
    1. PFC_BINARY environment variable
    2. PATH (shutil.which)
    3. Common install locations
    4. Same directory as this package

    Raises:
        FileNotFoundError: if the binary cannot be found.
    """
    # 1. Explicit override
    env_path = os.environ.get("PFC_BINARY")
    if env_path and Path(env_path).is_file():
        return env_path

    # 2. PATH
    binary_name = "pfc_jsonl.exe" if sys.platform == "win32" else "pfc_jsonl"
    found = shutil.which(binary_name)
    if found:
        return found

    # 3. Common locations
    candidates = [
        Path("/usr/local/bin/pfc_jsonl"),
        Path("/usr/bin/pfc_jsonl"),
        Path.home() / ".local" / "bin" / "pfc_jsonl",
        Path.home() / "bin" / "pfc_jsonl",
    ]
    for p in candidates:
        if p.is_file():
            return str(p)

    # 4. Package directory (for bundled installs)
    pkg_dir = Path(__file__).parent
    local = pkg_dir / binary_name
    if local.is_file():
        return str(local)

    raise FileNotFoundError(
        "pfc_jsonl binary not found.\n\n"
        "Install it first:\n"
        "  Linux:   curl -L https://github.com/ImpossibleForge/pfc-jsonl/releases/"
        "latest/download/pfc_jsonl-linux-x64 -o pfc_jsonl && chmod +x pfc_jsonl && "
        "sudo mv pfc_jsonl /usr/local/bin/\n"
        "  macOS:   coming soon\n"
        "  Windows: download pfc_jsonl-windows-x64.exe from the releases page\n\n"
        "Or set the PFC_BINARY environment variable to the binary path."
    )


def run(args: list, capture_stdout: bool = False) -> subprocess.CompletedProcess:
    """Run pfc_jsonl with the given argument list.

    Args:
        args:           Argument list, e.g. ["compress", "in.jsonl", "out.pfc"]
        capture_stdout: If True, capture stdout instead of letting it through.

    Returns:
        CompletedProcess instance.

    Raises:
        FileNotFoundError: if binary is missing.
        PFCError:          if the binary exits with a non-zero status.
    """
    binary = _find_binary()
    cmd = [binary] + args
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE if capture_stdout else None,
        stderr=subprocess.PIPE,
        text=False,
    )
    if result.returncode != 0:
        stderr_msg = result.stderr.decode(errors="replace").strip() if result.stderr else ""
        raise PFCError(
            f"pfc_jsonl exited with code {result.returncode}",
            returncode=result.returncode,
            stderr=stderr_msg,
        )
    return result


class PFCError(RuntimeError):
    """Raised when pfc_jsonl exits with a non-zero status."""

    def __init__(self, message: str, returncode: int = -1, stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr

    def __str__(self):
        base = super().__str__()
        if self.stderr:
            return f"{base}\n  stderr: {self.stderr}"
        return base
