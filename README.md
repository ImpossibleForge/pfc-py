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
```

---

## Install the Binary

The Python package is a thin wrapper — the compression engine is the `pfc_jsonl` binary.

**Linux (x64):**
```bash
curl -L https://github.com/ImpossibleForge/pfc-jsonl/releases/latest/download/pfc_jsonl-linux-x64 \
     -o pfc_jsonl && chmod +x pfc_jsonl && sudo mv pfc_jsonl /usr/local/bin/
```

**macOS (Apple Silicon M1/M2/M3/M4):**
```bash
curl -L https://github.com/ImpossibleForge/pfc-jsonl/releases/latest/download/pfc_jsonl-macos-arm64 \
     -o pfc_jsonl && chmod +x pfc_jsonl && sudo mv pfc_jsonl /usr/local/bin/
```
macOS Intel (x64): coming soon.

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

---

### `pfc.get_binary() -> str`

Return the path to the `pfc_jsonl` binary being used.

```python
print(pfc.get_binary())  # /usr/local/bin/pfc_jsonl
```

---

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

```sql
INSTALL pfc FROM community;
LOAD pfc;
LOAD json;
SELECT line->>'$.level' AS level, line->>'$.message' AS msg
FROM read_pfc_jsonl('logs/app.pfc')
WHERE line->>'$.level' = 'ERROR';
```

---


## Related repos

- [pfc-jsonl](https://github.com/ImpossibleForge/pfc-jsonl) — core binary (compress/decompress/query)
- [pfc-gateway](https://github.com/ImpossibleForge/pfc-gateway) — HTTP REST gateway — ingest + query, no DuckDB
- [pfc-fluentbit](https://github.com/ImpossibleForge/pfc-fluentbit) — live Fluent Bit → PFC pipeline
- [pfc-vector](https://github.com/ImpossibleForge/pfc-vector) — high-performance Rust ingest daemon for Vector.dev and Telegraf
- [pfc-migrate](https://github.com/ImpossibleForge/pfc-migrate) — one-shot export and archive conversion
- [pfc-duckdb](https://github.com/ImpossibleForge/pfc-duckdb) — DuckDB extension for SQL queries on PFC files
- [pfc-otel-collector](https://github.com/ImpossibleForge/pfc-otel-collector) — OpenTelemetry OTLP/HTTP log exporter
- [pfc-kafka-consumer](https://github.com/ImpossibleForge/pfc-kafka-consumer) — Kafka / Redpanda consumer → PFC

---

## License

pfc-py (this repository) is released under the MIT License — see [LICENSE](LICENSE).

The PFC-JSONL binary (`pfc_jsonl`) is proprietary software — free for personal and open-source use. Commercial use requires a license: [info@impossibleforge.com](mailto:info@impossibleforge.com)