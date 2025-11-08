Love the momentum. Here’s a tight, no-nonsense audit + concrete upgrades you can do tomorrow that will make authoring smoother, prompts sharper, and the repo feel pro.

# What to fix (and how)

## 1) Strengthen the profile’s system fragment (context + control surface)

Your current system header doesn’t teach the model what a “Truth Capsule” is or how to behave when capsules conflict. Add a short, repeatable preamble every profile can inherit:

```text
SYSTEM: Truth Capsules Overview
- A Truth Capsule = a small, versioned rule-package (id, domain, statement, assumptions, pedagogy, enforcement).
- When answering, obey “Capsule Compliance Order” below, and abstain if you cannot comply.
- Always produce a short COMPLIANCE block before the final answer.

Capsule Compliance Order
1) Safety > 2) Legal/PII > 3) Source integrity (Citations) > 4) Task-specific rules > 5) Pedagogy (advice-only).
Conflict Policy
- On conflict: cite the capsule ids and follow the highest-priority capsule; abstain if unsure.
- Ask at most ONE clarifying question when information is missing and abstention would be triggered.

Output Contract (per response)
[PLAN] bullets…
[VERIFY] checks vs. capsule ids…
[COMPLIANCE] for each capsule: PASS | FAIL | N/A with one-line justification
[ANSWER] final
```

Put that block in each `profiles/*.yaml` (or reference it via `response.system_block`), so the composer doesn’t have to reinvent this per-bundle.

## 2) Profile-aware “capsule projection” (what fields to show per profile)

Right now every capsule dumps similar fields. You’ll want **views** per profile (e.g., conversational vs CI vs code_patch) that pick and format capsule fields differently.

Add a tiny projection map (could be YAML or inline in the profile):

```yaml
# profiles/conversational.yaml (excerpt)
id: profile.conversational_guidance_v1
version: 1.1.0
response:
  system_block: |
    …(the improved preamble above)…
  projection:
    include:
      - title
      - statement
      - assumptions[:5]
      - pedagogy.socratic[:3]
      - pedagogy.aphorisms[:3]
    render:
      capsule_header: "BEGIN CAPSULE id={id} v={version} domain={domain}"
      assumption_bullet: "  - {text}"
      enforcement_footer: "ENFORCEMENT: Obey or abstain. END CAPSULE"
```

Then update `compose_capsules_cli.py` to accept `--projection default|strict|ci|pedagogy` (default = read from profile; override possible from CLI). The projection decides:

* Which fields appear
* Field limits (e.g., top-N assumptions)
* Formatting strings

This gives you the “template per profile” knob you asked for on day 1.

### Minimal code patch (recursive capsules + projection)

* **Recursive glob** so folders won’t break anything:

```python
# replace pattern in index_capsules(...)
pattern = os.path.join(root, "capsules", "**", "*.yaml")
for filepath in sorted(glob.glob(pattern, recursive=True)):
    ...
```

* **Projection aware rendering** (inside `compose_text`):

```python
proj = profile.get("response", {}).get("projection", {})  # dict
def take(lst, n): return (lst or [])[:n] if n else (lst or [])
def pick_capsule_fields(c):
    out = {"id": c.get("id"), "version": c.get("version"), "domain": c.get("domain")}
    if "title" in proj.get("include", []): out["title"] = c.get("title")
    if "statement" in proj.get("include", []): out["statement"] = c.get("statement")
    # assumptions[:N]
    for inc in proj.get("include", []):
        if inc.startswith("assumptions[:"):
            n = int(inc.split("[:")[1].split("]")[0])
            out["assumptions"] = take(c.get("assumptions"), n)
    # pedagogy.socratic[:N], pedagogy.aphorisms[:N]
    ped = c.get("pedagogy") or []
    soc = [p.get("text") for p in ped if p.get("kind","").lower()=="socratic"]
    aph = [p.get("text") for p in ped if p.get("kind","").lower()=="aphorism"]
    for inc in proj.get("include", []):
        if inc.startswith("pedagogy.socratic[:"):
            n = int(inc.split("[:")[1].split("]")[0]); out["socratic"]=take(soc,n)
        if inc.startswith("pedagogy.aphorisms[:"):
            n = int(inc.split("[:")[1].split("]")[0]); out["aphorisms"]=take(aph,n)
    return out
```

