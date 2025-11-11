# Truth Capsules v0.1 — informational & witnessed knowledge packs

**Curation-first, executable prompt library for LLMs — with optional signed receipts.**

A **Truth Capsule** is a tiny, versioned **YAML** object that encodes **rules, methods, assumptions, and pedagogy** (Socratic prompts + aphorisms). You can use capsules in **two lanes**:

* **Informational capsules** → compose great **system prompts** from curated bundles/profiles (for prompting, pedagogy, process).
* **Witnessed capsules** → run **executable checks** and emit **cryptographically-signed receipts** (for CI, policy, audits).

**Project status:** v0.1.0 (PoC) — feedback welcome

---

## Pick your lane

| Lane              | What you get                                                   | Typical uses                                          | Try it in 60s                                     | Buy                                                                   |
| ----------------- | -------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------- |
| **Informational** | Curated, deterministic **system prompts** + manifest lockfiles | Prompt profiles, pedagogy packs, process checklists   | Generate SPA and compose a prompt                 | *Creator Pack (YouTube/Twitch)* → **[Buy](STRIPE_CREATOR_PACK_LINK)** |
| **Witnessed**     | **GREEN/RED** results + **detached Ed25519 signature** per run | “Cite or abstain”, JSON-contract, safety/policy gates | `make witness-sandbox` (GREEN/RED examples below) | *Signed-Receipts Pilot* → **[Buy](STRIPE_PILOT_LINK)**                |

> Also available: **Day-rate contracting** (£450) → **[Book](STRIPE_DAY_RATE_LINK)** · **Sponsorship** ($1000) → **[Support](STRIPE_SPONSOR_LINK)**

---

## One-minute demo

### A) Informational lane (compose a prompt)

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
```

### B) Witnessed lane (GREEN/RED + signed receipts)

**1) Generate dev keys (one-time)**

```bash
make keygen
# writes:
#   keys/dev_ed25519_sk.pem  (private)
#   keys/dev_ed25519_pk.pem  (public)
```

**2) GREEN case** (citations present)

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org>
```

**3) RED case** (missing citations)

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org> \
  ALLOW_RED=1   # exit 0 but still shows RED
```

**Outputs** (under `artifacts/out/`)

* `witness_*.json` — raw results (JSON array)
* `witness_*.signed.json` — results wrapped with
  `proof { type: "Ed25519", created, keyId, canonical { algo, hash, digest }, signature }`
* `witness_*.sig` — detached base64 signature of canonical JSON

**Verify a signed receipt**

```bash
# Verify the most recent signed receipt with your public key
python scripts/verify_witness.py \
  --pub keys/dev_ed25519_pk.pem \
  artifacts/out/witness_YYYYMMDDTHHMMSSZ.signed.json
