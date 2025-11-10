# Objections & Pushbacks (v1 RC)

**Purpose.** Anticipate tough questions, steelman them, and respond crisply. This is **not** spin; it’s an operating plan for honest engagement on HN, GitHub Issues, and customer calls.

## TL;DR stance

* This repo is a **polished PoC**: curation-first YAML capsules → deterministic prompts → manifests → optional KG export → CI checks.
* Differentiators: **provenance/signing, executable witnesses, deterministic composition, profiles/projections, KG visibility**.
* We pin versions, show one-shot demos, and ship **WOW queries** to make value legible in minutes.

---

## Top objections (steelman) and our responses

| #  | Objection (verbatim-ish)                    | Why this is reasonable (steelman)                                   | Pushback / Core response                                                                                         | Mitigations & actions (shipped/next)                                                                 | Evidence / where to look                                                                   | Risk |
| -- | ------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ---- |
| 1  | “This is just another prompt library.”      | Most “prompt repos” are text dumps. Skepticism is healthy.          | This is **curation + determinism + provenance + witnesses + KG**. It’s not a zoo; it’s a reproducible system.    | Deterministic composer + manifest lock; signing; witnesses; RDF/Neo4j loaders; control table render. | `compose_capsules_cli.py`, `docs/CAPSULE_SCHEMA_v1.md`, `scripts/neo4j_wow_*.cypher`       | Low  |
| 2  | “Not production-ready.”                     | Fair: it’s a PoC. Prod needs policy engines, RBAC, hosted services. | We **explicitly** position as PoC; but flows are solid and CI-friendly.                                          | Pinned Neo4j path; strict linter; CI workflows; roadmap in README.                                   | README “Status & Roadmap”, `.github/workflows/*`, `docs/CI_GUIDE.md`                       | Low  |
| 3  | “Executable witnesses are a security risk.” | Running code is scary (net/file exfil).                             | Witness exec is **opt-in**; includes timeouts, temp cwd, minimal env. Recommended **no-net** (doc’d).            | Default `--no-exec` in CI; sandbox guidance; sample “safe” witnesses only.                           | `docs/WITNESSES_GUIDE.md`, `scripts/run_witnesses.py`                                      | Med  |
| 4  | “Neo4j/APOC setup is finicky.”              | Plugins/versions bite everyone.                                     | We ship a **pinned**, known-good path and a one-shot loader.                                                     | Neo4j **4.4 + apoc-4.4.0.39** script; import mount fixed; WOW queries included.                      | `scripts/neo4j_44_up.sh`, `scripts/neo4j_load_capsules.cypher`, `scripts/neo4j_wow_all.sh` | Med  |
| 5  | “YAML instead of a DSL?”                    | DSLs can be safer/typed; YAML can be messy.                         | YAML is **audit- and PR-friendly**, signable, easy to diff. DSL can compile-to-YAML later.                       | Strict schema + linter; signed examples; projection controls keep YAML small.                        | `docs/CAPSULE_SCHEMA_v1.md`, `scripts/capsule_linter.py`                                   | Low  |
| 6  | “Does this actually improve answers?”       | Show me lift, not vibes.                                            | We enable **policy gates** and **judge capsules**; demos show failure→pass diffs.                                | Include “before/after” demo and judge scores; ship PVA logs.                                         | `artifacts/examples/*`, `artifacts/out/pva_logs.json`, `docs/DEMOS.md`                     | Med  |
| 7  | “Profiles/projections sound complex.”       | Two layers of indirection can confuse.                              | Projection = **view** of a capsule per profile (e.g., conversational vs CI).                                     | Add **control table** header; side-by-side projection demos.                                         | `docs/PROFILES_REFERENCE.md`, `docs/examples/projections/*`                                | Low  |
| 8  | “Vendor lock-in?”                           | Model churn is real.                                                | Model-agnostic: **system prompt text in / text out**; no SDK dependency.                                         | Provide OpenAI/Anthropic snippets; env-based model selection.                                        | `docs/LLMS_INTEGRATION_GUIDE.md`                                                           | Low  |
| 9  | “Hard to author capsules.”                  | Authoring is a skill; people need guardrails.                       | Templates + linter + examples reduce friction; **rules_gen** profile helps.                                      | Add cookbook; `capsule init` scaffold (roadmap).                                                     | `capsules/*`, `docs/CAPSULES_SCHEMA_v1.md`, `profiles/rules_gen.yaml`                      | Med  |
| 10 | “Prompt injection via capsules?”            | Capsules are just text; can embed directives.                       | **Curated** repo; linter enforces schema; signed capsule example; **do not** treat user text as capsules.        | Strict mode requires `review.status=approved`; signing keys doc.                                     | `docs/PROVENANCE_SIGNING.md`, `.github/workflows/capsules-policy.yml`                      | Low  |
| 11 | “Duplicate of Guardrails/promptfoo/etc.?”   | Overlap exists.                                                     | Complementary: we focus on **curation, provenance, KG, and executable witnesses**—integrates with testing tools. | Adapters on roadmap; export manifests for other tools.                                               | `artifacts/out/*`, `docs/USE_CASES.md`                                                     | Low  |
| 12 | “Maintenance overhead / library rot.”       | Version drift kills trust.                                          | Semver on capsules; manifest lock; CI lint on PR.                                                                | Add `capsules.lock.json` with sha256; changelog policy.                                              | `CHANGELOG.md`, `.github/workflows/capsules-lint.yml`                                      | Med  |
| 13 | “Why a graph?”                              | Many teams don’t need RDF/Neo4j.                                    | Optional, but **makes coverage and dependencies visible** in minutes; great for governance.                      | WOW queries: coverage, clusters, safety cones; pure Turtle path (no APOC).                           | `artifacts/out/capsules.ttl`, `scripts/neo4j_wow_*.cypher`                                 | Low  |
| 14 | “Windows?”                                  | Docker + paths can be rough.                                        | Linux-first; WSL2 recommended; scripts note path caveats.                                                        | Add Windows notes; keep paths relative.                                                              | `docs/KG_README.md`, `scripts/*` comments                                                  | Low  |
| 15 | “Licensing / IP worries.”                   | Companies care.                                                     | MIT; demo signing key; no private keys in repo.                                                                  | Keys README; signed capsule example verifies.                                                        | `LICENSE`, `keys/README.md`, `capsules/*signed*.yaml`                                      | Low  |
| 16 | “Performance cost?”                         | Longer prompts can slow responses.                                  | Composer runs at build time; production can **omit pedagogy** via projection.                                    | `--projection compact`; profile-specific trims.                                                      | `docs/PROFILES_REFERENCE.md`                                                               | Low  |
| 17 | “Where are real-world domains?”             | LLM policy is abstract.                                             | We include **PR review**, **PII**, **safety refusal**, **decision log**.                                         | Add 2–3 domain capsules post-launch (sec, perf, analytics).                                          | `capsules/llm.*`, `capsules/business.*`, `capsules/ops.*`                                  | Med  |
| 18 | “Too much ceremony for small teams.”        | Maybe they just need a single prompt.                               | Start with **minibundle** + one profile; scale later.                                                            | `bundles/pr_review_minibundle_v1.yaml`; quickstart paths.                                            | `docs/QUICKSTART.md`                                                                       | Low  |
| 19 | “Results aren’t measurable.”                | Needs metrics.                                                      | Provide **judge scores** and policy pass/fail deltas in examples.                                                | Include PVA/judge artifacts for demos.                                                               | `artifacts/examples/answers.judgment.json`                                                 | Med  |
| 20 | “Neo4j? Why not SQLite/JSON?”               | Simpler stacks exist.                                               | JSON/NDJSON-LD are primary; KG is **optional** insight layer.                                                    | Keep JSON artifacts; KG as opt-in.                                                                   | `artifacts/out/*.ndjson`                                                                   | Low  |

