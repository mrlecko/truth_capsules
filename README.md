# Truth Capsules v0.1

**Curation-first, executable prompt library for LLMs.**

Truth Capsules are small, versioned **YAML** objects that encode **rules, methods, assumptions, and pedagogy** (Socratic prompts + aphorisms). A composer (CLI/SPA) builds **deterministic system prompts** and **manifests** from curated bundles and profiles. CI workflows lint, compose, export KGs, and optionally judge outputs.

**Status:** v0.1.0 - PoC Feedback

---

## Key features

* ✅ **23 Capsules (+1 signed example)** - PR review, red-teaming, safety, reasoning, business rules
* ✅ **Deterministic composition** - Reproducible prompts with manifest lockfiles
* ✅ **Profile system** - 7 contexts (conversational, CI, code assistant, pedagogical, etc.)
* ✅ **Bundle curation** - Pre-composed capsule sets for common workflows
* ✅ **Executable witnesses** - Automated validation code for compliance and CI gates
* ✅ **Provenance & signing** - Ed25519 signatures for trust and audit trails
* ✅ **Pedagogy-first** - Socratic prompts + aphorisms teach models *and* humans
* ✅ **CLI tools** - Linter, composer, witness runner, signing/verify, **KG export**
* ✅ **CI integration** - GitHub Actions for lint, compose, **KG smoke**, LLM-as-judge
* ✅ **Web viewer (snapshot)** - Interactive SPA for visual exploration
* ✅ **Knowledge-graph ready** - **RDF/Turtle**, **NDJSON-LD**, **JSON-LD context**, **Ontology (RDFS)**, **SHACL shapes**, **SPARQL queries**, **Neo4j loader**

---

## Quick start

**Prereqs (one-time):**

```bash
pip install -r requirements.txt
# Optional but recommended for command-line model runs:
# pipx install llm   # https://llm.datasette.io
```

### 1) Lint capsules

```bash
python scripts/capsule_linter.py capsules
# Output: Capsules: 23  errors: 0  warnings: 0
```

### 2) Discover profiles & bundles

```bash
python scripts/compose_capsules_cli.py --root . --list-profiles
python scripts/compose_capsules_cli.py --root . --list-bundles
```

### 3) Compose a system prompt

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out prompt.txt \
  --manifest prompt.manifest.json
```

### 4) Use with your LLM

**OpenAI (Python):**

```python
from openai import OpenAI
client = OpenAI()  # uses OPENAI_API_KEY

with open("prompt.txt") as f:
    system_prompt = f.read()

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Your query here"}
    ]
)
print(resp.choices[0].message.content)
```

**Anthropic (Python):**

```python
import anthropic
client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY

with open("prompt.txt") as f:
    system_prompt = f.read()

