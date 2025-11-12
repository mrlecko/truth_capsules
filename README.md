```
Assumption: You want a drop-in replacement for README.md that reflects the directory tree you pasted (accurate counts, updated examples, and current capsule/profile/bundle lists).

🧭 Mode=Basic | 🧠 Depth=3 | 🧪 Rigor=Medium | 📄 Scope=1-page | 🕒 Recency=optional | ⏸ Stop-at=— | 📡 Adapter=Chat
(quick change ⇒ “Mode: Deep · Depth: 5 · Rigor: High · Scope: YAML skeleton · Recency: required · Stop at S2 · Adapter: PR”)
```

Here’s an updated `README.md` you can paste over the current one. I’ve refreshed all counts and examples to match the tree you provided (as of **2025-11-12**).

---

# Truth Capsules v0.1 — informational & witnessed knowledge packs

**Curation-first, executable prompt library for LLMs — with optional signed receipts.**

A **Truth Capsule** is a tiny, versioned **YAML** object that encodes **rules, methods, assumptions, and pedagogy** (Socratic prompts + aphorisms). You can use capsules in **two lanes**:

* **Informational capsules** → compose great **system prompts** from curated bundles/profiles (for prompting, pedagogy, process).
* **Witnessed capsules** → run **executable checks** and emit **cryptographically-signed receipts** (for CI, policy, audits).

**Project status:** v0.1.0 (PoC) — feedback welcome

---

## Repo quick stats (from the current tree)

* **50 capsules** across 5 groups — CI (5), Dev (8), **MacGyver** (29), Support (7), Meta (1)
* **4 bundles** (`bundles/`), **4 profiles** (`profiles/`)
* **24 example inputs** (`artifacts/examples/…`)
* **CLI/tools:** 18 Python scripts + 5 shell helpers (`scripts/`)
* **Graph tooling:** 11 Cypher + 3 SPARQL queries (`extras/cypher_queries/`)
* **Schemas:** 7 JSON schemas (`schemas/`)
* **LLM templates:** 3 ready-to-use provider configs (`llm_templates/`)
* **Ontology & shapes:** 1 JSON-LD context, 1 RDFS/Turtle ontology, 1 SHACL shape

---

## Pick your lane

| Lane              | What you get                                                   | Typical uses                                          | Try it in 60s                           |
| ----------------- | -------------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------- |
| **Informational** | Curated, deterministic **system prompts** + manifest lockfiles | Prompt profiles, pedagogy packs, process checklists   | Generate SPA and compose a prompt       |
| **Witnessed**     | **GREEN/RED** results + **detached Ed25519 signature** per run | “Cite or abstain”, JSON-contract, safety/policy gates | `make witness-sandbox` (examples below) |

> Services available: Day-rate contracting · Pilot installs · Sponsorship. (See repo discussions or contact.)

---

## One-minute demo

### A) Informational lane (compose a prompt)

```bash
# 1) Deps
pip install -r requirements.txt

# 2) Generate the SPA snapshot (local composer)
python scripts/spa/generate_spa.py --root . --output capsule_composer.html
# Open capsule_composer.html → pick a profile + bundles → copy the prompt
```

Or via CLI:

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational_macgyver \
  --bundle macgyverisms_v1 \
  --out prompt.txt \
  --manifest prompt.manifest.json
```

### B) Witnessed lane (GREEN/RED + signed receipts)

**1) Keys (one-time)**

```bash
make keygen
# writes keys/dev_ed25519_sk.pem (private) & keys/dev_ed25519_pk.pem (public)
```

**2) Example: diff risk tags (Dev)**

```bash
# Likely GREEN: “no-risk” patch
make witness-sandbox CAPSULE=dev.diff_risk_tags_v1 WITNESS=diff_has_expected_risk_tags JSON=1 \
  ENV_VARS="-e DIFF_PATH=artifacts/examples/pr_diff_norisk.patch" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org>

# Likely RED: risky patch
make witness-sandbox CAPSULE=dev.diff_risk_tags_v1 WITNESS=diff_has_expected_risk_tags JSON=1 \
  ENV_VARS="-e DIFF_PATH=artifacts/examples/pr_diff.patch" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org> ALLOW_RED=1
```

**3) Example: PII redaction smoke (Support)**

```bash
make witness-sandbox CAPSULE=support.pii_redaction_smoke_v1 WITNESS=pii_is_redacted JSON=1 \
  ENV_VARS="-e INPUT_PATH=artifacts/examples/pii_ok.json"
```

**4) Example: SBOM present (CI)**

```bash
make witness-sandbox CAPSULE=ci.sbom_present_v1 WITNESS=sbom_file_exists JSON=1 \
  ENV_VARS="-e SBOM_PATH=artifacts/examples/ci/sbom.json"
```

**Verify a signed receipt**

```bash
python scripts/verify_witness.py \
  --pub keys/dev_ed25519_pk.pem \
  artifacts/out/witness_YYYYMMDDTHHMMSSZ.signed.json