---

## HN / GitHub comment playbook (copy-paste replies)

* **“Another prompt library?”**

  > This is a *deterministic* prompt composer with provenance, executable witnesses, and optional KG export. The manifest + lock lets you reproduce the exact system prompt that generated an output. The WOW queries show coverage/safety across the capsule set.

* **“Security risk with witnesses.”**

  > Witness exec is off by default in CI and sandboxed locally (timeouts, temp cwd, minimal env; recommended no-net). The idea is auditable, human-readable tests that travel with the policy.

* **“Setup pain (Neo4j/APOC).”**

  > Totally fair. We pinned a known-good path (Neo4j 4.4 + apoc-4.4.0.39) with a one-shot script. If you prefer, skip KG and use the JSON artifacts only—everything else still works.

* **“Show me lift.”**

  > We include judge artifacts and before/after runs for PR-review + PII + safety. You can run the demos locally and check the logs in `/artifacts/out`.

---

## Open risks (we acknowledge)

* **Sandboxing depth** (Med): process caps vary by OS. We provide guidance and defaults; hardened runner is a v1.1 target.
* **Projection complexity** (Low): we added a control table + examples; will keep projections small.
* **Authoring UX** (Med): templates + linter help; a `capsule init` scaffolder is planned.
* **Version drift in KG** (Low): we pin versions and ship a stable loader; long-term we’ll add a Docker compose for graph.

---

## What we’ve tightened (since RC feedback)

* Pinned Neo4j **4.4** + **apoc-4.4.0.39**, with a working loader & WOW queries.
* **Projection & presentation**: profile-aware rendering and a top **control table** to make active rules obvious.
* **Bundle schema**: linter checks; CI rejects unapproved/review-missing capsules in strict mode.
* **Manifests**: composer version + hashes for reproducibility.
* **CHEATSHEET**: “3 commands to WOW” path + profiles/bundles quick reference.

---

## How to escalate evidence in a thread

* Link to **WOW queries** and paste 2–3 result rows.
* Paste the **control table** snippet from a composed prompt.
* Point to **judge outputs** for a demo (capsule causing a pass/fail delta).
* Show **manifest.json** proving determinism.

---

## Appendix A — One-liner references

* **Deterministic compose:**
  `python scripts/compose_capsules_cli.py --root . --profile conversational --bundle conversation_red_team_baseline_v1 --out prompt.txt --manifest prompt.manifest.json`

* **Run linter (strict):**
  `python scripts/capsule_linter.py capsules --strict`

* **Export KG:**
  `python scripts/export_kg.py`

* **Spin Neo4j 4.4 + load:**
  `bash scripts/neo4j_44_up.sh && bash scripts/neo4j_load_capsules.sh && bash scripts/neo4j_wow_all.sh`

---

## Appendix B — Future-proof answers

* **DSL?** We’ll consider a typed layer that compiles to signed YAML; YAML remains the signed source of truth.
* **Guardrails integration?** Manifests can power other tools; adapters welcome.
* **Hosted?** This repo focuses on open PoC; a hosted viewer/CI add-on is on the table if there’s interest.

---