Use `proj.get("render", {})` strings to format headers/footers.

## 3) Folder structure for `/capsules` (safe to do if you switch to recursive glob)

Recommend:

```
capsules/
  llm/
    llm.citation_required_v1.yaml
    llm.pii_redaction_guard_v1.yaml
    …
  pr/
    llm.pr_diff_first_v1.yaml
    …
  safety/
  ops/
  pedagogy/
  business/
```

Because ids already include domain/name, moving files won’t break ids. Your linter can add a **path/domain consistency** check (warn if `domain:` doesn’t match top-level folder).

## 4) Bundle schema spec (v1.1)

Add a doc + JSON Schema for bundles so they can do more than list capsules.

**`docs/BUNDLES_SCHEMA_v1.md`** (essentials):

* `name` (string)
* `version` (semver)
* `applies_to` (list[str] profile ids or aliases)
* `capsules` (list[str] ids)
* `excludes` (optional list[str] ids)
* `priority_overrides` (map[capsule_id] -> int)  # helps tie-break conflicts
* `projection` (optional string)  # override profile default
* `order` (optional explicit ordering of capsule ids)
* `tags` (list[str])
* `notes` (string)

**JSON Schema** (snippet to drop in `schemas/bundle.schema.v1.json`):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Truth Capsule Bundle v1.1",
  "type": "object",
  "required": ["name", "version", "capsules"],
  "properties": {
    "name": {"type":"string"},
    "version": {"type":"string"},
    "applies_to": {"type":"array","items":{"type":"string"}},
    "capsules": {"type":"array","items":{"type":"string"}},
    "excludes": {"type":"array","items":{"type":"string"}},
    "priority_overrides": {"type":"object","additionalProperties":{"type":"integer"}},
    "projection": {"type":"string"},
    "order": {"type":"array","items":{"type":"string"}},
    "tags": {"type":"array","items":{"type":"string"}},
    "notes": {"type":"string"}
  }
}
```

Update `compose_capsules_cli.py` to:

* Validate bundles against this schema (optional `--strict-bundles`)
* Apply `excludes`, `priority_overrides`, `projection`, `order`

## 5) Prompt hygiene & compression (models obey short rules better)

Biggest red-team risk: **prompt bloat → non-adherence**. Add an **auto-compressor** pass:

* Merge redundant rules across capsules.
* Emit a compact **Control Table** the model can follow.

Example insertion (just before listing capsules):

```text
SYSTEM: Capsule Control Table (compiled)
| Priority | Capsule ID                     | Must / Forbid / Ask-One | Test (1-liner)       |
|---------:|--------------------------------|--------------------------|----------------------|
| 1        | llm.safety_refusal_guard_v1    | FORBID unsafe content    | refusal patterns…    |
| 2        | llm.pii_redaction_guard_v1     | FORBID raw PII           | mask or abstain      |
| 3        | llm.citation_required_v1       | MUST cite or abstain     | provide sources      |
| 4        | llm.plan_verify_answer_v1      | MUST Plan→Verify→Answer  | emit P,V,A sections  |
```

That single table massively increases adherence in practice.

## 6) Manifests & provenance (lock the exact “view”)

Your manifest should now record:

* profile id + profile version
* projection name/version
* bundle names + versions
* capsule ids + file hashes
* composer version
* optional **abstain threshold** and **ask-one policy**

Extend `manifest.json` accordingly.

## 7) Authoring ergonomics (“loose ends” you’ll feel tomorrow)

* **Capsule style guide**: one-screen checklist for authors (title verbs, statement format, assumptions granularity, 1-line enforcement).
* **Id/Title normalization**: linter ensures `id` matches filename slug; titles in Title Case.
* **Severity & scope**: add optional `severity: info|warn|error|block` per capsule; use it in Control Table.
* **Stop-on-fail**: bundle-level `stop_on_fail: [capsule_id,…]` gate.
* **Shortcodes**: allow `USES:[CITE, PVA, PII]`—composer expands to full rules or a compact reference if already compiled.
* **KG fields**: ensure each capsule has stable `@id` / IRI (you already do), and keep a tiny `sameAs`/`seeAlso` for interop.

## 8) Revised sample output (compact, profile-aware)

Here’s your example, upgraded:

```text
SYSTEM: Conversational Guidance (Truth Capsules)
- A Truth Capsule = small, versioned rule-package. Obey Capsule Compliance Order.
- Conflict: cite capsule ids; follow highest priority; ask ONE clarifying Q if needed.
- Output blocks: PLAN → VERIFY → COMPLIANCE → ANSWER.

