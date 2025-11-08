# LLM × Truth Capsules - Combination Usage Guide (v1 RC)

*A practical, copy-paste playbook for running Truth Capsules through the excellent [llm](https://llm.datasette.io/) CLI by [Simon Willison](https://simonwillison.net/) demonstrating “cognitive upgrade” (Socratic + aphorisms), enforceable structure (JSON schemas), executable checks (witnesses as tools), and reproducible templates.*

---

## Table of contents

* [What this gives you](#what-this-gives-you)
* [Concept map (Capsules ➜ llm features)](#concept-map-capsules--llm-features)
* [Quickstart TL;DR](#quickstart-tldr)
* [Project layout additions](#project-layout-additions)
* [1) Create capsule fragments](#1-create-capsule-fragments)
* [2) Enforce structure with `--schema`](#2-enforce-structure-with---schema)
* [3) Run baseline vs capsule-inflated prompts](#3-run-baseline-vs-capsule-inflated-prompts)
* [4) Add executable witnesses as `--functions` tools](#4-add-executable-witnesses-as---functions-tools)
* [5) Save as one-word templates](#5-save-as-oneword-templates)
* [6) A/B judge to *prove* cognitive upgrade](#6-ab-judge-to-prove-cognitive-upgrade)
* [7) Fragments & long context](#7-fragments--long-context)
* [8) Multi-turn chats & continuing tools](#8-multiturn-chats--continuing-tools)
* [9) Attachments (images, PDFs) with capsule constraints](#9-attachments-images-pdfs-with-capsule-constraints)
* [10) Logs, extraction, and reproducibility](#10-logs-extraction-and-reproducibility)
* [11) CI-friendly recipes](#11-ci-friendly-recipes)
* [12) Security posture (witness/tools sandboxing)](#12-security-posture-witnesstools-sandboxing)
* [Appendix A: `capsule_to_fragment.py`](#appendix-a-capsule_to_fragmentpy)
* [Appendix B: Reusable schemas](#appendix-b-reusable-schemas)
* [Appendix C: Makefile shortcuts](#appendix-c-makefile-shortcuts)

---

## What this gives you

* **Cognitive upgrade demo**: Same task, same model-**capsule** (statement + assumptions + Socratic + aphorisms) produces measurably better outputs than baseline.
* **Structure guarantees**: Model outputs **must** match a JSON schema via `--schema`.
* **Proof-carrying prompts**: Executable **witness** checks run in-loop via `--functions` (tools), yielding PASS/FAIL signals.
* **Reproducibility**: Save capsules as **templates** (`--save`) and **fragments**; set **model defaults**; capture **logs**.

---

## Concept map (Capsules ➜ llm features)

| Capsule element             | llm feature                           | Why it matters                                    |
| --------------------------- | ------------------------------------- | ------------------------------------------------- |
| `statement`, `assumptions`  | `--system` / `--sf` (system fragment) | Fix intent/scope; avoid prompt drift              |
| Socratic prompts, aphorisms | `--fragment`                          | Cognitive scaffolding without bespoke prompt text |
| Acceptance checklist        | `--schema`                            | Enforce section presence/shape                    |
| Witness (assertions)        | `--functions` (+ `--td`, `--ta`)      | Run checks as tools; show PASS/FAIL in output     |
| Capsule persona reuse       | `--save` templates                    | One-word reuse: `-t mycapsule`                    |
| A/B proof                   | logs + judge schema                   | Quantify upgrade (baseline vs capsule-inflated)   |

---

## Quickstart TL;DR

```bash
# Optional: pick a default model
export LLM_MODEL=gpt-4o-mini

# 1) Create capsule fragment (Socratic + aphorisms)
mkdir -p fragments schemas
# (See §1 below for full content)
$EDITOR fragments/citation_capsule.md

# 2) Create output JSON schema
$EDITOR schemas/psa2.schema.json

# 3) Baseline (no capsule)
llm 'Therac-25: Return JSON with sections.' --schema schemas/psa2.schema.json > /tmp/A.json

# 4) Capsule-inflated (system fragment)
llm --sf fragments/citation_capsule.md \
    'Therac-25: Return only JSON.' \
    --schema schemas/psa2.schema.json > /tmp/B.json

# 5) Add witness as a tool to check evidence length & citations
llm --sf fragments/citation_capsule.md \
    --functions "$(cat scripts/witness_validate_capsule.py)" \
    --td \
    'Therac-25: Return only JSON and CALL validate_capsule(JSON).' \
    --schema schemas/psa2.schema.json > /tmp/C.json

# 6) A/B judge (prove the upgrade)
llm --schema schemas/judge.schema.json \
   "Score A vs B with the rubric. A=$(cat /tmp/A.json) B=$(cat /tmp/B.json)"
```

---

## Project layout additions

Add these (if not already present):

```
fragments/             # capsule-derived prompt snippets
schemas/               # JSON schemas used by llm --schema
scripts/
  capsule_to_fragment.py
  witness_validate_capsule.py
docs/
  LLMS_COMBO_GUIDE.md  # (this file)
```

> **Note:** Keep YAML capsules the source of truth; fragments are derived artifacts (see Appendix A).

---

## 1) Create capsule fragments

**Goal**: Turn one capsule’s pedagogy into a reusable **system fragment**. Example (citations + PII hygiene):

`fragments/citation_capsule.md`

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

> You can generate these programmatically from YAML capsules (Appendix A).

---

## 2) Enforce structure with `--schema`

Create a reusable JSON schema to **force** sections to exist and to validate shapes:

`schemas/psa2.schema.json`

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

---

## 3) Run baseline vs capsule-inflated prompts

**Baseline (no capsule):**

```bash
llm 'What caused the Therac-25 accidents? Return only a JSON object with keys: Objective, Assumptions, Plan, Evidence, Citations, Final, SelfCheck' \
  --schema schemas/psa2.schema.json \
  > /tmp/therac_A.json
```

**Capsule-inflated (system fragment + schema):**

```bash
llm --sf fragments/citation_capsule.md \
  'What caused the Therac-25 accidents? Return only the JSON object.' \
  --schema schemas/psa2.schema.json \
  > /tmp/therac_B.json
```

> *What you’ll see:* `B` is consistently more complete, with explicit citations and a real self-check.

---

## 4) Add executable witnesses as `--functions` tools

Turn capsule “witness” logic into a Python tool callable by the model:

`scripts/witness_validate_capsule.py`

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

**Run with tool call & debug:**

```bash
llm --sf fragments/citation_capsule.md \
  --functions "$(cat scripts/witness_validate_capsule.py)" \
  --td \
  'Therac-25: Return only JSON (schema), then CALL validate_capsule(JSON) and include its result as {"Witness": {...}}' \
  --schema schemas/psa2.schema.json \
  > /tmp/therac_C.json
```

* `--td` prints **tool call** + return value (auditable).
* Use `--ta` to **approve** each call interactively.

---

## 5) Save as one-word templates

Make this capsule persona a template for easy reuse:

```bash
llm --sf fragments/citation_capsule.md --save tc_citation
llm -t tc_citation 'Summarize DNSSEC; return only JSON.' --schema schemas/psa2.schema.json
```

> Tip: version your templates (`tc_citation_v1`) to match capsule versions.

---

## 6) A/B judge to *prove* cognitive upgrade

Create a judge schema and ask the model to score both answers with one JSON result.

`schemas/judge.schema.json`

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

**Run judge:**

```bash
llm --schema schemas/judge.schema.json \
 'Compare two JSON answers (A and B) to the same question using 0–5 scores:
  - Structure completeness
  - Evidence quality (citations)
  - PII hygiene
  - Self-Check clarity
  Produce one JSON object with Structure,Evidence,PII,SelfCheck,Notes,Verdict.
  A='$(cat /tmp/therac_A.json)'
  B='$(cat /tmp/therac_B.json)''
```

> Expect **B** to win on Structure/Evidence/SelfCheck.

---

## 7) Fragments & long context

Fragments de-duplicate long prompts and can be aliased:

```bash
llm fragments set citcap fragments/citation_capsule.md
llm -f citcap 'Task...' --schema schemas/psa2.schema.json
llm fragments -q citcap
```

You can also use **system fragments** (`--sf`) for the capsule and **regular fragments** (`-f`) for domain context (specs, policies, diffs).

---

## 8) Multi-turn chats & continuing tools

Start a chat with capsule persona and tools:

```bash
llm chat -t tc_citation --td
# Now paste tasks. Tools defined with --functions persist if you start them in the opening prompt,
# or install plugin tools and start chat with -T / --tool.
```

> For plugin toolboxes (e.g., `Datasette(...)`), start with `llm chat -T 'Datasette("...")' --td`.

---

## 9) Attachments (images, PDFs) with capsule constraints

Use capsule instructions **plus** attachments:

```bash
llm --sf fragments/citation_capsule.md \
  "Extract key claims from this PDF and cite the pages." \
  -a report.pdf \
  --schema schemas/psa2.schema.json
```

> Great for **grounded** evidence gathering; pair with witnesses that verify citation shape.

---

## 10) Logs, extraction, and reproducibility

* Extract last fenced code block (or JSON block) only:

  ```bash
  llm -x --sf fragments/citation_capsule.md 'Return a single fenced JSON block...'
  ```
* Inspect models and options:

  ```bash
  llm models --options
  ```
* View logs:

  ```bash
  llm logs -c    # last conversation
  llm logs --schema  # browse stored JSON objects created with --schema
  ```

---

## 11) CI-friendly recipes

* **Pinned defaults**:

  ```bash
  llm models options set gpt-4o-mini temperature 0.2
  ```
* **Non-interactive run**:

  ```bash
  llm --no-stream --sf fragments/citation_capsule.md \
      'Task...' --schema schemas/psa2.schema.json > artifacts/out/run.json
  ```
* **A/B regression**: compare prior (`baseline.json`) to new (`capsule.json`) using the judge schema and **fail** CI if Verdict != “B wins”.

---

## 12) Security posture (witness/tools sandboxing)

* Prefer **small, deterministic** witness functions; avoid network and filesystem writes.
* Use `--ta` (approve tools) during interactive demos; in automation, run vetted functions only.
* Keep witness code in repo under `scripts/` with code review; avoid arbitrary runtime injection.
* For stronger isolation, run `llm` inside your **sandboxed container** with no-net and capped CPU/mem.

---

## Appendix A: `capsule_to_fragment.py`

Generate a fragment from a YAML capsule (pull `statement`, `assumptions`, and `pedagogy` entries marked `Socratic` / `Aphorism`).

```python
#!/usr/bin/env python3
import sys, yaml, textwrap

def to_fragment(capsule):
    stmt = capsule.get("statement","").strip()
    assumptions = capsule.get("assumptions", [])
    ped = capsule.get("pedagogy", []) or []
    soc = [p["text"] for p in ped if str(p.get("kind","")).lower().startswith("socratic")]
    aph = [p["text"] for p in ped if str(p.get("kind","")).lower().startswith("aphorism")]

    lines = []
    if stmt:
        lines += [f"STATEMENT: {stmt}", ""]
    if assumptions:
        lines += ["ASSUMPTIONS:"] + [f"- {a}" for a in assumptions] + [""]
    if soc:
        lines += ["SOCRATIC (answer briefly before drafting):"]
        for i, q in enumerate(soc, 1):
            lines.append(f"{i}) {q}")
        lines.append("")
    if aph:
        lines += ["APHORISMS:"] + [f"- {a}" for a in aph] + [""]
    lines += ["ACCEPTANCE (you MUST satisfy):",
              "- Include Objective, Assumptions, Plan, Evidence, Final, Citations, SelfCheck.",
              "- Provide ≥1 citation {title, url}.",
              "- Avoid PII or redact it.",
              ""]
    return "\n".join(lines).strip() + "\n"

if __name__ == "__main__":
    path = sys.argv[1]
    cap = yaml.safe_load(open(path))
    print(to_fragment(cap))
```

**Use:**

```bash
python scripts/capsule_to_fragment.py capsules/llm.citation_required_v1.yaml \
  > fragments/citation_capsule.md
```

---

## Appendix B: Reusable schemas

**Judge schema** (already shown): `schemas/judge.schema.json`
**Ops/PR variant** (extra keys) - extend `psa2.schema.json`:

```json
{
  "type":"object",
  "allOf":[
    { "$ref":"./psa2.schema.json" },
    {
      "properties":{
        "RiskTags":{"type":"array","items":{"type":"string"}},
        "TestHints":{"type":"array","items":{"type":"string"}}
      }
    }
  ]
}
```

---

## Appendix C: Makefile shortcuts

```make
MODEL ?= gpt-4o-mini

export LLM_MODEL=$(MODEL)

.PHONY: baseline capsule witness judge

baseline:
	llm 'Therac-25: Return only JSON with sections.' \
	  --schema schemas/psa2.schema.json > artifacts/out/A.json

capsule:
	llm --sf fragments/citation_capsule.md \
	  'Therac-25: Return only JSON.' \
	  --schema schemas/psa2.schema.json > artifacts/out/B.json

witness:
	llm --sf fragments/citation_capsule.md \
	  --functions "$$(cat scripts/witness_validate_capsule.py)" --td \
	  'Therac-25: Return only JSON and CALL validate_capsule(JSON).' \
	  --schema schemas/psa2.schema.json > artifacts/out/C.json

judge:
	llm --schema schemas/judge.schema.json \
	  "Score A vs B. A=$$(cat artifacts/out/A.json) B=$$(cat artifacts/out/B.json)" \
	  > artifacts/out/judge.json
```

---

### Final notes

* Keep **YAML capsules** as the *source of truth*; derive fragments and schemas from them.
* Use `--save` templates to make “capsule personas” one-word selectable by anyone on your team.
* The “**A/B + judge**” pattern is your **proof**: the capsule isn’t just style-it measurably improves structure, citations, and self-checks while witnesses make it **proof-carrying**.