```

Outputs land under `artifacts/out/`:

* `witness_*.json` — raw results
* `witness_*.signed.json` — result + detached-signature envelope
* `witness_*.sig` — detached base64 signature

More: **docs/witnesses/WITNESS_SANDBOX.md**, **docs/witnesses/SIGNED_WITNESSES.md**

---

## Why Truth Capsules (in 3 bullets)

* **Receipts, not vibes** — Reproducible prompts and **signed** witness results.
* **Low ceremony** — Plain YAML + CLI + one-file SPA; copy-paste in minutes.
* **Composable** — The same capsule feeds prompts *and* CI/policy without divergence.

---

## Key features

* ✅ **50 capsules** (CI 5 · Dev 8 · MacGyver 29 · Support 7 · Meta 1)
* ✅ **Profiles (4)** — `conversational_macgyver`, `dev.code_assistant`, `support_public_agent`, `ci.gates`
* ✅ **Bundles (4)** — `macgyverisms_v1`, `bundle.dev_code_assistant_v1`, `bundle.ci_quality_gates_v1`, `support_agent_v1_bundle`
* ✅ **Deterministic composition** — Manifests/lockfiles for reproducibility
* ✅ **Executable witnesses** — Automated **GREEN/RED** checks
* ✅ **Provenance & signing** — Ed25519 receipts for audit trails
* ✅ **CLI tools** — Linter, composer, witness runner, **sign/verify**, **KG export**
* ✅ **Knowledge-graph ready** — JSON-LD context, RDFS/Turtle ontology, SHACL, SPARQL, Neo4j helpers

---

## Snapshot SPA (compose visually)

```bash
python scripts/spa/generate_spa.py --root . --output docs/index.html
# Then enable GitHub Pages → /docs
```

The SPA validates capsule digests, exports manifests/share-links, and emits ready-to-run commands.

---

## Knowledge-graph readiness

```bash
python scripts/export_kg.py
# artifacts/out/capsules.ttl
# artifacts/out/capsules.ndjson
```

See **docs/graph/KG_README.md** and **extras/cypher_queries/** (11 Cypher, 3 SPARQL).

---

## Project structure (abridged)

```
truth-capsules/
├── artifacts/
│   ├── examples/                 # 24 input fixtures (CI/Dev/Support…)
│   └── out/                      # Generated outputs (KG, receipts)
├── bundles/                      # 4 curated bundles
├── capsules/                     # 50 capsules (CI 5, Dev 8, MacGyver 29, Support 7, Meta 1)
├── profiles/                     # 4 profiles
├── scripts/                      # 18 Python CLIs + 5 shell helpers (+ SPA generator)
├── llm_templates/                # 3 provider templates
├── extras/cypher_queries/        # 11 Cypher + 3 SPARQL
├── contexts/, ontology/, shacl/  # JSON-LD, RDFS/Turtle, SHACL
└── docs/                         # Guides, quickstarts, security, CI, witnesses
```

---

## Available capsules (by group)

**CI (5):**
`ci.container_hardening_v1`, `ci.license_compliance_v1`, `ci.reproducible_artifact_hash_v1`, `ci.sbom_present_v1`, `ci.secrets_in_build_env_v1`

**Dev (8):**
`dev.commit_conventions_v1`, `dev.diff_risk_tags_v1`, `dev.enforce_todo_ticket_v1`, `dev.prompt_safety_rules_v1`, `dev.review_checklist_v1`, `dev.secret_scan_baseline_v1`, `dev.style_guide_js_v1`, `dev.style_guide_python_v1`

**MacGyver (29):**
`macgyver.affordance_matrix_template_v1`, `macgyver.affordances_over_objects_v1`, `macgyver.bias_checklist_v1`, `macgyver.blast_radius_humility_v1`, `macgyver.chain_design_v1`, `macgyver.deception_force_multiplier_v1`, `macgyver.deliberate_practice_v1`, `macgyver.environment_as_component_v1`, `macgyver.fail_safe_defaults_v1`, `macgyver.five_rails_v1`, `macgyver.functional_fixedness_avoidance_v1`, `macgyver.inventory_thinking_v1`, `macgyver.latency_control_v1`, `macgyver.legal_ethical_guardrails_v1`, `macgyver.low_tech_first_v1`, `macgyver.mvp_mechanism_bias_v1`, `macgyver.parallel_options_v1`, `macgyver.problem_collapse_v1`, `macgyver.prompts_as_programs_v1`, `macgyver.prompt_skeleton_v1`, `macgyver.property_matching_v1`, `macgyver.rails_ledgers_hub_mapping_v1`, `macgyver.reality_check_v1`, `macgyver.redundancy_chokepoints_v1`, `macgyver.reflection_loop_v1`, `macgyver.sop_10min_loop_v1`, `macgyver.stock_verbs_v1`, `macgyver.transduction_chains_v1`, `macgyver.world_as_typed_graph_v1`

**Support (7):**
`support.billing_basics_v1`, `support.escalation_matrix_v1`, `support.intent_router_sanity_v1`, `support.knowledge_view_projection_v1`, `support.legal_privacy_rules_v1`, `support.pii_redaction_smoke_v1`, `support.tone_style_guide_v1`

**Meta (1):**
`meta.truth_capsules_v1`

---

## Docs you’ll want first

* **Quickstart:** `docs/QUICKSTART.md`, `docs/misc/QUICKSTART_SHIP_NEW_CAPSULE.md`
* **Profiles:** `docs/misc/PROFILES_REFERENCE.md`
* **Witnesses:** `docs/witnesses/WITNESSES_GUIDE.md`, `docs/witnesses/WITNESS_SANDBOX.md`
* **Security:** `docs/SECURITY.md`
* **CI:** `docs/ci/CI_GUIDE.md`
* **KG:** `docs/graph/KG_README.md`

---

## License

MIT — see **LICENSE**.

---

*Last updated:* **2025-11-12**
