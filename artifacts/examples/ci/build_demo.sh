#!/usr/bin/env bash
set -euo pipefail
outdir="artifacts/examples/ci/build/out"
mkdir -p "$outdir"
echo "hello-world-release-v1" > "$outdir/demo-artifact.txt"
