"""
pfc — Python interface for PFC-JSONL compression.

PFC-JSONL is a high-performance compressor for structured log files (JSONL).
This package provides a thin Python wrapper around the pfc_jsonl binary.

Community Mode (no license key):
    All operations are free up to 5 GB per calendar day.
    Usage is tracked locally in ~/.pfc/usage.json — no network calls.

License keys for production use (>5 GB/day):
    https://github.com/ImpossibleForge/pfc-jsonl

Quick start:
    >>> import pfc
    >>> pfc.compress("app.jsonl", "app.pfc")
    >>> pfc.decompress("app.pfc", "app_restored.jsonl")
    >>> results = pfc.query("app.pfc", "2026-01-01T00:00:00", "2026-01-02T00:00:00")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ._core import PFCError, _find_binary, run

__version__ = "0.1.0"
__all__ = [
    "compress",
    "decompress",
    "query",
    "seek_blocks",
    "community_usage",
    "get_binary",
    "PFCError",
]


def get_binary() -> str:
    """Return the path to the pfc_jsonl binary being used.

    Useful for debugging which binary is picked up.

    Returns:
        Absolute path string.

    Raises:
        FileNotFoundError: if no binary is found.
    """
    return _find_binary()


def compress(
    input_path: str,
    output_path: str,
    *,
    level: str = "balanced",
    block_size_mb: Optional[int] = None,
    workers: Optional[int] = None,
    verbose: bool = False,
) -> None:
    """Compress a JSONL file to PFC format.

    Community Mode: counts input bytes toward the 5 GB/day limit.

    Args:
        input_path:    Path to the input .jsonl file (or "-" for stdin).
        output_path:   Path to write the compressed .pfc file.
        level:         Compression level: "fast", "balanced" (default), or "max".
        block_size_mb: Block size in MiB (must be a power of 2, e.g. 16, 32).
                       Defaults to the binary's built-in default.
        workers:       Number of parallel compression workers.
                       Defaults to the binary's auto-detection.
        verbose:       Print progress info from the binary.

    Raises:
        FileNotFoundError: if pfc_jsonl binary is not found.
        PFCError:          if compression fails.

    Example:
        >>> pfc.compress("logs/app.jsonl", "logs/app.pfc")
        >>> pfc.compress("big.jsonl", "big.pfc", level="max", workers=4)
    """
    args = ["compress", input_path, output_path, "--level", level]
    if block_size_mb is not None:
        args += ["--block-size", str(block_size_mb)]
    if workers is not None:
        args += ["--workers", str(workers)]
    if not verbose:
        args += ["--quiet"]
    run(args)


def decompress(
    input_path: str,
    output_path: str = "-",
    *,
    verbose: bool = False,
) -> None:
    """Decompress a PFC file back to JSONL.

    Community Mode: counts decompressed output bytes toward the 5 GB/day limit.

    Args:
        input_path:  Path to the .pfc file (or "-" for stdin).
        output_path: Path to write the restored .jsonl file.
                     Use "-" to write to stdout (default).
        verbose:     Print progress info from the binary.

    Raises:
        FileNotFoundError: if pfc_jsonl binary is not found.
        PFCError:          if decompression fails.

    Example:
        >>> pfc.decompress("logs/app.pfc", "logs/app_restored.jsonl")
    """
    args = ["decompress", input_path, output_path]
    if not verbose:
        args += ["--quiet"]
    run(args)


def query(
    pfc_path: str,
    from_ts: str,
    to_ts: str,
    output_path: str = "-",
    *,
    verbose: bool = False,
) -> None:
    """Decompress only the blocks matching a timestamp range.

    Block-level filtering: only blocks that overlap the given time range
    are decompressed. Much faster than full decompression for recent logs.

    Community Mode: counts decompressed output bytes toward the 5 GB/day limit.

    Args:
        pfc_path:    Path to the .pfc file.
        from_ts:     Start of the time range (ISO 8601 or Unix timestamp).
                     Example: "2026-01-01T00:00:00" or "1735689600"
        to_ts:       End of the time range (inclusive).
        output_path: Path to write the results. Use "-" for stdout (default).
        verbose:     Print block selection info from the binary.

    Raises:
        FileNotFoundError: if pfc_jsonl binary is not found.
        PFCError:          if the query fails.

    Example:
        >>> pfc.query("logs/app.pfc", "2026-01-15T08:00:00", "2026-01-15T09:00:00",
        ...           "logs/morning.jsonl")
    """
    args = ["query", pfc_path, "--from", from_ts, "--to", to_ts, "--out", output_path]
    if not verbose:
        args += ["--quiet"]
    run(args)


def seek_blocks(
    pfc_path: str,
    blocks: list[int],
    output_path: str = "-",
    *,
    verbose: bool = False,
) -> None:
    """Decompress specific blocks by index without reading the full file.

    This is the low-level primitive used by the DuckDB extension internally.
    Useful for building custom query layers on top of PFC files.

    Community Mode: counts decompressed output bytes toward the 5 GB/day limit.

    Args:
        pfc_path:    Path to the .pfc file.
        blocks:      List of 0-based block indices to decompress.
        output_path: Path to write the result. Use "-" for stdout (default).
        verbose:     Print seek info from the binary.

    Raises:
        FileNotFoundError: if pfc_jsonl binary is not found.
        PFCError:          if decompression fails.
        ValueError:        if blocks list is empty.

    Example:
        >>> pfc.seek_blocks("logs/app.pfc", [0, 3, 7], "logs/selected.jsonl")
    """
    if not blocks:
        raise ValueError("blocks list must not be empty")
    args = ["seek-blocks", pfc_path, "--blocks"] + [str(b) for b in blocks]
    args += ["--out", output_path]
    if not verbose:
        args += ["--quiet"]
    run(args)


def community_usage() -> dict:
    """Return today's Community Mode usage.

    Reads ~/.pfc/usage.json without invoking the binary.

    Returns:
        dict with keys:
            "date"            (str)  — today's date, e.g. "2026-04-04"
            "bytes_today"     (int)  — bytes processed today
            "bytes_remaining" (int)  — bytes remaining before the 5 GB limit
            "limit_gb"        (float) — daily limit in GB (always 5.0)
            "used_gb"         (float) — bytes_today converted to GB

    Example:
        >>> usage = pfc.community_usage()
        >>> print(f"Used {usage['used_gb']:.2f} GB of {usage['limit_gb']} GB today")
    """
    import time

    limit = 5 * 1024 ** 3
    usage_path = Path.home() / ".pfc" / "usage.json"
    today = time.strftime("%Y-%m-%d")

    bytes_today = 0
    try:
        if usage_path.exists():
            data = json.loads(usage_path.read_text(encoding="utf-8"))
            if data.get("date") == today:
                bytes_today = int(data.get("bytes_today", 0))
    except Exception:
        pass

    return {
        "date": today,
        "bytes_today": bytes_today,
        "bytes_remaining": max(0, limit - bytes_today),
        "limit_gb": 5.0,
        "used_gb": round(bytes_today / 1024 ** 3, 3),
    }
