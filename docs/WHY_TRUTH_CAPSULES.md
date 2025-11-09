# What makes a Truth Capsule different (core shape)

* **Atomic, portable envelope.** A capsule is one small directory/YAML that bundles: a statement (what you assert), **witnesses** (how you check), example inputs/profiles, and **receipts** (digests/signatures/run logs). It’s meant to travel between a dev’s laptop, CI, and an auditor, unchanged.
* **Polyglot by default.** Each witness can be shell, Python, OPA, Great Expectations, LLM eval, anything. Capsules don’t ask you to re-platform your checks.
* **Receipts built-in.** Running a capsule emits verifiable NDJSON receipts, with optional signing. You can prove *what was checked, with what inputs, and what happened*.
* **Hermetic option (sandbox).** The `witness-sandbox` path executes witnesses in a locked-down container (ro mount, no net, tmpfs /tmp, low pids/mem, no new privs). That gives you reproducibility and tames untrusted checks.

# How capsules complement the “nearby” tools

## 1) LLM eval frameworks (Frontier Evals / LangSmith evals / ragas)

* **Overlap:** Evaluate prompts, RAG answers, guardrails.
* **Capsule role:** The capsule is the *envelope* that runs your eval harness and then emits signed **receipts**. You keep using your favorite eval tools; the capsule standardizes the *evidence*.
* **Why lower barrier:** No new SaaS account or DSL required. Stick a tiny Python witness around your eval, run `make run-witness` (or sandboxed), and ship the NDJSON receipt with the model/report.

## 2) Policy-as-Code (OPA/Gatekeeper, Kyverno)

* **Overlap:** Declarative rules; pass/fail gating.
* **Capsule role:** Produce evidence before/alongside enforcement. Example: a PR job runs a capsule that checks Go linters + license policy + LLM-PR-risk witness; OPA then **admits** only if a valid receipt is attached to the artifact.
* **Interlock:** Keep OPA as the enforcer; use a capsule as the **evidence generator**. OPA rego can simply require a fresh, signed capsule receipt (digest + policy tag) rather than re-implement every check in Rego.

## 3) Supply chain & provenance (SBOM/SPDX, SLSA, in-toto, Sigstore)

* **Overlap:** Digests, attestations, signatures.
* **Capsule role:** Add **what you asserted & verified** to the supply-chain story. SBOM proves *what* you built; SLSA/in-toto proves *how*; a capsule proves *which claims you checked* and the **outputs**.
* **Interlock:** Attach capsule digests/receipts as in-toto evidence or reference them from SPDX (ExternalRefs). Use cosign (or similar) to sign the capsule’s NDJSON receipts.

## 4) Data quality (Great Expectations / data contracts)

* **Overlap:** Expectation suites, dataset checks.
* **Capsule role:** Wrap your GE suite as a witness (CLI/python). The capsule captures inputs, run parameters, result JSON, and signature.
* **Why lower barrier:** You don’t have to “adopt GE” org-wide to start; one data engineer can pilot a capsule in an afternoon and still hand an auditor a signed receipt.

## 5) Compliance models (OSCAL / NIST controls)

* **Overlap:** Machine-readable control catalogs and assessment results.
* **Capsule role:** Be the **executable assessment procedure** that produces artifacts you can reference from OSCAL. Capsules aren’t a compliance model; they’re the little robots that run and return proof.

## 6) Knowledge graphs / semantics (RDF/SHACL)

* **Overlap:** Shapes and constraints.
* **Capsule role:** Two directions: (a) run SHACL as a witness, (b) export capsule metadata/receipts as RDF so your KG shows **who claimed what, using which check, when, and with what outcome**.
* **Why lower barrier:** You can reach semantic/audit worlds later—today, it’s just a YAML + a script.

## 7) CI/CD & build tools (GitHub Actions, GitLab CI, Jenkins)

* **Overlap:** Orchestration.
* **Capsule role:** A **single step** that runs checks and drops receipts into `artifacts/`. No infra migration; no lock-in. Because capsules are small and local, your CI runner can execute them hermetically.

---

# Design contrasts that matter in practice

