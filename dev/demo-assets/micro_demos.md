Amazing-here’s a tight, “hit record and go” package: a **5-minute screencast script** plus **3 micro case studies** with copy-paste steps and **expected pass/fail logs**. Everything uses paths/files already in your repo so you can demo without prep.

---

# 🎬 5-Minute Screencast Script (voiceover + terminal steps)

**Goal:** show that capsules = **policy + pedagogy + proof** (Socratic/aphorisms + executable witnesses) and that they **run, fail, get fixed, pass**-plus a quick **KG export**.

### 0:00 – 0:30 - What you’re seeing

* “These are **Truth Capsules**: signed YAML artifacts that bundle a policy statement, explicit assumptions, a few Socratic prompts & aphorisms, and **executable witnesses**. They run in CI or locally and can export to a knowledge graph.”

### 0:30 – 2:00 - Run the assistant baseline (passes)

```bash
# from repo root
pip install -r requirements.txt

# run the assistant baseline bundle (PII + citation + tool-contract + plan-verify)
python scripts/run_capsules.py --bundle bundles/assistant_baseline_v1.yaml
```

**Narrate:** “We load the bundle and run four gates against sample artifacts under `artifacts/examples/`.”

**Expected condensed output (PASS):**

```
[Bundle] assistant_baseline_v1
  [Capsule] llm.pii_redaction_guard_v1
    - witness: pii_scan ............... PASS
  [Capsule] llm.citation_required_v1
    - witness: has_citation ........... PASS
  [Capsule] llm.tool_json_contract_v1
    - witness: schema_conforms ........ PASS
  [Capsule] llm.plan_verify_answer_v1
    - witness: plan_verified .......... PASS
Summary: 4/4 capsules passed, 0 failed. Witnesses passed: 4/4
```

### 2:00 – 3:00 - Make it fail, then fix

```bash
# 1) Break citations by removing the citation field
jq 'del(.citations)' artifacts/examples/answer_with_citation.json > artifacts/examples/answer_missing_citation.json
TC_ARTIFACT=artifacts/examples/answer_missing_citation.json \
python scripts/run_capsules.py --capsule capsules/llm.citation_required_v1.yaml
```

**Expected output (FAIL then reason):**

```
[Capsule] llm.citation_required_v1
  - witness: has_citation ............. FAIL
    AssertionError: Missing required field: citations (>=1)
Summary: 0/1 capsules passed, 1 failed. Witnesses passed: 0/1
```

```bash
# Fix it by adding a citation back
jq '.citations=[{"title":"RFC 7231","url":"https://www.rfc-editor.org/rfc/rfc7231"}]' \
  artifacts/examples/answer_missing_citation.json > artifacts/examples/answer_fixed_citation.json
TC_ARTIFACT=artifacts/examples/answer_fixed_citation.json \
python scripts/run_capsules.py --capsule capsules/llm.citation_required_v1.yaml
```

**Expected output (PASS):**

```
[Capsule] llm.citation_required_v1
  - witness: has_citation ............. PASS
Summary: 1/1 capsules passed, 0 failed. Witnesses passed: 1/1
```

### 3:00 – 4:00 - Tool-contract catch (fail), then pass

```bash
# Break tool schema: set attendees to a string vs array
jq '.attendees="foo@bar.com"' artifacts/examples/tool_call_ok.json > artifacts/examples/tool_call_bad.json
TC_CALL=artifacts/examples/tool_call_bad.json \
python scripts/run_capsules.py --capsule capsules/llm.tool_json_contract_v1.yaml
```

**Expected output (FAIL):**

```
[Capsule] llm.tool_json_contract_v1
  - witness: schema_conforms .......... FAIL
    ValidationError: $.attendees: expected array of strings, got string
Summary: 0/1 capsules passed, 1 failed. Witnesses passed: 0/1
```

```bash
# Fix: restore array form
jq '.attendees=["foo@bar.com"]' artifacts/examples/tool_call_bad.json > artifacts/examples/tool_call_fixed.json
TC_CALL=artifacts/examples/tool_call_fixed.json \
python scripts/run_capsules.py --capsule capsules/llm.tool_json_contract_v1.yaml
```

**Expected output (PASS).**

### 4:00 – 5:00 - KG export + validate (wow moment)

```bash
# Export RDF (Turtle) + NDJSON-LD and validate with SHACL
python scripts/export_kg.py
pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
```

**Expected output (conforms):**

```
[KG] Wrote artifacts/out/capsules.ttl and artifacts/out/capsules.ndjson
Conforms: True
Results (0):
```

