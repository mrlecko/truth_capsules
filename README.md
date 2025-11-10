This is strong—but the opening doesn’t yet land the “two lanes” story or show a signed GREEN/RED in under a minute. Here’s a **drop-in README** that does both, keeps your current sections, and adds clear CTAs. Replace your README.md with this and tweak the Stripe links + video URLs.

---

````markdown
# Truth Capsules v0.1 — informational & witnessed knowledge packs

**Curation-first, executable prompt library for LLMs — with optional signed receipts.**

A *Truth Capsule* is a tiny, versioned **YAML** object that encodes **rules, methods, assumptions, and pedagogy** (Socratic prompts + aphorisms). You can use capsules in two lanes:

- **Informational capsules** → compose great **system prompts** from curated bundles/profiles (for prompting, pedagogy, process).
- **Witnessed capsules** → run **executable checks** and emit **cryptographically-signed receipts** (for CI, policy, audits).

**Status:** v0.1.0 — PoC, feedback welcome

---

## Pick your lane

| Lane | What you get | Typical uses | How to try | Buy |
|---|---|---|---|---|
| **Informational** | Curated, deterministic **system prompts** with manifests | Prompt profiles, pedagogy packs, process checklists | Generate SPA and compose a prompt in 60s | *Creator Pack* (YouTube/Twitch) → **[Buy](<STRIPE_CREATOR_PACK_LINK>)** |
| **Witnessed** | **GREEN/RED** results + **detached Ed25519 signature** for each run | “Cite or abstain”, JSON-contract, safety/policy gates | Run `witness-sandbox` (GREEN/RED examples below) | *Signed-Receipts Pilot* → **[Buy](<STRIPE_PILOT_LINK>)** |

> Also available: **Day-rate contracting** (£450) → **[Book](<STRIPE_DAY_RATE_LINK>)** · **Sponsorship** ($1000) → **[Support](<STRIPE_SPONSOR_LINK>)**

---

## One-minute demo

### Informational lane (compose a prompt)

```bash
# 1) (One-time) deps
pip install -r requirements.txt

# 2) Compose conversational prompt from a bundle
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out prompt.txt \
  --manifest prompt.manifest.json

# 3) Paste prompt.txt into your LLM of choice
````

### Witnessed lane (GREEN/RED + signed receipts)

**GREEN case** (citations present):

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org>
```

**RED case** (missing citations):

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org> \
  ALLOW_RED=1  # exit 0 but still shows RED
```

**Outputs** (saved under `artifacts/out/`):

* `witness_*.json` — raw results (JSON array)
* `witness_*.signed.json` — results wrapped with `proof { type: "Ed25519", created, keyId, digest, signature }`
* `witness_*.sig` — detached base64 signature of canonical JSON

> See **[docs/PROVENANCE_SIGNING.md](docs/PROVENANCE_SIGNING.md)** for verifying signatures and trust model.

---

## Why Truth Capsules (in 3 bullets)

* **Receipts, not vibes** — Reproducible prompts and **signed** witness results.
* **Low ceremony** — Plain YAML + CLI + one-file SPA; copy-paste in minutes.
* **Composable** — Same capsule feeds prompts *and* CI/policy without divergence.

---

## Key features

* ✅ **23 Capsules (+1 signed example)** — PR review, red-team, safety, reasoning, business rules
* ✅ **Deterministic composition** — Manifests/lockfiles for reproducibility
* ✅ **Profile system** — 7 contexts (conversational, CI, code assistant, pedagogy…)
* ✅ **Bundle curation** — Pre-composed capsule sets
* ✅ **Executable witnesses** — Automated validations for **GREEN/RED**
* ✅ **Provenance & signing** — Ed25519 receipts for audit trails
* ✅ **Pedagogy-first** — Socratic prompts + aphorisms
* ✅ **CLI tools** — Linter, composer, witness runner, **sign/verify**, **KG export**
* ✅ **CI integration** — Lint, compose, KG smoke, (optional) LLM-as-judge
* ✅ **Snapshot SPA** — Visual composer + digest check
* ✅ **Knowledge-graph ready** — RDF/Turtle, NDJSON-LD, JSON-LD, Ontology (RDFS), SHACL, SPARQL, Neo4j loader

---

## Quick start (full)

```bash
pip install -r requirements.txt
# Optional: llm runner
# pipx install llm  # https://llm.datasette.io
```

**Lint capsules**

```bash
python scripts/capsule_linter.py capsules
# Capsules: 23  errors: 0  warnings: 0
```

**Discover profiles & bundles**

```bash
python scripts/compose_capsules_cli.py --root . --list-profiles
python scripts/compose_capsules_cli.py --root . --list-bundles
```

**Compose prompts (informational lane)**

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out prompt.txt \
  --manifest prompt.manifest.json
```

