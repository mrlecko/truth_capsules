# NEW_WITNESS_EXAMPLES — Minting Guide (Perfect Process)

This guide is a **turnkey playbook** for creating a brand-new executable witness example:
from capsule YAML to runnable fixtures, tests, and CI. It encodes best practices we established:
**determinism**, **env-overrides**, **SKIP semantics**, and **focused runner filters**.

---

## 0) Mental model

- A **capsule** is a small YAML object capturing a rule/policy plus pedagogy.
- A **witness** is executable code embedded in the capsule that **verifies** the rule.
- The **runner** executes witnesses and reports `PASS / FAIL / SKIP` as JSON.
- **Deterministic & offline**: witnesses should not make network calls.

---

## 1) Choose the rule and scope

**Write one sentence** that an org would gladly gate on. Examples:
- “PR reviews must name detected risk areas and include a mitigation for each.”
- “Factual answers must provide citations covering ≥60% of declarative sentences.”

Decide:
- **Inputs** (keep them local in `artifacts/examples/`)
- **Policy knobs** (thresholds/allowlists via `env:` + OS env override)
- **SKIP** condition (when the rule is inapplicable)

---

## 2) Create the capsule

**Path:** `capsules/<domain>.<name>_v1.yaml`  
**ID:** must match filename stem.

Scaffold:
```yaml
id: <domain>.<name>_v1
version: 1.0.0
domain: <domain>
title: <Short human title>
statement: >
  <One-sentence rule the witness will verify.>
assumptions:
- <Optional assumption>
pedagogy:
- kind: Socratic
  text: <One question that elicits correct reasoning>
- kind: Aphorism
  text: <Short sticky maxim>
witnesses:
  - name: <unique_witness_name>
    language: python
    env:
      INPUT_PATH: artifacts/examples/<name>_pass.json
      THRESHOLD: "0.6"
      MODE: ""   # set e.g. MODE=opinion to SKIP
    code: |-
      # See witness template below
provenance:
  schema: provenance.v1
  author: <Your name>
  org: Truth Capsules Demo
  license: MIT
  source_url: https://example.com/truth-capsules
  created: '2025-11-09T15:36:13Z'
  updated: '2025-11-09T15:36:13Z'
  review:
    status: draft
    reviewers: []
    last_reviewed: null
applies_to: [conversation, ci]
security:
  sensitivity: low
  notes: Zero-network; reads only example fixtures.
```

---

## 3) Prepare fixtures (PASS / FAIL / SKIP)

Create three inputs to show the whole semantic surface:

```
artifacts/examples/
├── <name>_pass.json  # should PASS
├── <name>_fail.json  # should FAIL
└── <name>_skip.json  # or reuse pass + run with MODE=opinion for SKIP
```

---

## 4) Witness code template (drop-in)

This Python template enforces **OS env precedence**, **SKIP** semantics, and prints **one JSON** object.

```python
import os, sys, json, pathlib, re

WITNESS = "<unique_witness_name>"

# 1) Resolve inputs from env (OS env overrides capsule env)
p = pathlib.Path(os.getenv("INPUT_PATH","")).resolve()
if not p.exists():
    print(json.dumps({"witness":WITNESS,"status":"FAIL","reason":"file-not-found","inputs":{"path":str(p)}}))
    sys.exit(1)

# 2) Policy-controlled SKIP (optional)
if os.getenv("MODE","").lower() == "opinion":
    print(json.dumps({"witness":WITNESS,"status":"SKIP","reason":"policy-skip","inputs":{"path":str(p)}}))
    sys.exit(0)

# 3) Load & validate input
try:
    data = json.loads(p.read_text(encoding="utf-8"))
except Exception as e:
    print(json.dumps({"witness":WITNESS,"status":"FAIL","reason":"bad-json","error":str(e),"inputs":{"path":str(p)}}))
    sys.exit(1)

# 4) Example fields and simple heuristic
text = (data.get("text") or "").strip()
THRESHOLD = float(os.getenv("THRESHOLD","0.6"))

# Very light sentence segmentation
sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
covered = sum(1 for s in sentences if "[ok]" in s)  # example "evidence" marker
total = len(sentences)

# 5) Decide SKIP if no declaratives
if total == 0:
    print(json.dumps({"witness":WITNESS,"status":"SKIP","reason":"no-declaratives","inputs":{"path":str(p)}}))
    sys.exit(0)

coverage = covered/total
# 6) Threshold gate
if coverage < THRESHOLD:
    print(json.dumps({"witness":WITNESS,"status":"FAIL","reason":"coverage-too-low","coverage":coverage,"min":THRESHOLD,"inputs":{"path":str(p)}}))
    sys.exit(1)

# 7) PASS with helpful metrics
out = {
  "witness": WITNESS,
  "status": "PASS",
  "coverage": coverage,
  "totals": {"sentences": total, "covered": covered},
  "inputs": {"path": str(p)}
}
print(json.dumps(out, indent=2))
sys.exit(0)
```

