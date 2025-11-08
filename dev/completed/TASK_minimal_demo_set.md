Awesome-here’s a complete drop-in **DEMOS.md** plus the exact helper files you asked for:

---

# DEMOS.md

**Truth Capsules v1 - Show & Tell Demos**

This guide gives you copy-paste demos that prove the value of capsules:

1. **Cognitive Upgrade A/B** (baseline vs. capsule)
2. **Executable Witness** (in-loop & sandboxed)
3. **Knowledge-Graph Export + SHACL validation**
4. **One-command happy path** (`make demo`)
5. **Security: 10-line Docker run profile**

> Prereqs: Python 3.10+, `pip install -r requirements.txt`, [`llm`](https://llm.datasette.io) installed and configured (`OPENAI_API_KEY` set).
> Repo paths assumed from project root.

---

## 0) Add the demo assets (once)

Create these new files (exact contents below in **Appendix**):

* `Makefile`
* `fragments/citation_capsule.md`
* `schemas/psa2.schema.json`
* `schemas/judge.schema.json`
* `scripts/witness_validate_capsule.py`        (in-loop tool)
* `scripts/witness_runner.py`                  (offline sandbox witness)
* `scripts/ab_run.sh`                          (A/B + judge)
* `scripts/export_kg.py`                       (YAML → Turtle)
* `shacl/truthcapsule.shacl.ttl`               (SHACL shapes)
* `scripts/run_sandboxed.sh`                   (Docker sandbox runner)

Create output folder:

```bash
mkdir -p artifacts/out
```

---

## 1) A/B Cognitive Upgrade (Baseline vs Capsule)

**What this shows:** same model + same question → **capsule** (Socratic + aphorisms + acceptance + schema) produces measurably better structure and evidence.

Run:

```bash
bash scripts/ab_run.sh
```

This writes:

* `artifacts/out/A.json`  - baseline
* `artifacts/out/B.json`  - capsule-inflated
* `artifacts/out/judge.json` - rubric score & **verdict**

**Expected:** B wins on Structure/Evidence/SelfCheck.
Sample `judge.json` (illustrative):

```json
{
  "Structure": 5,
  "Evidence": 4,
  "PII": 5,
  "SelfCheck": 4,
  "Notes": "B includes plan, citations and explicit self-check; A missed citations.",
  "Verdict": "B wins"
}
```

---

## 2) Executable Witness (in-loop & sandboxed)

### 2a) In-loop tool call (visible with `--td`)

```bash
llm --sf fragments/citation_capsule.md \
  --functions "$(cat scripts/witness_validate_capsule.py)" \
  --td \
  'Therac-25: Return only JSON matching the schema; then CALL validate_capsule(JSON) and include its result as {"Witness":{"ok":bool,"errors":[...]}}' \
  --schema schemas/psa2.schema.json \
  > artifacts/out/C.json
```

Look for a line like:

```
Tool call: validate_capsule({...})
  {"ok": true, "errors": []}
```

### 2b) Sandbox the witness offline (no-net, RO FS, caps)

```bash
bash scripts/run_sandboxed.sh artifacts/out/B.json
```

**Expected:** prints `SANDBOX WITNESS: PASS` or errors. This runs **only** the witness checker inside a constrained container-no API keys or network.

---

## 3) Knowledge-Graph Export + SHACL

Export all `capsules/*.yaml` → Turtle + validate with SHACL:

```bash
python scripts/export_kg.py \
  --capsules-dir capsules \
  --out-turtle artifacts/out/capsules.ttl

pyshacl -s shacl/truthcapsule.shacl.ttl \
  -m -f human-readable \
  artifacts/out/capsules.ttl
```

**Expected:** SHACL report ends with `Conforms: True`.

**Three SPARQL queries** to try (e.g., in RDF tooling; copy from Appendix §E):

* Q1: Capsules by domain/title
* Q2: Capsules covering a specific `appliesTo` context
* Q3: Capsules missing signature data (quick health check)

---

## 4) One-command happy path

```bash
make demo
```

This runs: baseline → capsule → judge → witness (in-loop) → KG export → SHACL.
At the end, it prints the artifact paths and the judge verdict.

---

## 5) Security - 10-line Docker run profile

Use this profile to run **witnesses** in isolation (details in Appendix §F).
Already wired by `scripts/run_sandboxed.sh`.

---

## Troubleshooting

* **Schema errors:** The model must output **only** a JSON object; try `--no-stream` or lower temperature (`llm -o temperature 0.2`).
* **llm not found:** `pipx install llm` or see llm docs.
* **pySHACL missing:** `pip install pyshacl rdflib pyyaml`.
* **Windows:** Use WSL or convert `.sh` to PowerShell.

---

# Appendix - Exact files

## A) `Makefile`

```make
MODEL ?= gpt-4o-mini
export LLM_MODEL=$(MODEL)

BASE=A.json
CAPS=B.json
JUDGE=judge.json
WITC=C.json
TTL=artifacts/out/capsules.ttl

.PHONY: demo baseline capsule judge witness kg shacl clean

baseline:
	llm 'What caused the Therac-25 accidents? Return only a JSON object with keys: Objective, Assumptions, Plan, Evidence, Citations, Final, SelfCheck' \
	  --schema schemas/psa2.schema.json \
	  > artifacts/out/$(BASE)

capsule:
	llm --sf fragments/citation_capsule.md \
	  'What caused the Therac-25 accidents? Return only the JSON object.' \
	  --schema schemas/psa2.schema.json \
	  > artifacts/out/$(CAPS)

judge:
	llm --schema schemas/judge.schema.json \
	  "Compare two JSON answers (A,B) with 0–5 scores for Structure,Evidence,PII,SelfCheck and return one JSON object. A=$$(cat artifacts/out/$(BASE)) B=$$(cat artifacts/out/$(CAPS))" \
	  > artifacts/out/$(JUDGE)

witness:
	llm --sf fragments/citation_capsule.md \
	  --functions "$$(cat scripts/witness_validate_capsule.py)" \
	  --td \
	  'Therac-25: Return only JSON (schema), then CALL validate_capsule(JSON) and include its result as {"Witness": {...}}' \
	  --schema schemas/psa2.schema.json \
	  > artifacts/out/$(WITC)

kg:
	python scripts/export_kg.py --capsules-dir capsules --out-turtle $(TTL)

shacl:
	pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human-readable $(TTL)

demo: baseline capsule judge witness kg shacl
	@echo
	@echo "Artifacts:"
	@echo "  Baseline: artifacts/out/$(BASE)"
	@echo "  Capsule:  artifacts/out/$(CAPS)"
	@echo "  Judge:    artifacts/out/$(JUDGE)"
	@echo "  Witness:  artifacts/out/$(WITC)"
	@echo "  Turtle:   $(TTL)"
	@echo

clean:
	rm -f artifacts/out/*.json artifacts/out/*.ttl
```

---

## B) `fragments/citation_capsule.md`

```md
STATEMENT: Each factual claim must include at least one credible citation; avoid PII.

ASSUMPTIONS:
- You can cite well-known sources you've seen before.
- You will redact any email/phone-like strings.

SOCRATIC (answer briefly before drafting):
1) What is the precise objective and success criterion?
2) What key assumptions must hold true?
3) What 3–5 steps will you follow?
4) What evidence will you produce, and how will you verify it?
5) What could make this wrong, and how would you detect it?

APHORISMS:
- One failing test beats ten opinions.
- Show me your plan before your answer.
- Cite it, or it didn’t happen.

ACCEPTANCE (you MUST satisfy all):
- Include sections: Objective, Assumptions, Plan, Evidence, Final, Citations, SelfCheck.
- Provide ≥1 citation {title, url}.
- Avoid PII or explicitly redact it.
```

---

## C) `schemas/psa2.schema.json`

```json
{
  "type": "object",
  "required": ["Objective","Assumptions","Plan","Evidence","Citations","Final","SelfCheck"],
  "properties": {
    "Objective":   { "type": "string", "minLength": 8 },
    "Assumptions": { "type": "array",  "minItems": 1, "items": { "type": "string" } },
    "Plan":        { "type": "array",  "minItems": 3, "items": { "type": "string" } },
    "Evidence":    { "type": "array",  "minItems": 1, "items": { "type": "string" } },
    "Citations":   {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "required": ["title","url"],
        "properties": { "title": { "type": "string" }, "url": { "type": "string", "format": "uri" } }
      }
    },
    "Final":       { "type": "string", "minLength": 16 },
    "SelfCheck":   { "type": "string", "minLength": 16 }
  },
  "additionalProperties": false
}
```

## D) `schemas/judge.schema.json`

```json
{
  "type":"object",
  "required":["Structure","Evidence","PII","SelfCheck","Notes","Verdict"],
  "properties":{
    "Structure":{"type":"integer","minimum":0,"maximum":5},
    "Evidence":{"type":"integer","minimum":0,"maximum":5},
    "PII":{"type":"integer","minimum":0,"maximum":5},
    "SelfCheck":{"type":"integer","minimum":0,"maximum":5},
    "Notes":{"type":"string"},
    "Verdict":{"type":"string"}
  }
}
```

---

## E) `scripts/witness_validate_capsule.py`

```python
from typing import List, Dict

def validate_capsule(payload: Dict) -> Dict:
    errors: List[str] = []
    if not payload.get("Citations"):
        errors.append("No citations present")
    evidence = payload.get("Evidence") or []
    if not any(len(str(e)) >= 10 for e in evidence):
        errors.append("Evidence items too short (<10 chars)")
    ok = not errors
    return {"ok": ok, "errors": errors}
```

---

## F) `scripts/witness_runner.py` (offline/sandbox witness)

```python
#!/usr/bin/env python3
import json, sys

def main(path: str) -> int:
    data = json.load(open(path))
    errors = []
    if not data.get("Citations"):
        errors.append("No citations present")
    evidence = data.get("Evidence") or []
    if not any(len(str(e)) >= 10 for e in evidence):
        errors.append("Evidence items too short (<10 chars)")
    if errors:
        print("SANDBOX WITNESS: FAIL")
        for e in errors: print("-", e)
        return 2
    print("SANDBOX WITNESS: PASS")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: witness_runner.py /path/to/result.json", file=sys.stderr)
        sys.exit(64)
    sys.exit(main(sys.argv[1]))
```

---

## G) `scripts/ab_run.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

A=artifacts/out/A.json
B=artifacts/out/B.json
J=artifacts/out/judge.json

echo "== Baseline =="
llm 'What caused the Therac-25 accidents? Return only a JSON object with keys: Objective, Assumptions, Plan, Evidence, Citations, Final, SelfCheck' \
  --schema schemas/psa2.schema.json > "$A"

echo "== Capsule =="
llm --sf fragments/citation_capsule.md \
  'What caused the Therac-25 accidents? Return only the JSON object.' \
  --schema schemas/psa2.schema.json > "$B"

echo "== Judge (A vs B) =="
llm --schema schemas/judge.schema.json \
  "Compare two JSON answers (A,B) with 0–5 scores for Structure,Evidence,PII,SelfCheck and return one JSON object.
   A=$(cat "$A") B=$(cat "$B")" > "$J"

echo "== Verdict =="
cat "$J"
```

---

## H) `scripts/export_kg.py` (YAML → Turtle)

```python
#!/usr/bin/env python3
import argparse, os, glob, yaml, datetime as dt

PFX = """@prefix tc:  <https://example.org/truthcapsule#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix prov:<http://www.w3.org/ns/prov#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""

def lit(s):  # naive turtle string escaper
    return '"' + str(s).replace('\\','\\\\').replace('"','\\"') + '"'

def main(capsules_dir, out_turtle):
    rows = [PFX]
    for path in sorted(glob.glob(os.path.join(capsules_dir, "*.yaml"))):
        cap = yaml.safe_load(open(path))
        cid  = cap.get("id") or os.path.splitext(os.path.basename(path))[0]
        subj = f"<urn:tc:{cid}>"
        rows.append(f"{subj} a tc:Capsule ;")
        rows.append(f"  tc:id {lit(cid)} ;")
        if cap.get("domain"):
            rows.append(f"  tc:domain {lit(cap['domain'])} ;")
        if cap.get("title"):
            rows.append(f"  dct:title {lit(cap['title'])} ;")
        if cap.get("statement"):
            rows.append(f"  tc:statement {lit(cap['statement'])} ;")
        for a in cap.get("assumptions",[])[:10]:
            rows.append(f"  tc:assumption {lit(a)} ;")
        for ctx in (cap.get("applies_to") or []):
            rows.append(f"  tc:appliesTo {lit(ctx)} ;")
        prov = cap.get("provenance") or {}
        if prov.get("author"):
            rows.append(f"  dct:creator {lit(prov['author'])} ;")
        if prov.get("org"):
            rows.append(f"  prov:wasAttributedTo {lit(prov['org'])} ;")
        if prov.get("created"):
            rows.append(f"  dct:created {lit(prov['created'])}^^xsd:dateTime ;")
        if prov.get("updated"):
            rows.append(f"  dct:modified {lit(prov['updated'])}^^xsd:dateTime ;")
        signing = (prov.get("signing") or {})
        if signing.get("digest"):
            rows.append(f"  tc:digest {lit(signing['digest'])} ;")
        if signing.get("signature"):
            rows.append(f"  tc:signature {lit(signing['signature'])} ;")
        # terminate triple
        rows[-1] = rows[-1][:-1] + " .\n"
    open(out_turtle,"w").write("\n".join(rows))
    print(f"Wrote {out_turtle}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--capsules-dir", required=True)
    ap.add_argument("--out-turtle", required=True)
    args = ap.parse_args()
    main(args.capsules_dir, args.out_turtle)
```

---

## I) `shacl/truthcapsule.shacl.ttl`

```turtle
@prefix sh:  <http://www.w3.org/ns/shacl#> .
@prefix tc:  <https://example.org/truthcapsule#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

tc:CapsuleShape
  a sh:NodeShape ;
  sh:targetClass tc:Capsule ;
  sh:property [ sh:path tc:id ;        sh:datatype xsd:string ; sh:minCount 1 ] ;
  sh:property [ sh:path dct:title ;     sh:datatype xsd:string ; sh:minCount 1 ] ;
  sh:property [ sh:path tc:domain ;     sh:datatype xsd:string ; sh:minCount 1 ] ;
  sh:property [ sh:path dct:created ;   sh:datatype xsd:dateTime ; sh:minCount 1 ] ;
  sh:property [ sh:path dct:modified ;  sh:datatype xsd:dateTime ; sh:minCount 1 ] ;
  sh:property [ sh:path tc:statement ;  sh:datatype xsd:string ; sh:minCount 1 ] .
```

---

## J) `scripts/run_sandboxed.sh` (Docker profile)

```bash
#!/usr/bin/env bash
# Usage: scripts/run_sandboxed.sh artifacts/out/B.json
set -euo pipefail
JSON=${1:?Path to JSON required}

IMAGE="python:3.11-slim"
# 10-line hardened profile: no net, RO FS, caps-down, resource limits
exec docker run --rm \
  --network=none \
  --read-only \
  --cpus="1.0" --memory="256m" --pids-limit=128 \
  --security-opt no-new-privileges \
  --cap-drop=ALL \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m \
  -v "$(pwd)":/repo:ro \
  -w /repo \
  ${IMAGE} \
  python scripts/witness_runner.py "$JSON"
```

---

## K) SPARQL queries (copy/paste)

**Q1 - Capsules by domain and title**

```sparql
PREFIX tc:  <https://example.org/truthcapsule#>
PREFIX dct: <http://purl.org/dc/terms/>
SELECT ?id ?domain ?title
WHERE {
  ?c a tc:Capsule ;
     tc:id ?id ;
     tc:domain ?domain ;
     dct:title ?title .
}
ORDER BY ?domain ?id
```

**Q2 - Capsules by appliesTo context (e.g., “conversation”)**

```sparql
PREFIX tc: <https://example.org/truthcapsule#>
SELECT ?id
WHERE {
  ?c a tc:Capsule ; tc:id ?id ; tc:appliesTo "conversation" .
}
ORDER BY ?id
```

**Q3 - Capsules missing signature (audit)**

```sparql
PREFIX tc: <https://example.org/truthcapsule#>
SELECT ?id
WHERE {
  ?c a tc:Capsule ; tc:id ?id .
  FILTER NOT EXISTS { ?c tc:signature ?sig }
}
ORDER BY ?id
```

---

### That’s it

* **Fast path:** `make demo` → judge verdict, witness pass, KG export, SHACL conform.
* **Security:** use `scripts/run_sandboxed.sh` to validate outputs offline in a constrained container.
* **Talking point:** this is “**proof-carrying prompts**”: Socratic + aphorisms + acceptance + schema + executable witness + KG.

If you want me to also generate a **PowerShell** variant for Windows users and a **GIF script** for the README hero demo, say the word.