resp = client.messages.create(
    model="claude-3-5-sonnet-latest",
    system=system_prompt,
    messages=[{"role": "user", "content": "Your query here"}]
)
print(resp.content[0].text)
```

See **[QUICKSTART.md](docs/QUICKSTART.md)** for a full tutorial.

---

## Knowledge-graph readiness (RDF + Property graphs)

Truth Capsules ship with **first-class graph tooling**:

**Included resources**

* `contexts/truthcapsule.context.jsonld` - JSON-LD context
* `ontology/truthcapsule.ttl` - RDFS vocabulary for capsules, witnesses, pedagogy, provenance
* `shacl/truthcapsule.shacl.ttl` - SHACL constraints for validation
* `queries/*.sparql` - Starter SPARQL queries
* `scripts/export_kg.py` - Export RDF/Turtle + NDJSON-LD
* `scripts/load_neo4j.cypher` - Minimal Neo4j loader

**Export RDF + NDJSON-LD**

```bash
python scripts/export_kg.py
# Outputs in artifacts/out/:
#   capsules.ttl      (RDF/Turtle for triple stores)
#   capsules.ndjson   (NDJSON-LD for property graphs like Neo4j/Memgraph)
```

**Validate RDF with SHACL**

```bash
pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
```

**Run SPARQL queries (example)**

* Load `artifacts/out/capsules.ttl` into your triple store (Jena/Fuseki, GraphDB, Stardog, etc.)
* Use the provided queries (e.g. `queries/list_capsules.sparql`, `queries/capsules_by_domain.sparql`, `queries/capsules_with_python_witness.sparql`)

**Load into Neo4j (property graph)**

```bash
# Start Neo4j locally, then run:
cypher-shell -u neo4j -p password -f scripts/load_neo4j.cypher
# load_neo4j.cypher expects artifacts/out/capsules.ndjson
```

**Artifacts directory**

```
artifacts/
└── out/
    ├── capsules.ttl      # RDF graph (semantic web)
    └── capsules.ndjson   # Property-graph import (Neo4j/Memgraph)
```

See **[docs/KG_README.md](docs/KG_README.md)** for end-to-end examples.

---

## Documentation

### Getting started

* **[Quickstart](docs/QUICKSTART.md)** - 5-minute setup with examples
* **[One-Pager](docs/ONE_PAGER.md)** - Elevator pitch & use cases
* **[Profiles Reference](docs/PROFILES_REFERENCE.md)** - All 7 profiles & aliases

### Schema & design

* **[Capsule Schema v1](docs/CAPSULE_SCHEMA_v1.md)** - YAML structure & fields
* **[Witnesses Guide](docs/WITNESSES_GUIDE.md)** - Executable validation & security
* **[Provenance & Signing](docs/PROVENANCE_SIGNING.md)** - Cryptographic trust model
* **[Security & CSP](docs/SECURITY_CSP.md)** and **[SECURITY.md](docs/SECURITY.md)** - Witness isolation & threat model

### CI & automation

* **[CI Guide](docs/CI_GUIDE.md)** - GitHub Actions workflows
* **[Linter Guide](docs/LINTER_GUIDE.md)** - Validation & strict mode
* **[CI Examples](examples/ci/README.md)** - Sample workflows & artifacts

### Knowledge graphs

* **[KG README](docs/KG_README.md)** - RDF/NDJSON-LD export, SHACL, SPARQL, Neo4j
* **[Capsule Graph Annotations Guide](docs/CAPSULE_GRAPH_ANNOTATIONS_GUIDE.md)** - Optional embedded graph labels/edges (future)

---

## Project structure

```
truth-capsules-v1/
├── artifacts/
│   ├── examples/                # Input fixtures for demos/CI
│   └── out/                     # Generated outputs (KG, logs, etc.)
│       ├── capsules.ttl         # RDF/Turtle export
│       ├── capsules.ndjson      # NDJSON-LD (property graph)
│       ├── answers.json         # Example LLM judge logs (optional)
│       └── ...
├── bundles/                     # Pre-composed capsule sets
├── capsules/                    # YAML capsules (23 + 1 signed example)
├── contexts/
│   └── truthcapsule.context.jsonld
├── docs/                        # Full documentation set
├── examples/
│   └── ci/                      # CI usage examples
├── .github/workflows/           # CI workflows (incl. kg-smoke)
├── keys/                        # (No private keys committed; README only)
├── ontology/
│   └── truthcapsule.ttl         # RDFS vocabulary
├── profiles/                    # 7 context profiles
├── prompts/                     # System prompt fragments
├── queries/                     # SPARQL queries
│   ├── list_capsules.sparql
│   ├── capsules_by_domain.sparql
│   └── capsules_with_python_witness.sparql
├── schemas/                     # JSON Schemas (CI/judge/report)
├── scripts/                     # CLI/utility scripts
│   ├── capsule_linter.py
│   ├── compose_capsules_cli.py
│   ├── run_witnesses.py
│   ├── capsule_sign.py
│   ├── capsule_verify.py
│   ├── export_kg.py
│   ├── load_neo4j.cypher
│   ├── smoke_llm.py
│   └── spa/
│       ├── generate_spa.py
│       ├── README.md
│       └── template.html
├── shacl/
│   └── truthcapsule.shacl.ttl   # SHACL validation shapes
├── tests/
│   └── test_capsules_validate.py
├── .editorconfig  .gitattributes  .gitignore  CHANGELOG.md  LICENSE
├── Makefile  CONTRIBUTING.md  CODE_OF_CONDUCT.md  README.md
└── requirements.txt  QUICKSTART.md
```

---

## Tools

### Core CLI (production-ready)

**`scripts/capsule_linter.py`** - Validate capsule schema & provenance

```bash
python scripts/capsule_linter.py capsules [--strict] [--json]
```

**`scripts/compose_capsules_cli.py`** - Compose system prompts from capsules

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle pr_review_minibundle_v1 \
  --out prompt.txt \
  --manifest manifest.json
```

**`scripts/run_witnesses.py`** - Execute witness validation code

```bash
python scripts/run_witnesses.py capsules

python scripts/run_witnesses.py capsules --json
```

**Signing**

```bash
python scripts/capsule_sign.py   capsules --key $SIGNING_KEY
python scripts/capsule_verify.py capsules --pubkey $PUBLIC_KEY
```

### Knowledge graph tooling

**`scripts/export_kg.py`** - Export to RDF/Turtle + NDJSON-LD

```bash
python scripts/export_kg.py
# artifacts/out/capsules.ttl
# artifacts/out/capsules.ndjson
```

**`shacl/truthcapsule.shacl.ttl`** - Validate RDF graph

```bash
pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
```

**`queries/*.sparql`** - Ready-to-run SPARQL examples

**`scripts/load_neo4j.cypher`** - Minimal Neo4j loader for `capsules.ndjson`

### Snapshot SPA

```bash
python scripts/spa/generate_spa.py --root . --output capsule_composer.html
```

See **[`scripts/spa/README.md`](scripts/spa/README.md)**.

---

## Available capsules (23 + 1 signed example)

### LLM behavior & reasoning (11)

* `llm.citation_required_v1` - Cite sources or abstain
* `llm.plan_verify_answer_v1` - Plan → Verify → Answer workflow
* `llm.red_team_assessment_v1` - Adversarial evaluation protocol
* `llm.counterfactual_probe_v1` - Generate alternative scenarios
* `llm.steelmanning_v1` - Strengthen opposing arguments
* `llm.five_whys_root_cause_v1` - Root cause analysis
* `llm.fermi_estimation_v1` - Order-of-magnitude estimates
* `llm.assumption_to_test_v1` - Convert assumptions to tests
* `llm.evidence_gap_triage_v1` - Identify missing evidence
* `llm.bias_checklist_v1` - Check for cognitive biases
* `llm.plan_backtest_v1` - Test plans against past cases

### PR review & code (5)

* `llm.pr_diff_first_v1` - Always read diff first
* `llm.pr_risk_tags_v1` - Tag risky changes (auth, I/O, etc.)
* `llm.pr_test_hints_v1` - Suggest test cases
* `llm.pr_deploy_checklist_v1` - Deployment safety checks
* `llm.pr_change_impact_v1` - User-facing impact assessment

### Safety & compliance (3)

* `llm.pii_redaction_guard_v1` - Redact PII in outputs
* `llm.safety_refusal_guard_v1` - Safety refusal patterns
* `llm.tool_json_contract_v1` - Enforce JSON schemas for tool calls

### Business & ops (3)

* `business.decision_log_v1` - Decision record requirements
* `ops.rollback_plan_v1` - Deployment rollback plans
* `llm.judge_answer_quality_v1` - LLM-as-judge scoring

### Meta (1)

* `pedagogy.problem_solving_v1` - General problem-solving guidance

**Signed example:** `llm.citation_required_v1_signed.yaml`

---

## Bundles (6)

* **`conversation_red_team_baseline_v1`** - 10 capsules for reasoning + safety
* **`pr_review_minibundle_v1`** - 5 capsules for code review
* **`assistant_baseline_v1`** - 4 capsules for code assistants
* **`ci_llm_baseline_v1`** - 5 capsules for LLM-judge CI gates
* **`ci_nonllm_baseline_v1`** - 2 capsules for deterministic CI checks
* **`conversation_pedagogy_v1`** - 1 capsule for pedagogy

---

## Profiles (7)

* **`conversational`** (`profile.conversational_guidance_v1`) - Natural-language Q&A
* **`pedagogical`** (`profile.pedagogical_v1`) - Socratic teaching
* **`code_patch`** (`profile.code_patch_v1`) - PR review with diffs
* **`tool_runner`** (`profile.tool_runner_v1`) - Function calling with JSON
* **`ci_det`** (`profile.ci_deterministic_gate_v1`) - Non-LLM CI checks
* **`ci_llm`** (`profile.ci_llm_judge_v1`) - LLM-as-judge scoring
* **`rules_gen`** (`profile.rules_generator_v1`) - Capsule authoring meta-profile

See **[PROFILES_REFERENCE.md](docs/PROFILES_REFERENCE.md)**.

---

## CI workflows

Located in `.github/workflows/`:

1. `capsules-lint.yml` - Lint on every push/PR
2. `capsules-compose.yml` - Generate artifacts for bundles
3. `capsules-llm-judge.yml` - LLM-as-judge evaluation (optional)
4. `capsules-policy.yml` - Gate on `review.status=approved`
5. `kg-smoke.yml` - **Export KG and validate with SHACL**

See **[CI_GUIDE.md](docs/CI_GUIDE.md)**.

---

## Development

### Add a new capsule

1. Create `capsules/domain.name_v1.yaml`
2. Required fields: `id`, `version`, `domain`, `statement`
3. Optional: pedagogy (Socratic + Aphorisms) and witnesses
4. Run linter: `python scripts/capsule_linter.py capsules`
5. Add to a bundle or use individually

See **[CAPSULE_SCHEMA_v1.md](docs/CAPSULE_SCHEMA_v1.md)**.

### Create a bundle

1. Create `bundles/my_bundle_v1.yaml`
2. List capsule IDs under `capsules:`
3. Set `applies_to:` contexts
4. Test: `python scripts/compose_capsules_cli.py --bundle my_bundle_v1 ...`

### Create a profile

1. Create `profiles/my_profile.yaml`
2. Set `kind: profile`, add `id`, `title`, `version`
3. Define `response:` format/policy
4. Test: `python scripts/compose_capsules_cli.py --profile my_profile ...`

---

## License

MIT - see **[LICENSE](LICENSE)**.
Use in commercial products, modify freely, attribution welcomed.

---

## Status & roadmap

**v0.1.0 POC (current)**

* ✅ 24 capsules (+1 signed example)
* ✅ CLI tools (lint, compose, sign/verify, **KG export**)
* ✅ GitHub Actions workflows (incl. **KG smoke**)
* ✅ Snapshot SPA viewer
* ✅ Comprehensive documentation
* ✅ Profile alias system
* ✅ UTF-8 normalization
* ✅ Strict mode linting

**Post-v1 (feedback-driven)**

* [ ] Signature verification in CI (P1-03)
* [ ] PR comment bot integration (P1-10)
* [ ] SPA provenance panel (P1-11)
* [ ] Live SPA dev server
* [ ] Secrets-handling capsules (P1-07)
* [ ] Capsule search & tagging (P1-13)
* [ ] VS Code extension
* [ ] Community capsule gallery

---

## Contact & support

* **Issues** - GitHub Issues
* **Discussions** - GitHub Discussions
* **Sponsorship** - See provenance headers / repo contact

For professional services (org-specific capsule curation, CI/KG integration, training), contact via repository details.

---

*Version:* **0.1.0-rc**
*Last updated:* **2025-11-07**
*Capsules:* **24 (+1 signed example)**

---

## Acknowledgments

Built on prompt-engineering practice, formal verification ideas, and Socratic pedagogy.

**Key influences**

* Pragmatic Prompt & Context Engineering
* Package management patterns (npm, pip, cargo)
* Provenance/SBOM models
* Socratic method & aphoristic teaching