**Close:** “Capsules are **proof-carrying prompts** you can run, sign, and query.”

---

# 📚 Micro Case Study 1 - Customer Support Guardrails (PII + Citations)

**Outcome:** prevent PII leakage and require citations for factual claims.

## Steps

1. **Baseline pass** (sanity check):

```bash
python scripts/run_capsules.py --bundle bundles/assistant_baseline_v1.yaml
```

2. **Trigger PII failure** (insert an email + phone):

```bash
cp artifacts/examples/pii_ok.json artifacts/examples/pii_bad.json
# Inject a couple of PII tokens (email, phone)
jq '.text="Contact me at jane.doe@example.com or +1 (555) 123-4567"' \
  artifacts/examples/pii_bad.json > artifacts/examples/pii_bad.json.tmp && \
mv artifacts/examples/pii_bad.json.tmp artifacts/examples/pii_bad.json

TC_TXT=artifacts/examples/pii_bad.json \
python scripts/run_capsules.py --capsule capsules/llm.pii_redaction_guard_v1.yaml
```

**Expected log (FAIL):**

```
[Capsule] llm.pii_redaction_guard_v1
  - witness: pii_scan ................. FAIL
    Found PII: email(jane.doe@example.com), phone(+1 (555) 123-4567)
Summary: 0/1 capsules passed, 1 failed. Witnesses passed: 0/1
```

3. **Redact and pass**:

```bash
jq '.text="Contact me at [redacted email] or [redacted phone]"' \
  artifacts/examples/pii_bad.json > artifacts/examples/pii_redacted.json
TC_TXT=artifacts/examples/pii_redacted.json \
python scripts/run_capsules.py --capsule capsules/llm.pii_redaction_guard_v1.yaml
```

**Expected log (PASS).**

4. **Trigger citation failure** (remove citations):

```bash
jq 'del(.citations)' artifacts/examples/answer_with_citation.json \
  > artifacts/examples/answer_missing_citation.json

TC_ARTIFACT=artifacts/examples/answer_missing_citation.json \
python scripts/run_capsules.py --capsule capsules/llm.citation_required_v1.yaml
```

**Expected log (FAIL):**

```
[Capsule] llm.citation_required_v1
  - witness: has_citation ............. FAIL
    AssertionError: Missing required field: citations (>=1)
```

5. **Add citation and pass**:

```bash
jq '.citations=[{"title":"RFC 7231","url":"https://www.rfc-editor.org/rfc/rfc7231"}]' \
  artifacts/examples/answer_missing_citation.json \
  > artifacts/examples/answer_fixed_citation.json

TC_ARTIFACT=artifacts/examples/answer_fixed_citation.json \
python scripts/run_capsules.py --capsule capsules/llm.citation_required_v1.yaml
```

**Expected log (PASS).**

---

# 🧰 Micro Case Study 2 - Tool Contract Enforcement (JSON Schema)

**Outcome:** block malformed tool calls before they hit your backends.

## Steps

1. **Pass with the provided OK call:**

```bash
python scripts/run_capsules.py --capsule capsules/llm.tool_json_contract_v1.yaml
```

(Uses `TC_SCHEMA` and `TC_CALL` from the assistant bundle’s `env` defaults; should PASS.)

2. **Fail on type mismatch:**

```bash
jq '.attendees="alice@corp.com"' artifacts/examples/tool_call_ok.json \
  > artifacts/examples/tool_call_bad.json

TC_CALL=artifacts/examples/tool_call_bad.json \
python scripts/run_capsules.py --capsule capsules/llm.tool_json_contract_v1.yaml
```

**Expected log (FAIL):**

```
[Capsule] llm.tool_json_contract_v1
  - witness: schema_conforms .......... FAIL
    ValidationError: $.attendees: expected array of strings, got string
```

3. **Fail on missing required field:**

```bash
jq 'del(.start_time)' artifacts/examples/tool_call_ok.json \
  > artifacts/examples/tool_call_missing_field.json

TC_CALL=artifacts/examples/tool_call_missing_field.json \
python scripts/run_capsules.py --capsule capsules/llm.tool_json_contract_v1.yaml
```

**Expected log (FAIL):**

```
[Capsule] llm.tool_json_contract_v1
  - witness: schema_conforms .......... FAIL
    ValidationError: $.start_time: is required
```

4. **Fix and pass:**