Capsule Compliance Order
1) safety  2) PII/legal  3) citations  4) task rules  5) pedagogy

SYSTEM: Capsule Control Table (compiled)
|Pri| Capsule ID                      | Directive                |
|---|---------------------------------|--------------------------|
|1  | llm.safety_refusal_guard_v1     | FORBID unsafe outputs    |
|2  | llm.pii_redaction_guard_v1      | FORBID raw PII           |
|3  | llm.citation_required_v1        | MUST cite or abstain     |
|4  | llm.plan_verify_answer_v1       | MUST Plan→Verify→Answer  |

SYSTEM: Capsule Rules (view=conversational)
BEGIN CAPSULE id=llm.pii_redaction_guard_v1 v=1.0.0 domain=llm
TITLE: PII redaction
STATEMENT: Output must not contain raw PII (emails/phones). Use placeholders or abstain.
ASSUMPTIONS:
  - Operating in a general context
SOCRATIC:
  - What evidence supports this claim?
APHORISMS:
  - Cite or abstain.
ENFORCEMENT: Obey or abstain. END CAPSULE
```

## 9) Docs to add/update

* `docs/BUNDLES_SCHEMA_v1.md` (above)
* `docs/PROFILES_REFERENCE.md` → add **projection** concept
* `docs/CAPSULE_SCHEMA_v1.md` → optional `severity`, optional `iri`, `sameAs`
* `docs/QUICKSTART.md` → how to pick a projection; “short vs full” modes
* `docs/LLMS_INTEGRATION_GUIDE.md` → emphasize short prompts + control tables

## 10) Quick backlog (high impact, low friction)

* [ ] Add `--projection` to composer; default from profile; allow CLI override
* [ ] Switch `capsules/**.yaml` recursive load; add domain/path consistency lint
* [ ] Implement control-table compiler (dedupe + priority)
* [ ] Extend manifest with projection + hashes + abstain policy
* [ ] Add `schemas/bundle.schema.v1.json`; validate in linter
* [ ] Write `docs/BUNDLES_SCHEMA_v1.md` and update guides
* [ ] Add `severity` + `stop_on_fail` semantics and show in CI profile
* [ ] Add `--compact` flag to composer to drop pedagogy entirely for CI

---

Alright—here’s the “hand-it-to-VSCode-LLM” spec. It’s explicit, linear, and testable. If the agent does each step and checks the acceptance boxes, you’ll land a clean update without breaking anything.

# Truth-Capsules v1.1 — Implementation Task Spec (Idiot-Proof)

## 0) Goal & Scope (what changes)

Implement four functional upgrades + hygiene:

1. **Profile-aware projections**: profiles decide *which capsule fields* get rendered and how (plus `--projection` override).
2. **Recursive capsules/** support: allow subfolders without breaking ids or existing tooling.
3. **Bundle schema v1.1**: richer bundles (excludes, priority overrides, optional projection, explicit order). Validate in linter and composer.
4. **Control-table compiler**: compact “Capsule Control Table” summarizing priorities & directives to improve adherence.
5. **Manifest expansion**: include profile/projection, bundle versions, capsule file hashes, composer version, abstain/ask-one policy.
6. **Docs refresh**: add bundle schema doc; update profiles reference, quickstart, readme.

Everything else (KG export, Neo4j loaders, existing bundles/capsules) must keep working.

---

## 1) Setup

* Baseline checks must pass **before** edits:

  * `python scripts/capsule_linter.py capsules` → `errors: 0`
  * `python scripts/compose_capsules_cli.py --root . --list-profiles`
  * `python scripts/compose_capsules_cli.py --root . --list-bundles`
  * `python scripts/export_kg.py` → writes `artifacts/out/capsules.ttl` & `.ndjson`

**Acceptance**: all commands run green.

---

## 2) Add Profile-Aware Projections

### 2.1 Profile schema: new `response.projection` block

* For each `profiles/*.yaml`, allow:

```yaml
response:
  system_block: |  # keep existing if present
    (existing text)
  projection:
    include:
      - title
      - statement
      - assumptions[:5]
      - pedagogy.socratic[:3]
      - pedagogy.aphorisms[:3]
    render:
      capsule_header: "BEGIN CAPSULE id={id} v={version} domain={domain}"
      assumption_bullet: "  - {text}"
      enforcement_footer: "ENFORCEMENT: Obey or abstain. END CAPSULE"
```

* Add to **conversational** profile; others can inherit a minimal projection (e.g., CI drops pedagogy).

### 2.2 CLI flags

* Extend `scripts/compose_capsules_cli.py`:

  * `--projection <name>` (optional): `default` uses the profile’s `response.projection`. If provided, look up `profiles/projections/<name>.yaml` (new dir) or a built-in map. If not found, error cleanly.
  * `--compact` (optional bool): when set, ignore pedagogy entirely (override projection include list at runtime).

### 2.3 Composer: projection application

* Implement a small helper inside the composer:

  * Normalize capsule fields (id, version, domain, title, statement, assumptions, pedagogy).
  * Respect `include` and field slicing semantics: `assumptions[:N]`, `pedagogy.socratic[:N]`, `pedagogy.aphorisms[:N]`.
  * Render using `render` strings when present; else fall back to current formatting.

**Acceptance**

* Command:
  `python scripts/compose_capsules_cli.py --root . --profile conversational --bundle conversation_red_team_baseline_v1 --out /tmp/p.txt`

  * Output contains projection-limited fields.
* Command with override:
  `python scripts/compose_capsules_cli.py --root . --profile conversational --bundle conversation_red_team_baseline_v1 --projection ci --out /tmp/p2.txt`

  * Output excludes pedagogy and is visibly shorter.
* `--compact` produces an even smaller prompt.

---

## 3) Recursive `capsules/**` Support

### 3.1 Loader change

* In `compose_capsules_cli.py` and any tool that scans capsules:

  * Replace `glob("capsules/*.yaml")` with `glob("capsules/**/*.yaml", recursive=True)`.

