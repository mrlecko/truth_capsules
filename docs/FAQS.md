# Truth Capsules - Frequently Asked Questions

**Docs quick links:**
[Capsule Schema v1](./schemas/CAPSULE_SCHEMA_v1.md) · [KG One-Pager](./KG_ONE_PAGER.md) · [Capsule Graph Annotations Guide](./graph/CAPSULE_GRAPH_ANNOTATIONS_GUIDE.md) · [Provenance & Signing](./PROVENANCE_SIGNING.md) · [Linter Guide](./misc/LINTER_GUIDE.md) · [CI Guide](./CI_GUIDE.md) · [Profiles Reference](./misc/PROFILES_REFERENCE.md)

---

## Table of Contents

1. [What is this?](#what-is-this)
2. [What problems does this solve?](#what-problems-does-this-solve)
3. [Why is this new / different?](#why-is-this-new--different)
4. [How do I create a capsule?](#how-do-i-create-a-capsule)
5. [How do I use / consume a capsule?](#how-do-i-use--consume-a-capsule)
6. [What functional contexts can capsules be used in?](#what-functional-contexts-can-capsules-be-used-in)
7. [What is a bundle?](#what-is-a-bundle)
8. [Aphorisms & Socratic prompts (why they matter for LLMs)](#aphorisms--socratic-prompts-why-they-matter-for-llms)
9. [What is a witness?](#what-is-a-witness)
10. [Executable truth & LLMs](#executable-truth--llms)
11. [Extending models with non-corpus knowledge](#extending-models-with-non-corpus-knowledge)
12. [Comparison to RAG / Graph-RAG / MCP / prompt libraries](#comparison-to-rag--graph-rag--mcp--prompt-libraries)
13. [How does signing work?](#how-does-signing-work)
14. [How does provenance work?](#how-does-provenance-work)
15. [How are capsules managed?](#how-are-capsules-managed)
16. [How does CI integration occur?](#how-does-ci-integration-occur)
17. [How do I execute witnesses?](#how-do-i-execute-witnesses)
18. [How do I use capsules in a knowledge graph?](#how-do-i-use-capsules-in-a-knowledge-graph)
19. [Why YAML over a database/graph-native store?](#why-yaml-over-a-databasegraph-native-store)
20. [How does this aid developers?](#how-does-this-aid-developers)
21. [How does this aid teams?](#how-does-this-aid-teams)
22. [How does this aid executives and decision-makers?](#how-does-this-aid-executives-and-decision-makers)
23. [Why are “thinking patterns” the new IP edge?](#why-are-thinking-patterns-the-new-ip-edge)
24. [Schema at a glance](#schema-at-a-glance)
25. [What is a Profile?](#what-is-a-profile)
26. [Composing bundles](#composing-bundles)
27. [Do witnesses expose code?](#do-witnesses-expose-code)
28. [Can I embed graph annotations in YAML later?](#can-i-embed-graph-annotations-in-yaml-later)
29. [Security guidance for witnesses](#security-guidance-for-witnesses)
30. [Roadmap](#roadmap)

---

## What is this?

**Truth Capsules** are small, signed **YAML** artifacts that bundle:

* a **normative statement** (“what must be true”),
* explicit **assumptions**,
* **pedagogy** (Socratic questions + aphorisms), and
* optional **witnesses** (executable checks).

They’re portable “policy + pedagogy + proof” units you can lint, sign, run, compose, and export to knowledge graphs.
See: [Capsule Schema v1](./CAPSULE_SCHEMA_v1.md)

---

## What problems does this solve?

* **Hallucinations & drift:** executable gates anchor outcomes in checks, not vibes.
* **Opaque prompts:** policies become diffable, signable, auditable artifacts.
* **Team alignment:** the *questions to ask* (Socratic) and *principles to apply* (aphorisms) ship with the gate.
* **Re-use across contexts:** the same capsule powers assistants, CI, PR review, and pedagogy.
* **Interoperability:** author in YAML; export to **RDF/SHACL** and **Cypher**.
  See: [KG One-Pager](./KG_ONE_PAGER.md)

---

## Why is this new / different?

* **Executable truth travels with policy** (witnesses), not as a separate doc.
* **Pedagogy + enforcement**: Socratic prompts and aphorisms *shape* reasoning; witnesses *prove* it.
* **Cryptographic provenance**: deterministic digests, Ed25519 signatures.
* **Graph-ready by design**: one-command export to RDF/NDJSON-LD; SHACL validation; Cypher demo.
  See: [Provenance & Signing](./PROVENANCE_SIGNING.md)

---

## How do I create a capsule?

1. Scaffold from the schema and examples in `capsules/` and [Capsule Schema v1](./CAPSULE_SCHEMA_v1.md).
2. Add minimal fields: `id, version, domain, title, statement, assumptions[], provenance`.
3. Add optional pedagogy (`Socratic`, `Aphorism`) and witnesses (`code` or `code_ref`).
4. Lint/validate: `python scripts/capsule_linter.py`
5. (Optional) Sign: `python scripts/capsule_sign.py` → verify: `python scripts/capsule_verify.py`
   See: [Linter Guide](./LINTER_GUIDE.md)

---

## How do I use / consume a capsule?

* **Assistants**: load bundles; present Socratic prompts/aphorisms; enforce witnesses as gates.
* **CI / PR review**: run witnesses as preflight checks; fail builds on invariant breaks.
* **Pedagogy / onboarding**: guide reasoning with curated prompts.
* **Knowledge Graphs**: export Turtle/NDJSON-LD; validate with SHACL; run SPARQL/Cypher.
  See: [CI Guide](./CI_GUIDE.md), [KG One-Pager](./KG_ONE_PAGER.md)

---

## What functional contexts can capsules be used in?

* Conversational assistants, code assistants, CI pipelines, PR review, incident/postmortems, pedagogy/training, red-team drills, policy enforcement, knowledge-graph curation.
  See: `profiles/` and [Profiles](./PROFILES.md)

---

## What is a bundle?

A named set of capsule IDs plus environment settings for a scenario. Example: `assistant_baseline_v1` activates citation, tool-contract, and PII guards together.
See: `bundles/*.yaml`

---

## Aphorisms & Socratic prompts (why they matter for LLMs)

**Aphorisms** are compact, high-leverage principles (e.g., *“One failing test beats ten opinions.”*). They are token-light and **steer** models toward robust behavior.
**Socratic questions** are targeted prompts that force **decomposition** and **evidence surfacing** (e.g., *“What changed?”*, *“What assumption would most break this plan?”*).

### The PSA² Loop: Pedagogy + Structure + Assumptions + Assertions

Capsules combine:

* **Pedagogy** (Socratic + Aphorisms) → *shape* the reasoning trajectory.
* **Structure** (statement, domain, title) → *focus* the task.
* **Assumptions** → *declare* preconditions and scope.
* **Assertions** (witnesses) → *prove* outcomes with code.

This loop yields:

* **Higher first-pass quality** (the model is guided to ask/answer the right things).
* **Lower variance** (smaller prompt jitter, more consistent outcomes).
* **Auditability** (you can see which questions were asked and which gates passed).

Practical tip: keep **≤5** Socratic prompts and **≤5** aphorisms per capsule (see style guidance in [Capsule Schema v1](./CAPSULE_SCHEMA_v1.md)).

---

## What is a witness?

A small executable that asserts invariants (e.g., *“response includes ≥1 assumption and ≥1 evidence item ≥10 chars”*). Languages: Python/Node/Bash are common. Use **block literals** (`|-`) for code in YAML, and run in a **sandbox**.
See: [Linter Guide](./LINTER_GUIDE.md)

---

## Executable truth & LLMs

Witnesses provide a **trustable ground state**:

* Deterministic acceptance criteria.
* Repeatable checks in CI-like systems for reasoning tasks.
* Evidence logs: what passed/failed, when, under which inputs.

This converts “prompt hopes” into **proof-carrying** results.

---

## Extending models with non-corpus knowledge

Capsules sit **beside** the model (no fine-tuning required). They encode:

* **What must be asked** (Socratic),
* **How to think** (aphorisms),
* **What must hold** (witnesses).

They thereby “extend” the model’s effective behavior with **portable, signed** thinking patterns and gates.

---

## Comparison to RAG / Graph-RAG / MCP / prompt libraries

* **Prompt libraries**: text-only; capsules add structure, signatures, and executable gates.
* **RAG / Graph-RAG**: fetches *facts*; capsules define *must-be-true* **outcomes**.
* **MCP / tool use**: executes tools; capsules bind tools to **policies + proofs**.
  **Best practice:** use RAG for retrieval, MCP for actions, **capsules for guarantees**.

---

## How does signing work?

* A deterministic **core-content digest** (sha256) covers:
  `id, version, domain, title, statement, assumptions, pedagogy(kind,text)`
* `scripts/capsule_sign.py` signs the digest (Ed25519); `scripts/capsule_verify.py` verifies with the pubkey.
  See: [Provenance & Signing](./PROVENANCE_SIGNING.md)

---

## How does provenance work?

Each capsule includes `provenance` (author, org, license, created/updated, review status, signing metadata). This supports clear **ownership, lifecycle, and audit**.
See: [Provenance & Signing](./PROVENANCE_SIGNING.md)

---

## How are capsules managed?

* **Source of truth:** YAML in Git (reviewable, diffable, signable).
* **Quality:** schema validation, linters, witness smoke tests.
* **Lifecycle:** `provenance.review.status` → draft / in_review / approved / deprecated.
* **Distribution:** releases or submodules; artifacts in `artifacts/`.
  See: [Linter Guide](./LINTER_GUIDE.md), [CI Guide](./CI_GUIDE.md)

---

## How does CI integration occur?

GitHub Actions under `.github/workflows/`:

* Lint capsules and schemas.
* Enforce policy/gates on PRs.
* Compose bundles and emit artifacts.
  Add the **KG smoke** job to export Turtle + SHACL validate.
  See: [CI Guide](./CI_GUIDE.md)

---

## How do I execute witnesses?

* CLI example:

  ```bash
  python scripts/run_capsules.py --capsule capsules/<capsule_id>.yaml
  ```
* Provide environment vars needed by the witness.
* Run in a **sandbox**: no network, read-only FS, strict time/memory limits.
  See: [Linter Guide](./LINTER_GUIDE.md)

---

## How do I use capsules in a knowledge graph?

```bash
# Export RDF (Turtle) + NDJSON-LD
python scripts/export_kg.py

# Validate RDF with SHACL
pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
```

* Query with SPARQL (see `queries/`).
* Neo4j/Memgraph: `:RUN scripts/load_neo4j.cypher`.
  See: [KG One-Pager](./KG_ONE_PAGER.md)

---

## Why YAML over a database/graph-native store?

* **Versioning & review**: first-class diffs, PRs, and signatures.
* **Portability**: any stack can read YAML; export to graphs when needed.
* **Stability**: schema tweaks don’t require DB migrations for authors.

---

## How does this aid developers?

* Clear, **testable** acceptance criteria for AI behavior.
* Reusable bundles per repo/team; predictable CI gates.
* Minimal friction (YAML + small scripts); no model changes required.

---

## How does this aid teams?

* Shared **thinking kits** (Socratic + aphorisms) aligned with **enforced** invariants.
* Faster PR review and incident analysis.
* Signed provenance → accountability without ceremony.

---

## How does this aid executives and decision-makers?

* Transparent approval criteria (**what must be true** to ship/respond).
* Auditability (who signed what, when; which gates failed).
* Graph views of coverage, dependencies, and risk hotspots.

---

## Why are “thinking patterns” the new IP edge?

Models are commoditizing; **process isn’t**. Capsules package **how** you think-questions asked, principles applied, invariants enforced-as **portable, signed IP**. They scale across stacks and teams and are defensible because they’re **executable and auditable**.

---

## Schema at a glance

* **Required:** `id, version, domain, title, statement, assumptions[], provenance`
* **Optional:** `pedagogy[]` (Socratic/Aphorism), `witnesses[]`, `applies_to[]`, `dependencies[]`, `incompatible_with[]`, `security`
  See: [Capsule Schema v1](./CAPSULE_SCHEMA_v1.md)

---

## What is a Profile?

A runtime configuration describing **how** capsules run in a given context (assistant, CI, code patching, pedagogy).
See: [Profiles](./PROFILES.md) · [Profiles Reference](./PROFILES_REFERENCE.md)

---

## Composing bundles

List capsule IDs in `bundles/*.yaml`, plus any `env` variables for witnesses. Use `scripts/compose_capsules_cli.py` if present.

---

## Do witnesses expose code?

No. The KG exporter emits **hashes** (`codeHash`) or **references** (`codeRef`)-never raw code. Inline code stays in YAML; executions should occur in a sandbox.

---

## Can I embed graph annotations in YAML later?

Yes-optionally, via a `kg:` block that exporters can merge into RDF/Cypher. It’s **ignored today** (RC is one-way: YAML → graph).
See: [Capsule Graph Annotations Guide](./CAPSULE_GRAPH_ANNOTATIONS_GUIDE.md)

---

## Security guidance for witnesses

* Treat witness code as **untrusted**.
* Sandbox: **no network**, read-only FS, CPU/memory/time caps, low-privilege user.
* Explicit env allowlist; deterministic seeds & locales.
  See: [Linter Guide](./LINTER_GUIDE.md)

---

## Roadmap

* PROV-O **run records** (inputs, verdicts, timestamps)
* Richer **SHACL** shapes
* Optional **`kg:`** annotations + named graphs
* Packaged loaders for popular graph stacks
  See: [KG One-Pager](./KNOWLEDGE_GRAPH_READY.md) · [Capsule Graph Annotations Guide](./CAPSULE_GRAPH_ANNOTATIONS_GUIDE.md)

---

**Have more questions?** Open an issue or check the examples in `artifacts/examples/` and the scripts under `scripts/`.