```bash
jq '.attendees=["alice@corp.com"] | .start_time="2025-12-01T15:00:00Z"' \
  artifacts/examples/tool_call_missing_field.json \
  > artifacts/examples/tool_call_fixed.json

TC_CALL=artifacts/examples/tool_call_fixed.json \
python scripts/run_capsules.py --capsule capsules/llm.tool_json_contract_v1.yaml
```

**Expected log (PASS).**

---

# 🧪 Micro Case Study 3 - Problem-Solving Rubric (Pedagogy + Witness)

**Outcome:** teach & enforce a lightweight **5-step reasoning form** (objective, assumptions, plan, evidence, summary).

## Steps

1. **Pass with the provided good report:**

```bash
python scripts/run_capsules.py --capsule capsules/pedagogy.problem_solving_v1.yaml
```

(Uses `artifacts/examples/problem_solving_ok.json` via the witness; should PASS.)

**Expected log (PASS):**

```
[Capsule] pedagogy.problem_solving_v1
  - witness: five_step_gate ........... PASS
```

2. **Fail by removing required fields:**

```bash
jq 'del(.evidence) | del(.assumptions)' \
  artifacts/examples/problem_solving_ok.json \
  > artifacts/examples/problem_solving_bad.json

PS_REPORT=artifacts/examples/problem_solving_bad.json \
python scripts/run_capsules.py --capsule capsules/pedagogy.problem_solving_v1.yaml
```

**Expected log (FAIL with the assert messages from your witness):**

```
[Capsule] pedagogy.problem_solving_v1
  - witness: five_step_gate ........... FAIL
    AssertionError: Missing fields: ["assumptions","evidence"]
```

3. **Partial fix but still fail (evidence too short):**

```bash
jq '.assumptions=["network available"] | .evidence=["ok"]' \
  artifacts/examples/problem_solving_bad.json \
  > artifacts/examples/problem_solving_short_evidence.json

PS_REPORT=artifacts/examples/problem_solving_short_evidence.json \
python scripts/run_capsules.py --capsule capsules/pedagogy.problem_solving_v1.yaml
```

**Expected log (FAIL):**

```
[Capsule] pedagogy.problem_solving_v1
  - witness: five_step_gate ........... FAIL
    AssertionError: evidence must contain at least one item with length >= 10
```

4. **Full fix and pass:**

```bash
jq '.evidence=["Validated result logs exceed 10 chars."]' \
  artifacts/examples/problem_solving_short_evidence.json \
  > artifacts/examples/problem_solving_fixed.json

PS_REPORT=artifacts/examples/problem_solving_fixed.json \
python scripts/run_capsules.py --capsule capsules/pedagogy.problem_solving_v1.yaml
```

**Expected log (PASS).**

---

## (Optional) KG “case study” - SHACL catches a malformed capsule

1. **Create a broken capsule (missing `title`):**

```bash
cat > capsules/tmp.bad_capsule.yaml <<'YAML'
id: demo.bad_capsule_v1
version: 1.0.0
domain: demo
statement: "This capsule is missing a title"
assumptions: ["foo"]
provenance:
  schema: provenance.v1
  author: You
  org: Demo
  license: MIT
  created: 2025-11-07T00:00:00Z
  updated: 2025-11-07T00:00:00Z
YAML
```

2. **Export + validate:**

```bash
python scripts/export_kg.py
pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
```

**Expected SHACL report (FAIL with pointer to missing title):**

```
Conforms: False
Results (1):
Constraint Violation in PropertyConstraintComponent (http://.../title)
Focus Node: https://w3id.org/tc/capsule/demo.bad_capsule_v1
Message: Less than 1 values on dct:title
Path: dct:title
```

---

# ✅ Presenter cheat-sheet (talking points while logs scroll)

* **Socratic + Aphorisms**: “We *front-load* good thinking-Socratic prompts force decomposition and surface assumptions; aphorisms are small nudges (token-cheap) that bias the model toward robust behavior.”
* **Witnesses**: “These are small, hermetic tests that convert prompts into **proof-carrying** outputs-pass/fail you can trust.”
* **Signatures & provenance**: “Capsules are signable artifacts; changes are diffable and auditable.”
* **KG readiness**: “Export to RDF/SHACL in one command; query in SPARQL or load into Neo4j.”

---

## Notes & assumptions

* The **exact wording** of failure messages may differ by your witness implementation; the messages above reflect the *intended checks* (missing fields, schema mismatches, PII hits). If your runner prints differently, keep the spirit (capsule → witness → PASS/FAIL + reason).
* Commands rely on **`jq`** being available; if not, replace with a text editor for the screencast.

Want me to tailor the expected log format to your runner’s exact output? Paste one real run and I’ll match its style line-for-line.