---

## 5) Run with filters

```bash
# PASS
python scripts/run_witnesses.py capsules   --capsule <domain>.<name>_v1   --witness <unique_witness_name>   --json

# FAIL
INPUT_PATH=artifacts/examples/<name>_fail.json python scripts/run_witnesses.py capsules   --capsule <domain>.<name>_v1   --witness <unique_witness_name>   --json

# SKIP
MODE=opinion python scripts/run_witnesses.py capsules   --capsule <domain>.<name>_v1   --witness <unique_witness_name>   --json
```

If you see `"witness_results": []`, the filter didn’t match your `id`/`name`. Check strings exactly.

---

## 6) Tests (pytest)

Create `tests/test_<name>_witness.py`:

```python
import json, subprocess, os

RUN = ["python", "scripts/run_witnesses.py", "capsules",
       "--capsule", "<domain>.<name>_v1",
       "--witness", "<unique_witness_name>", "--json"]

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
    rc, data = _run({ "INPUT_PATH": "artifacts/examples/<name>_fail.json" })
    cap, wit = _extract(data)
    assert rc == 1 and cap == "RED" and wit == "FAIL"

def test_skip():
    rc, data = _run({ "MODE": "opinion" })
    cap, wit = _extract(data)
    assert rc == 0 and cap == "SKIP" and wit == "SKIP"
```

---

## 7) Makefile shortcuts (optional)

```make
witness-<name>-pass:
	python scripts/run_witnesses.py capsules --capsule <domain>.<name>_v1 --witness <unique_witness_name> --json
witness-<name>-fail:
	INPUT_PATH=artifacts/examples/<name>_fail.json \
	python scripts/run_witnesses.py capsules --capsule <domain>.<name>_v1 --witness <unique_witness_name> --json
witness-<name>-skip:
	MODE=opinion \
	python scripts/run_witnesses.py capsules --capsule <domain>.<name>_v1 --witness <unique_witness_name> --json
```

---

## 8) Docs & CI

- Add a short page: `docs/WITNESS_<NAME>.md` (what/why/how/who/how-to-run/security/outputs).
- Link it from README.
- Add a GH Action job to run the witness with real inputs & env on PRs.

---

## 9) Provenance, digests, signing

```bash
python scripts/capsule_linter.py capsules
python scripts/capsule_digest.py capsules
python scripts/capsule_sign.py capsules --key keys/my_key.pem  # optional
python scripts/capsule_verify.py capsules
```

---

## 10) Definition of Done

- [ ] Capsule schema OK; ID/filename match.
- [ ] PASS/FAIL/SKIP fixtures committed under `artifacts/examples/`.
- [ ] Runner filters produce the expected statuses.
- [ ] Tests PASS locally (pytest).
- [ ] README + doc page linked.
- [ ] Digests updated; signatures verified (if enabled).
- [ ] CI job gates appropriately.

---

## Reference: Citation Required (full)

Use this as a working exemplar; adapt nouns & thresholds, keep the patterns:
- **Env-first knobs**, **SKIP policy**, **compact JSON**, **no-network**, **clear metrics**.

```yaml
id: llm.citation_required_v1
version: 1.0.0
domain: llm
title: Citations required
statement: Answers must include at least one citation or abstain.
assumptions:
- Operating in a general context
pedagogy:
- kind: Socratic
  text: What evidence supports this claim?
- kind: Aphorism
  text: Cite or abstain.
witnesses:
  - name: citations_cover_claims
    language: python
    env:
      ANSWER_PATH: artifacts/examples/answer_with_citation.json
      COVERAGE_MIN: "0.6"
      DIVERSITY_MAX: "0.7"
      ALLOWLIST: "doi.org,arxiv.org,acm.org,ieee.org,nature.com,sciencemag.org,gov,edu"
      DOC_CLASS: ""
    code: |-
      <omitted for brevity — see your repo copy>
provenance:
  schema: provenance.v1
  author: John Macgregor
  org: Truth Capsules Demo
  license: MIT
  source_url: https://example.com/truth-capsules
  created: '2025-11-07T03:53:50.511776Z'
  updated: '2025-11-07T03:56:05.351404Z'
  review:
    status: draft
    reviewers: []
    last_reviewed: null
  signing:
    method: ed25519
    key_id: null
    pubkey: null
    digest: 0a51607ced8bd646d4a3bcaf8fa3c8ef4c5519afe87615669c6ad389d725cb39
    signature: null
applies_to:
- conversation
- code_assistant
- ci
security:
  sensitivity: low
  notes: ''
```