### 3.2 Linter improvement (optional warning)

* In `scripts/capsule_linter.py`, if the file is under `capsules/<folder>/...` and the YAML field `domain:` exists, warn if `<folder>` ≠ `domain`.

**Acceptance**

* Create `capsules/llm/llm.citation_required_v1.yaml` (move the file there).
* `python scripts/capsule_linter.py capsules` → still `errors: 0`, and optional domain/path warnings are fine.
* Compose a prompt including that capsule; it still resolves by `id`, not path.

---

## 4) Bundle Schema v1.1 (+ validation)

### 4.1 Add schema file

* New: `schemas/bundle.schema.v1.json` with:

```json
{
  "$schema":"http://json-schema.org/draft-07/schema#",
  "title":"Truth Capsule Bundle v0.1",
  "type":"object",
  "required":["name","version","capsules"],
  "properties":{
    "name":{"type":"string"},
    "version":{"type":"string"},
    "applies_to":{"type":"array","items":{"type":"string"}},
    "capsules":{"type":"array","items":{"type":"string"}},
    "excludes":{"type":"array","items":{"type":"string"}},
    "priority_overrides":{"type":"object","additionalProperties":{"type":"integer"}},
    "projection":{"type":"string"},
    "order":{"type":"array","items":{"type":"string"}},
    "tags":{"type":"array","items":{"type":"string"}},
    "notes":{"type":"string"}
  }
}
```

### 4.2 Update composer to apply bundle features

* Load bundle(s); validate against schema (use `jsonschema`, optional `--strict-bundles`).
* Apply in this order:

  1. Start with `capsules` (list).
  2. Apply `excludes` (remove by id).
  3. Apply `order` if provided (reorder; others append in original order).
  4. Capture `priority_overrides` for control table (next section).
  5. If bundle has `projection`, override profile projection for this composition.

**Acceptance**

