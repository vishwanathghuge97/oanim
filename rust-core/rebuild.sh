#!/bin/sh
# Rebuild oanim_core (Rust splat backend). Everything stays inside exp/.
# - Toolchain: tmp/rustup + tmp/cargo (no system rust, no ~/.cargo writes)
# - Linker: zig bundled in .venv (no system gcc)
# - Build Python (headers): tmp/uv-python (system python has no -devel headers)
# - Output wheel goes to tmp/wheels, installed into .venv (abi3: works on 3.8+)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export RUSTUP_HOME="$ROOT/tmp/rustup" CARGO_HOME="$ROOT/tmp/cargo"
export TMPDIR="$ROOT/tmp" PIP_CACHE_DIR="$ROOT/tmp/pip-cache"
export PATH="$CARGO_HOME/bin:$PATH"
BUILD_PY="$ROOT/tmp/uv-python/cpython-3.14.7-linux-x86_64-gnu/bin/python3"
"$ROOT/.venv/bin/maturin" build --release -i "$BUILD_PY" --out "$ROOT/tmp/wheels"
"$ROOT/.venv/bin/pip" install --no-input --force-reinstall "$ROOT"/tmp/wheels/oanim_core-*.whl
"$ROOT/.venv/bin/python" bench/bench_splat.py