```

> Details: **docs/SIGNED_WITNESSES.md** and **docs/WITNESS_SANDBOX.md**

---

## Why Truth Capsules (in 3 bullets)

* **Receipts, not vibes** — Reproducible prompts and **signed** witness results.
* **Low ceremony** — Plain YAML + CLI + one-file SPA; copy-paste in minutes.
* **Composable** — The same capsule feeds prompts *and* CI/policy without divergence.

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
# Optional: local LLM runner
# pipx install llm   # https://llm.datasette.io
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
make keygen
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

**Publish as GitHub Pages (zero infra)**

```bash
# Generates SPA into /docs for Pages hosting
python scripts/spa/generate_spa.py --root . --output docs/index.html
# Then enable: Settings → Pages → Deploy from branch → /docs
```

---

## Knowledge-graph readiness

Truth Capsules ship with **first-class graph tooling**:

* JSON-LD context (`contexts/`), RDFS ontology (`ontology/`), SHACL shapes (`shacl/`)
* RDF/Turtle + NDJSON-LD export (`scripts/export_kg.py`)
* SPARQL queries (`queries/`), minimal Neo4j loader (`scripts/load_neo4j.cypher`)

```bash
python scripts/export_kg.py
# artifacts/out/capsules.ttl
# artifacts/out/capsules.ndjson
```

> End-to-end examples: **docs/KG_README.md**

---

## Security model (witness sandbox)

* **Containerized** with `--read-only`, `--cap-drop=ALL`, `--pids-limit`, `--network=none`, tmpfs for `/tmp`
* **Inputs by env vars** (`ENV_VARS="-e KEY=VAL ..."`) and read-only mounts
* **No secrets in capsules**; keys live in `./keys/` and are ignored by git

Build & smoke test the runner:

```bash
make sandbox-image
make sandbox-smoke
```

---

## Documentation

* **Getting started:** **docs/QUICKSTART.md**
* **One-Pager (pitch):** **docs/ONE_PAGER.md**
* **Profiles Reference:** **docs/PROFILES_REFERENCE.md**
* **Capsule Schema v1:** **docs/CAPSULE_SCHEMA_v1.md**
* **Migration & Schema Updates:** **docs/MIGRATION_GUIDE.md**
* **Witnesses Guide:** **docs/WITNESSES_GUIDE.md**
* **Provenance & Signing:** **docs/PROVENANCE_SIGNING.md**
* **Security & CSP:** **docs/SECURITY.md**
* **CI Guide:** **docs/CI_GUIDE.md**
* **KG README:** **docs/KG_README.md**
* **Signed witnesses walk-through:** **docs/SIGNED_WITNESSES.md**
* **Witness sandbox quickref:** **docs/WITNESS_SANDBOX.md**

---

## Project structure

```
truth-capsules/
├── artifacts/
│   ├── examples/                # Input fixtures (GREEN/RED)
│   └── out/                     # Generated outputs (KG, receipts)
│       ├── capsules.ttl
│       ├── capsules.ndjson
│       ├── witness_*.signed.json   # <-- signed receipts
│       └── ...
├── bundles/                     # Capsule sets
├── capsules/                    # YAML capsules (23 + 1 signed example)
├── docs/                        # Full documentation
├── profiles/                    # 7 context profiles
├── scripts/                     # CLI & utilities
│   ├── capsule_linter.py
│   ├── compose_capsules_cli.py
│   ├── run_witnesses.py
│   ├── sign_witness.py          # <-- signs witness results (Ed25519)
│   ├── verify_witness.py        # <-- verifies witness signatures
│   └── spa/
│       ├── generate_spa.py
│       └── template.html
└── ...
```

---

## Available capsules (23 + 1 signed example)

**LLM behavior & reasoning (11):**
`llm.citation_required_v1`, `llm.plan_verify_answer_v1`, `llm.red_team_assessment_v1`, `llm.counterfactual_probe_v1`, `llm.steelmanning_v1`, `llm.five_whys_root_cause_v1`, `llm.fermi_estimation_v1`, `llm.assumption_to_test_v1`, `llm.evidence_gap_triage_v1`, `llm.bias_checklist_v1`, `llm.plan_backtest_v1`

**PR review & code (5):**
`llm.pr_diff_first_v1`, `llm.pr_risk_tags_v1`, `llm.pr_test_hints_v1`, `llm.pr_deploy_checklist_v1`, `llm.pr_change_impact_v1`

**Safety & compliance (3):**
`llm.pii_redaction_guard_v1`, `llm.safety_refusal_guard_v1`, `llm.tool_json_contract_v1`

**Business & ops (3):**
`business.decision_log_v1`, `ops.rollback_plan_v1`, `llm.judge_answer_quality_v1`

**Meta (1):**
`pedagogy.problem_solving_v1`

**Signed example:**
`llm.citation_required_v1_signed.yaml`

---

## CI workflows

* `capsules-lint.yml` — Lint on push/PR
* `capsules-compose.yml` — Compose artifacts for bundles
* `capsules-llm-judge.yml` — Optional LLM-as-judge eval
* `capsules-policy.yml` — Gate on `review.status=approved`
* `kg-smoke.yml` — Export KG + SHACL validation

See **docs/CI_GUIDE.md**.

---

## Pricing & services

* **Creator Pack (Informational)** — bespoke prompt profile + capsule bundle for your channel.
* **Signed-Receipts Pilot (Witnessed)** — install one or two executable checks with receipts.
* **Day-rate contracting** — £450/day for rapid capsule curation & integration.
* **Sponsorship** — $1000 one-off to accelerate open-source capsules & docs.

> Stripe links live at the top of this README.

---

## License

MIT — see **LICENSE**. Commercial use encouraged; attribution welcomed.

---

## Status & roadmap

**v0.1.0 PoC (current)**
✅ 23 capsules (+1 signed example) · ✅ CLI tools · ✅ KG export · ✅ GH Actions · ✅ Snapshot SPA

**Post-v1 (feedback-driven)**
[ ] Signature verification in CI · [ ] PR comment bot · [ ] SPA provenance panel
[ ] Live SPA dev server · [ ] Secrets-handling capsules · [ ] Capsule search & tags
[ ] VS Code extension · [ ] Community capsule gallery

---

## Contact

Issues / Discussions on GitHub.
Professional services: see Stripe links above or repo contact.

*Last updated:* 2025-11-09