* Add a test bundle `bundles/conversation_red_team_plus_v1.yaml`:

  * Inherit the baseline capsules, add an `excludes` of one capsule, and set `projection: ci`.
* Compose with that bundle; verify the excluded capsule is gone, projection changed.

---

## 5) Control-Table Compiler

### 5.1 Heuristics (simple & robust)

* For each selected capsule, derive a `(priority, directive)` row:

  * Priority rules (lower number = higher priority):

    * `llm.safety_refusal_guard_v1`: 1
    * `llm.pii_redaction_guard_v1`: 2
    * `llm.citation_required_v1`: 3
    * `llm.plan_verify_answer_v1`: 4
    * else: default 5
  * Apply `bundle.priority_overrides` if present.
  * Directive templates:

    * safety → `FORBID unsafe outputs`
    * pii → `FORBID raw PII`
    * citations → `MUST cite or abstain`
    * plan/verify → `MUST Plan→Verify→Answer`
    * else → `SEE capsule statement`
* De-dupe rows; sort by priority then id.

### 5.2 Rendering

* Insert a table after the system preamble:

```
SYSTEM: Capsule Control Table (compiled)
| Pri | Capsule ID                   | Directive                  |
|-----|------------------------------|----------------------------|
| 1   | llm.safety_refusal_guard_v1  | FORBID unsafe outputs      |
| 2   | llm.pii_redaction_guard_v1   | FORBID raw PII             |
| 3   | llm.citation_required_v1     | MUST cite or abstain       |
| 4   | llm.plan_verify_answer_v1    | MUST Plan→Verify→Answer    |
```

**Acceptance**

* Compose conversational bundle; ensure the table appears and reflects actual included capsules and overrides.

---

## 6) Manifest Expansion

### 6.1 Add fields

When writing `--manifest`, include:

```json
{
  "profile": "<id>",
  "profile_version": "<profile.version>",
  "projection": "<resolved-name-or 'default'>",
  "bundles": [{"name":"<name>","version":"<version>"}],
  "capsules": [{"id":"...","file":"<path>","sha256":"<hash>"}],
  "composer_version": "<semver, hardcode '1.1.0' for now>",
  "abstain_policy": "ask-one-then-abstain",
  "generated_at": "2025-11-07T..Z"
}
```

* Compute file SHA256 for each capsule path.

**Acceptance**

* Compose with `--manifest /tmp/m.json`; inspect keys & hashes present.

---

## 7) CLI Compatibility & New Flags

* Keep existing behavior when projections are absent (backward-compatible).
* New flags:

  * `--projection <name>` (optional)
  * `--compact` (optional)
  * `--strict-bundles` (optional)
* Update `--list-bundles` to print bundle version and optional projection.

**Acceptance**

* `--list-bundles` shows versions.
* Compositions without new flags still mirror v1 output (ignoring the control table addition if you choose to keep it behind `--control-table` flag; recommended default = ON for conversational, OFF for CI).

---

## 8) Linter: Bundle Validation

* Create `scripts/bundle_linter.py` (simple utility):

  * Validates each `bundles/*.yaml` against `schemas/bundle.schema.v1.json`.
  * Checks that each `capsules` id resolves and prints missing ids.
* Add to CI (optional): `.github/workflows/capsules-lint.yml` → run bundle_linter after capsule_linter.

**Acceptance**

* `python scripts/bundle_linter.py bundles` → `errors: 0`.

---

## 9) Docs & README Updates

* New: `docs/BUNDLES_SCHEMA_v1.md` (explain fields with examples).
* Update: `docs/PROFILES_REFERENCE.md` to document `response.projection` and the new `profiles/projections/` directory if you add it.
* Update: `docs/QUICKSTART.md`—show `--projection` and `--compact`.
* Update: `README.md`—mention control table and richer bundles.
* Update: `docs/LLMS_INTEGRATION_GUIDE.md`—recommend short prompts + control table for adherence.

**Acceptance**

* Run a quick docs link check (manual hover in VSCode is fine).
* README “Project Structure” shows `schemas/bundle.schema.v1.json` and (optionally) `profiles/projections/`.

---

## 10) Tests (minimal but meaningful)

Create/extend tests under `tests/`:

