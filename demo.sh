#!/usr/bin/env bash
# Demo: generate synthetic data, build the graph, run one query via each
# method, then run the full evaluation. Uses the project virtualenv.
set -e
cd "$(dirname "$0")"
PY=.venv/bin/python
if [ ! -x "$PY" ]; then
  echo "No .venv found. Create one first:"
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi
echo "=== 1. generate synthetic data ==="
$PY data/generate_synthetic.py
echo
echo "=== 2. build the context graph ==="
$PY -m src.ingest
echo
echo "=== 3. sample query (graph method) ==="
$PY -m src.query --question "Who asked for quarterly billing at Harborview Medical?"
echo
echo "=== 4. sample query (baseline method) ==="
$PY -m src.query --question "Who asked for quarterly billing at Harborview Medical?" --method baseline
echo
echo "=== 5. evaluation ==="
$PY -m src.evaluate