| Axis           | Truth Capsule                          | Evals/QA frameworks      | Policy engines       | Compliance schemas             | Supply-chain attestations |
| -------------- | -------------------------------------- | ------------------------ | -------------------- | ------------------------------ | ------------------------- |
| Unit of record | **Claim + witnesses + receipts**       | Test suite & metrics     | Policies & decisions | Controls & evidence references | Build/process lineage     |
| Execution      | **Anything** (shell, py, OPA, GE, LLM) | Usually Python/SDK-bound | Rego/Kyverno         | Non-executable                 | Non-executable            |
| Output         | **Receipts (NDJSON/JSON) + digests**   | Scores/plots             | allow/deny           | XML/JSON catalogs              | DSSE/attestations         |
| Portability    | **High (one directory)**               | Medium (requires stack)  | High in K8s          | High as metadata               | High as metadata          |
| Adoption cost  | **Very low**                           | Medium (framework)       | Medium (cluster)     | High (program)                 | Medium (program)          |
| Governance fit | **Evidence unit**                      | Evaluation quality       | Enforcement          | Canonical catalog              | Lineage/provenance        |

The punchline: you keep the systems you already like; capsules give you a **thin, portable evidence layer** that’s easy to start and easy to share.

---

# Why the barrier to entry is low

* **Author in minutes.** Copy a template, write a 10–20-line YAML + a tiny witness script. You don’t need to restructure repos or stand up servers.
* **Run anywhere.** `make run-witness` for speed; `make witness-sandbox` for hermetic runs (ro filesystem, zero net, constrained resources).
* **Receipts out of the box.** Every run emits NDJSON you can check into CI artifacts. Add signatures when/if you want.
* **No lock-in.** YAML + POSIX + Python; if you walk away, your checks and receipts still work.
* **Composable.** One pipeline can call many capsules. One capsule can call many tools.
* **Human-friendly UX.** The SPA profile/prompt composer ships with the repo. Non-engineers can read capsules, run them, and see results.

---

# “Why not just…” answers (skeptical engineer edition)

* **“…write unit tests?”** Do it! Capsules are for **cross-cutting** checks you want to **share** as portable evidence (policy, eval, data, security) with a standard receipt. Unit tests rarely travel or come signed.
* **“…adopt a big eval framework?”** Also fine. Capsules *wrap* it so results are portable/signed and live with the claim—not just in a vendor UI.
* **“…lean on OPA only?”** OPA decides; it doesn’t run polyglot checks and stamp receipts. Use both: capsule produces evidence; OPA enforces presence/freshness.
* **“…ship an SBOM and call it a day?”** SBOM ≠ verified claims. SBOM says *what’s inside.* A capsule tells what you **asserted and verified** about behavior, data quality, risk, etc.

---

# Integration “bridge” patterns you can demo today

1. **Pre-merge guard:**

   * CI runs a capsule (`llm.pr_risk_tags_v1`) → emits receipt → stores in job artifacts.
   * OPA/GitHub status check requires a fresh receipt digest referencing that PR SHA.

2. **Data pipeline SLA:**

   * Capsule wraps a Great Expectations suite for `table_X` → **RED** fails the deploy; **GREEN** attaches the JSON receipt to the release notes.

3. **Model card with proof:**

   * Capsule runs your eval harness and a bias/coverage witness → publish the receipts alongside the model card.

4. **Compliance crosswalk:**

   * Map capsule IDs to OSCAL controls in docs; link receipts in your SSP as “objective evidence”.

---

# Where capsules *don’t* try to compete (on purpose)

* Not a replacement for OPA/Kyverno admission control.
* Not a build system or pipeline orchestrator.
* Not a full compliance framework.
* Not a long-term evidence store (use your artifact repo/KG for that).

They’re a **thin, universal adaptor**: run checks, capture receipts, move on.

---

# Risks & mitigations (brief)

* **Ad-hoc sprawl** if teams mint too many capsules → Mitigate with a naming convention, tags, and a `list-bundles`/catalog page.
* **Weak witnesses** (e.g., vague LLM checks) → Provide *blessed witness templates* with thresholds, fixtures, and negative tests.
* **Sandbox friction** (file perms, RO mounts) → You already added `--tmpfs /tmp` and user remap; document “how to pass inputs” and “when to relax flags.”
* **Receipt trust gap** → Show optional signing; publish a one-pager on how to verify signatures/digests locally.

---

# Bottom line

**Truth Capsules** are the missing *evidence unit*: small enough to author in minutes, strong enough to carry **multi-tool checks + receipts** across org boundaries, and neutral enough to **plug into** eval frameworks, policy engines, SBOM/SLSA, and compliance models without asking anyone to switch stacks.