1. **Projection unit test**

   * Input: 1 capsule with title/statement/assumptions/pedagogy.
   * Profile: conversational projection as above.
   * Assert output contains sliced assumptions/pedagogy and render strings.

2. **Recursive discovery test**

   * Put a capsule under `capsules/llm/`.
   * Ensure `index_capsules` picks it up; compose includes it by `id`.

3. **Bundle schema validation test**

   * Good bundle (v1.1 fields) passes; bad bundle (unknown field type) fails in strict mode.

4. **Control table test**

   * With four known capsules, assert table rows appear, sorted by priority.

5. **Manifest test**

   * Compose with `--manifest`; assert required keys and that the listed file hashes match `sha256sum`.

6. **Golden snapshot**

   * For `conversation_red_team_baseline_v1`, write prompt to `tests/gold/conversation_red_team.txt`.
   * Test ensures a stable header + control table presence (allowing flexible capsule order if you don’t lock it).

**Acceptance**

* `pytest -q` (or simple Python asserts in a runner script) → all green.

---

## 11) Backward-Compatibility Checklist

* Old bundles without `version` still load (set version to `"1.0.0"` default at read time).
* Old profiles without `projection` still render via legacy path.
* `compose_capsules_cli.py` without new flags still works.
* KG export unaffected (capsule YAML untouched structurally).

**Acceptance**

* Re-run:

  * `python scripts/export_kg.py` → produces files in `artifacts/out/`.
  * Neo4j loader you used earlier still imports 24 capsules.

---

## 12) Error Handling & UX

* Composer:

  * If bundle declares `projection` not found: exit 2 with helpful message and `--list-profiles`.
  * If `--projection` is unknown: same behavior.
  * If capsules from bundle don’t resolve: print warnings and continue **unless** `--strict-bundles`; then fail.
* Linter:

  * Domain/path mismatch → WARNING only.
  * Unknown bundle fields → ERROR in strict mode, WARNING otherwise.

---

## 13) Deliverables & PR Checklist

* [ ] Code: `compose_capsules_cli.py` (projection, recursive, control table, manifest)
* [ ] New: `schemas/bundle.schema.v1.json`
* [ ] New: `scripts/bundle_linter.py`
* [ ] Profile updates: add `response.projection` to `profiles/conversational.yaml` (and optionally others)
* [ ] Tests under `tests/` (as above)
* [ ] Docs: `docs/BUNDLES_SCHEMA_v1.md`, updates to README/QUICKSTART/PROFILES_REFERENCE/LLMS_INTEGRATION_GUIDE
* [ ] Changelog: add `1.1.0` with bullet points
* [ ] Version bump: composer “composer_version”: `"1.1.0"`

**Definition of Done**

* All acceptance checks in sections 2–12 pass locally.
* `capsule_linter.py`, `bundle_linter.py`, `export_kg.py` run green.
* `compose_capsules_cli.py` can:

  * render legacy output,
  * render projection-aware output,
  * render compact output,
  * emit a control table,
  * produce a richer manifest.

---

## 14) Command Cheat-Run (for the implementer)

```bash
# Lint (pre)
python scripts/capsule_linter.py capsules

# List profiles/bundles
python scripts/compose_capsules_cli.py --root . --list-profiles
python scripts/compose_capsules_cli.py --root . --list-bundles

# Compose (default)
python scripts/compose_capsules_cli.py --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out artifacts/out/prompt_default.txt \
  --manifest artifacts/out/manifest_default.json

# Compose (projection override + compact)
python scripts/compose_capsules_cli.py --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --projection ci \
  --compact \
  --out artifacts/out/prompt_ci_compact.txt \
  --manifest artifacts/out/manifest_ci.json

# Validate bundles
python scripts/bundle_linter.py bundles

# Export KG (sanity check unchanged)
python scripts/export_kg.py
ls -l artifacts/out/capsules.ttl artifacts/out/capsules.ndjson
```

---

## 15) Pitfalls & Guardrails

* **Don’t** change capsule YAML schema—projection is a *profile/bundle* concern.
* **Do** keep ids canonical; file moves must not alter ids.
* **Don’t** hard-code table rows for unknown capsules; fall back to “SEE capsule statement”.
* **Do** fail fast with human messages when projections are missing or bundles invalid in strict mode.

---

