# pfc-jsonl · Python Package

Python interface for **PFC-JSONL** — high-performance compression for structured log files (JSONL), with block-level timestamp filtering.

```
pip install pfc-jsonl
```

> **Requires the `pfc_jsonl` binary.** Install it separately — see [below](#install-the-binary).

---

## What is PFC-JSONL?

PFC-JSONL compresses JSONL log files **25–37% smaller than gzip/zstd** on typical log data. It stores a timestamp index alongside each file, enabling fast time-range queries without full decompression.

| Operation | Description |
|-----------|-------------|
| `compress` | JSONL → `.pfc` (with timestamp index) |
| `decompress` | `.pfc` → JSONL |
| `query` | Decompress only blocks matching a time range |
| `seek_blocks` | Decompress specific blocks by index (DuckDB primitive) |

---

## Quick Start

```python
import pfc

# Compress
pfc.compress("logs/app.jsonl", "logs/app.pfc")

# Decompress
pfc.decompress("logs/app.pfc", "logs/app_restored.jsonl")

# Query by time range — only decompresses matching blocks
pfc.query("logs/app.pfc",
          from_ts="2026-01-15T08:00:00",
          to_ts="2026-01-15T09:00:00",
          output_path="logs/morning.jsonl")

# Check Community Mode usage
usage = pfc.community_usage()
print(f"Used {usage['used_gb']:.2f} GB of {usage['limit_gb']} GB today")
```

---

## Install the Binary

The Python package is a thin wrapper — the compression engine is the `pfc_jsonl` binary.

**Linux (x64):**
```bash
curl -L https://github.com/ImpossibleForge/pfc-jsonl/releases/latest/download/pfc_jsonl-linux-x64 \
     -o pfc_jsonl && chmod +x pfc_jsonl && sudo mv pfc_jsonl /usr/local/bin/
```

**macOS:** Coming soon.

**Windows:** No native binary available. Use WSL2 or a Linux machine.

**Custom location:** Set the `PFC_BINARY` environment variable:
```bash
export PFC_BINARY=/opt/tools/pfc_jsonl
```

Verify:
```bash
pfc_jsonl --help
```

---

## API Reference

### `pfc.compress(input_path, output_path, *, level="default", block_size_mb=None, workers=None, verbose=False)`

Compress a JSONL file to PFC format.

```python
pfc.compress("logs/app.jsonl", "logs/app.pfc")
pfc.compress("big.jsonl", "big.pfc", level="max", workers=4)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `level` | `"default"` | `"fast"`, `"default"`, or `"max"` (also accepts `1`-`5`) |
| `block_size_mb` | auto | Block size in MiB (power of 2, e.g. 16, 32) |
| `workers` | auto | Parallel compression workers |
| `verbose` | `False` | Print progress from binary |

---

### `pfc.decompress(input_path, output_path="-", *, verbose=False)`

Decompress a PFC file back to JSONL.

```python
pfc.decompress("logs/app.pfc", "logs/app_restored.jsonl")
```

---

### `pfc.query(pfc_path, from_ts, to_ts, output_path="-")`

Decompress only the blocks matching a timestamp range.

```python
pfc.query("logs/app.pfc",
          from_ts="2026-01-15T08:00:00",
          to_ts="2026-01-15T09:00:00",
          output_path="logs/morning.jsonl")
```

Timestamps can be ISO 8601 strings or Unix epoch integers (as strings).

---

### `pfc.seek_blocks(pfc_path, blocks, output_path="-", *, verbose=False)`

Decompress specific blocks by index. Used internally by the DuckDB extension.

```python
pfc.seek_blocks("logs/app.pfc", [0, 3, 7], "logs/selected.jsonl")
```

---

### `pfc.community_usage() -> dict`

Return today's Community Mode usage without invoking the binary.

```python
usage = pfc.community_usage()
# {
#   "date": "2026-04-04",
#   "bytes_today": 1073741824,
#   "bytes_remaining": 4294967296,
#   "limit_gb": 5.0,
#   "used_gb": 1.0
# }
```

---

### `pfc.get_binary() -> str`

Return the path to the `pfc_jsonl` binary being used.

```python
print(pfc.get_binary())  # /usr/local/bin/pfc_jsonl
```

---

## Community Mode

PFC-JSONL includes a built-in free tier called **Community Mode** — no account, no signup, no license key required:

- All operations (compress, decompress, query, seek-blocks) are **free up to 5 GB/day**
- `compress` counts **input bytes**; `decompress`, `query`, `seek-blocks` count **decompressed output bytes**
- Usage is tracked locally in `~/.pfc/usage.json` — **no network calls**
- Resets every calendar day (midnight UTC)

For production use exceeding 5 GB/day, contact: **impossibleforge@gmail.com**

---

## Error Handling

```python
import pfc
from pfc import PFCError

try:
    pfc.compress("missing.jsonl", "out.pfc")
except FileNotFoundError as e:
    print(f"Binary not found: {e}")
except PFCError as e:
    print(f"Compression failed (exit {e.returncode}): {e.stderr}")
```

---

## Integration with Fluent Bit

Use [pfc-fluentbit](https://github.com/ImpossibleForge/pfc-fluentbit) to receive logs from Fluent Bit and compress them automatically.

## Integration with DuckDB

Use the [pfc DuckDB extension](https://github.com/ImpossibleForge/pfc-duckdb) to query `.pfc` files directly with SQL:

> **Status:** Submitted — pending review ([PR #1679](https://github.com/duckdb/community-extensions/pull/1679)). Once available:

```sql
-- Once available in DuckDB community extensions:
INSTALL pfc FROM community;
LOAD pfc;
LOAD json;
SELECT line->>'$.level' AS level, line->>'$.message' AS msg
FROM read_pfc_jsonl('logs/app.pfc')
WHERE line->>'$.level' = 'ERROR';
```

---

## License

MIT — see [LICENSE](LICENSE)

Binary releases are proprietary. See [pfc-jsonl releases](https://github.com/ImpossibleForge/pfc-jsonl/releases) for terms.
