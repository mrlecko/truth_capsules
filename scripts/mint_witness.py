#!/usr/bin/env python3
"""
mint_witness.py — Cookie-cutter to scaffold a new executable witness example.

Creates:
  - capsules/<domain>.<name>_v1.yaml
  - artifacts/examples/<name>_pass.json
  - artifacts/examples/<name>_fail.json
  - tests/test_<name>_witness.py

Design:
  * Deterministic & offline
  * Env-first policy knobs
  * SKIP semantics
  * Focused runner filters (--capsule/--witness)

Usage:
  python mint_witness.py --domain llm --name myrule \
    --title "My Rule" \
    --statement "Do X or SKIP." \
    --witness-name check_myrule \
    [--force]

After generating:
  - Edit capsule witness code to implement your rule
  - Run:
      python scripts/run_witnesses.py capsules --capsule <domain>.<name>_v1 --witness <witness-name> --json
  - Add real fixtures and tune thresholds.

Author: Auto-generated
Updated: 2025-11-09T15:36:13Z
"""

import argparse, pathlib, sys, datetime, json, textwrap

def slug(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in s.strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, help="Domain (e.g., llm, pr_review, ops)")
    ap.add_argument("--name", required=True, help="Short name (slug) for the rule")
    ap.add_argument("--title", required=False, default="", help="Human title")
    ap.add_argument("--statement", required=False, default="", help="One-sentence rule")
    ap.add_argument("--witness-name", required=False, default="check_rule_compliance", help="Unique witness function name")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = ap.parse_args()

    domain = slug(args.domain)
    name = slug(args.name)
    wid = slug(args.witness_name)
    cid = f"{domain}.{name}_v1"

    # Paths
    cap_path = pathlib.Path("capsules") / f"{domain}.{name}_v1.yaml"
    ex_dir = pathlib.Path("artifacts/examples")
    test_path = pathlib.Path("tests") / f"test_{name}_witness.py"

    # Prepare dirs
    cap_path.parent.mkdir(parents=True, exist_ok=True)
    ex_dir.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.force:
        for p in (cap_path, ex_dir / f"{name}_pass.json", ex_dir / f"{name}_fail.json", test_path):
            if p.exists():
                print(f"ERROR: {p} exists. Use --force to overwrite.", file=sys.stderr)
                sys.exit(2)

    # Fixtures
    pass_json = {
        "text": "This sentence is supported [ok]. Another supported claim [ok].",
        "items": []
    }
    fail_json = {
        "text": "Two sentences without the [ok] evidence marker. Another claim without support.",
        "items": []
    }

    (ex_dir / f"{name}_pass.json").write_text(json.dumps(pass_json, indent=2), encoding="utf-8")
    (ex_dir / f"{name}_fail.json").write_text(json.dumps(fail_json, indent=2), encoding="utf-8")

    created = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    title = args.title or f"{name.title().replace('_',' ')} (Executable Witness)"
    statement = args.statement or "Ensure at least a threshold fraction of declarative sentences have explicit evidence markers."

    witness_code = textwrap.dedent(f'''\
    import os, sys, json, pathlib, re

    WITNESS = "{wid}"

    # 1) Resolve inputs from env (OS env overrides capsule env)
    p = pathlib.Path(os.getenv("INPUT_PATH","")).resolve()
    if not p.exists():
        print(json.dumps({{"witness":WITNESS,"status":"FAIL","reason":"file-not-found","inputs":{{"path":str(p)}}}}))
        sys.exit(1)

    # 2) Policy-controlled SKIP (optional)
    if os.getenv("MODE","").lower() == "opinion":
        print(json.dumps({{"witness":WITNESS,"status":"SKIP","reason":"policy-skip","inputs":{{"path":str(p)}}}}))
        sys.exit(0)

    # 3) Load & validate input
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({{"witness":WITNESS,"status":"FAIL","reason":"bad-json","error":str(e),"inputs":{{"path":str(p)}}}}))
        sys.exit(1)

    # 4) Example heuristic: coverage of "[ok]" markers per declarative sentence
    text = (data.get("text") or "").strip()
    THRESHOLD = float(os.getenv("THRESHOLD","0.6"))

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\\s+', text) if s.strip()]
    total = len(sentences)
    covered = sum(1 for s in sentences if "[ok]" in s)

    if total == 0:
        print(json.dumps({{"witness":WITNESS,"status":"SKIP","reason":"no-declaratives","inputs":{{"path":str(p)}}}}))
        sys.exit(0)

    coverage = covered/total
    if coverage < THRESHOLD:
        print(json.dumps({{"witness":WITNESS,"status":"FAIL","reason":"coverage-too-low","coverage":coverage,"min":THRESHOLD,"inputs":{{"path":str(p)}}}}))
        sys.exit(1)

    out = {{
      "witness": WITNESS,
      "status": "PASS",
      "coverage": coverage,
      "totals": {{"sentences": total, "covered": covered}},
      "inputs": {{"path": str(p)}}
    }}
    print(json.dumps(out, indent=2))
    sys.exit(0)
    ''')

    capsule = f'''id: {cid}
version: 1.0.0
domain: {domain}
title: {title}
statement: >
  {statement}
assumptions:
- Using a lightweight coverage heuristic with explicit evidence markers.
pedagogy:
- kind: Socratic
  text: Which statements require explicit evidence, and how is it shown?
- kind: Aphorism
  text: Evidence disciplines decisions.
witnesses:
  - name: {wid}
    language: python
    env:
      INPUT_PATH: artifacts/examples/{name}_pass.json
      THRESHOLD: "0.6"
      MODE: ""   # set MODE=opinion to SKIP
    code: |-
{witness_code.replace("\n", "\n      ")}
provenance:
  schema: provenance.v1
  author: Mint Witness Script
  org: Truth Capsules Demo
  license: MIT
  source_url: https://example.com/truth-capsules
  created: '{created}'
  updated: '{created}'
  review:
    status: draft
    reviewers: []
    last_reviewed: null
applies_to: [conversation, ci]
security:
  sensitivity: low
  notes: Zero-network; uses local fixtures only.
'''

    cap_path.write_text(capsule, encoding="utf-8")

    test_code = f'''import json, subprocess, os

RUN = ["python", "scripts/run_witnesses.py", "capsules",
       "--capsule", "{cid}",
       "--witness", "{wid}", "--json"]

def _run(extra_env=None):
    env = os.environ.copy()
    if extra_env: env.update(extra_env)
    p = subprocess.run(RUN, capture_output=True, text=True, env=env, timeout=10)
    return p.returncode, json.loads(p.stdout)

def _extract(res):
    cap = res[0]
    return cap["status"], cap["witness_results"][0]["status"]

def test_pass():
    rc, data = _run()
    cap, wit = _extract(data)
    assert rc == 0 and cap == "GREEN" and wit == "PASS"

def test_fail():
    rc, data = _run({{"INPUT_PATH": "artifacts/examples/{name}_fail.json"}})
    cap, wit = _extract(data)
    assert rc == 1 and cap == "RED" and wit == "FAIL"

def test_skip():
    rc, data = _run({{"MODE": "opinion"}})
    cap, wit = _extract(data)
    assert rc == 0 and cap == "SKIP" and wit == "SKIP"
'''
    test_path.write_text(test_code, encoding="utf-8")

    print("Created:")
    print("  ", cap_path)
    print("  ", ex_dir / f"{name}_pass.json")
    print("  ", ex_dir / f"{name}_fail.json")
    print("  ", test_path)
    print("\\nNext steps:")
    print(f"  python scripts/run_witnesses.py capsules --capsule {cid} --witness {wid} --json")
    print("  pytest -v", test_path)

if __name__ == "__main__":
    main()