**Witness run + signed receipts (witnessed lane)**

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org>
```

---

## Snapshot SPA (compose visually)

```bash
python scripts/spa/generate_spa.py --root . --output capsule_composer.html
# Open capsule_composer.html → select profile/bundles → copy the generated prompt
```

* Validates capsule digests client-side (SHA-256 of a canonical core).
* Exports manifests, share links, and ready-to-run `llm` CLI commands.

---

## Knowledge-graph readiness

Truth Capsules ship with **first-class graph tooling**:

* JSON-LD context (`contexts/`), RDFS ontology (`ontology/`), SHACL shapes (`shacl/`)
* RDF/Turtle + NDJSON-LD export (`scripts/export_kg.py`)
* SPARQL queries (`queries/`), minimal Neo4j loader (`scripts/load_neo4j.cypher`)

```bash
python scripts/export_kg.py
# artifacts/out/capsules.ttl, artifacts/out/capsules.ndjson
```

> See **[docs/KG_README.md](docs/KG_README.md)** for end-to-end examples.

---

## Documentation

* **[Quickstart](docs/QUICKSTART.md)** — 5-minute setup
* **[One-Pager](docs/ONE_PAGER.md)** — Elevator pitch & use cases
* **[Profiles Reference](docs/PROFILES_REFERENCE.md)** — All 7 profiles & aliases
* **[Capsule Schema v1](docs/CAPSULE_SCHEMA_v1.md)** — YAML fields
* **[Witnesses Guide](docs/WITNESSES_GUIDE.md)** — Execution & sandboxing
* **[Provenance & Signing](docs/PROVENANCE_SIGNING.md)** — Trust model (+ verification)
* **[Security & CSP](docs/SECURITY_CSP.md)**, **[SECURITY.md](docs/SECURITY.md)** — Isolation & threat model
* **[CI Guide](docs/CI_GUIDE.md)** — GitHub Actions workflows
* **[SPA README](scripts/spa/README.md)** — Composer details

---

## Project structure

```
truth-capsules-v1/
├── artifacts/
│   ├── examples/                # Input fixtures (GREEN/RED)
│   └── out/                     # Generated outputs (KG, receipts)
│       ├── capsules.ttl
│       ├── capsules.ndjson
│       ├── witness_*.signed.json   # <-- signed receipts
│       └── ...
├── bundles/                     # Capsule sets
├── capsules/                    # YAML capsules (23 + 1 signed example)
├── docs/                        # Documentation
├── profiles/                    # 7 context profiles
├── scripts/                     # CLI & utilities
│   ├── capsule_linter.py
│   ├── compose_capsules_cli.py
│   ├── run_witnesses.py
│   ├── sign_witness.py          # <-- signs witness results (Ed25519)
│   └── spa/
│       ├── generate_spa.py
│       └── template.html
└── ...
```

---

## Available capsules (23 + 1 signed example)

**LLM behavior & reasoning (11):** `llm.citation_required_v1`, `llm.plan_verify_answer_v1`, `llm.red_team_assessment_v1`, `llm.counterfactual_probe_v1`, `llm.steelmanning_v1`, `llm.five_whys_root_cause_v1`, `llm.fermi_estimation_v1`, `llm.assumption_to_test_v1`, `llm.evidence_gap_triage_v1`, `llm.bias_checklist_v1`, `llm.plan_backtest_v1`

**PR review & code (5):** `llm.pr_diff_first_v1`, `llm.pr_risk_tags_v1`, `llm.pr_test_hints_v1`, `llm.pr_deploy_checklist_v1`, `llm.pr_change_impact_v1`

**Safety & compliance (3):** `llm.pii_redaction_guard_v1`, `llm.safety_refusal_guard_v1`, `llm.tool_json_contract_v1`

**Business & ops (3):** `business.decision_log_v1`, `ops.rollback_plan_v1`, `llm.judge_answer_quality_v1`

**Meta (1):** `pedagogy.problem_solving_v1`

**Signed example:** `llm.citation_required_v1_signed.yaml`

---

## CI workflows

* `capsules-lint.yml`: Lint on push/PR
* `capsules-compose.yml`: Compose artifacts for bundles
* `capsules-llm-judge.yml`: Optional LLM-as-judge eval
* `capsules-policy.yml`: Gate on `review.status=approved`
* `kg-smoke.yml`: Export KG + SHACL validation

See **[CI_GUIDE.md](docs/CI_GUIDE.md)**.

---

## Pricing & services

TBD

---

## License

MIT — see **[LICENSE](LICENSE)**. Commercial use encouraged; attribution welcomed.

---

## Status & roadmap

**v0.1.0 PoC (current)**
✅ 24 capsules (+1 signed example) · ✅ CLI tools · ✅ KG export · ✅ GH Actions · ✅ Snapshot SPA

**Post-v1 (feedback-driven)**
[ ] Signature verification in CI · [ ] PR comment bot · [ ] SPA provenance panel · [ ] Live SPA dev server · [ ] Secrets-handling capsules · [ ] Capsule search & tags · [ ] VS Code extension · [ ] Community gallery

---

## Contact

Issues / Discussions on GitHub.
Professional services: see Stripe links above or repo contact.

*Last updated:* 2025-11-09


