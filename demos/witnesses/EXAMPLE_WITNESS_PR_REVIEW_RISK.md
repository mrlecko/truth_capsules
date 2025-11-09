# Example Witness: **PR Risk-Coverage**

## What it demonstrates

A **deterministic, offline** gate that ties static heuristics in a PR **diff** to **accountability** in the human/LLM **review**:

* If the diff touches any risky surface (`auth`, `net`, `fs`, `secrets`, `pii`),
* the review must **name** each detected tag and include a **Mitigation** note,
* otherwise the witness **FAILs** (non-zero exit).
* If no risks are detected, the witness returns **SKIP** (exit 0).

## Why it’s useful

* **Catches real regressions early** (hardcoded secrets, casual FS writes, network calls in auth paths, PII in logs).
* **Enforces review quality** with a binary rule: *acknowledge risk + state mitigation or fail*.
* **Explainable** (small, readable regexes) and **auditable** (JSON result with inputs & reasons).
* **Portable & vendor-agnostic** — no model calls, no network.

## How it works (logic)

1. Heuristics scan a unified diff for patterns:

   * `secrets`: `AWS_`, `SECRET`, `api[-_]?key`, `password=`, …
   * `auth`: `oauth`, `jwt`, `session`, `login`, `auth`…
   * `net`: URLs, `requests.`, `fetch(`, `socket.`
   * `fs`: `open(`, `os.remove`, `shutil.`
   * `pii`: basic email/phone/SSN-ish tokens
2. Build `present = {tags found in diff}`.

   * If `present == ∅` → **SKIP**.
   * Else, the review must **mention each tag** *and* include the word **“Mitigation”**.
3. Missing coverage → **FAIL**; fully covered → **PASS**.

> The code lives inside capsule `llm.pr_risk_tags_v1` under `witnesses:` and uses stdlib only. The witness emits `status:"SKIP"` when no risks are detected.

## Who would use this pattern

* **Developers / Reviewers** — guardrail that their notes actually cover risks.
* **Platform / SRE / Security** — a zero-friction gate before staging.
* **QA / Compliance** — auditable evidence that risk classes were acknowledged and mitigated.
* **Agent / LLM teams** — hold LLM-drafted reviews to deterministic standards.

## How to deploy / apply

* **Local:** run via `scripts/run_witnesses.py` (or a Make target) before merge.
* **CI:** add a job that runs witnesses; **fail** the build on non-zero.
* **Policy:** place the capsule in team bundles so the rule is always composed for PRs.
* **Org-wide:** standardize heuristics & mitigation phrasing to match policy.

> The runner is configured so **OS environment variables override** capsule `env:` defaults, recognizes witness `status:"SKIP"`, and now supports **filters**: `--capsule`, `--capsule-file`, and `--witness` for focused runs.

## Security considerations

* **No network** and **read-only** inputs under `artifacts/examples/*`.
* Run with **timeouts** and minimal environment; prefer **containerized / restricted** runners (no-net, read-only FS).
* Treat witness code like build scripts — **review it** before enabling in CI.

---

## Step-by-step (shell)

**Prereqs:** venv active and these fixtures present:

* `artifacts/examples/pr_diff.patch` — touches `auth`, `net`, `fs`, `secrets`
* `artifacts/examples/pr_review.md` — **good** review (names each tag + “Mitigation”)
* `artifacts/examples/pr_review_bad.md` — **bad** review (“Looks fine.”)

### 1) Run only this capsule (PASS case)

```bash
python scripts/run_witnesses.py capsules \
  --capsule llm.pr_risk_tags_v1 \
  --json | tee artifacts/out/pva_logs.json
```

**Expect (excerpt):**

```json
{
  "capsule": "llm.pr_risk_tags_v1",
  "status": "GREEN",
  "witness_results": [
    {
      "name": "pr_review_covers_risks",
      "status": "PASS",
      "stdout": "{\n  \"witness\": \"pr_review_covers_risks\",\n  \"found_tags\": [\"auth\",\"fs\",\"net\",\"secrets\"],\n  \"missing\": [],\n  \"status\": \"PASS\",\n  \"inputs\": {\"diff\": \"artifacts/examples/pr_diff.patch\", \"review\": \"artifacts/examples/pr_review.md\"}\n}\n"
    }
  ]
}
```

### 2) FORCE a FAIL (bad review, missing mitigations)

Because **OS env overrides** capsule defaults, point the witness at the bad review:

```bash
REVIEW_PATH=artifacts/examples/pr_review_bad.md \
python scripts/run_witnesses.py capsules \
  --capsule llm.pr_risk_tags_v1 \
  --json | tee artifacts/out/pva_logs.json
```

**Expect (excerpt):**

```json
{
  "name": "pr_review_covers_risks",
  "status": "FAIL",
  "stdout": "{\n  \"found_tags\": [\"auth\",\"fs\",\"net\",\"secrets\"],\n  \"missing\": [\n    {\"tag\":\"auth\",\"reason\":\"tag-not-mentioned\"},\n    {\"tag\":\"fs\",\"reason\":\"tag-not-mentioned\"},\n    {\"tag\":\"net\",\"reason\":\"tag-not-mentioned\"},\n    {\"tag\":\"secrets\",\"reason\":\"tag-not-mentioned\"}\n  ],\n  \"status\": \"FAIL\",\n  \"inputs\": {\"diff\": \"artifacts/examples/pr_diff.patch\", \"review\": \"artifacts/examples/pr_review_bad.md\"}\n}\n"
}
```

### 3) SKIP (no-risk diff)

```bash
printf '%s\n' \
 'diff --git a/README.md b/README.md' \
 '--- a/README.md' '+++ b/README.md' \
 '@@' '+ Minor doc tweak.' > artifacts/examples/pr_diff_norisk.patch

DIFF_PATH=artifacts/examples/pr_diff_norisk.patch \
python scripts/run_witnesses.py capsules \
  --capsule llm.pr_risk_tags_v1 \
  --json | tee artifacts/out/pva_logs.json
```

**Expect (excerpt):**

```json
{
  "name": "pr_review_covers_risks",
  "status": "SKIP",
  "stdout": "{\n  \"witness\": \"pr_review_covers_risks\",\n  \"found_tags\": [],\n  \"status\": \"SKIP\",\n  \"inputs\": {\"diff\": \"artifacts/examples/pr_diff_norisk.patch\", \"review\": \"artifacts/examples/pr_review.md\"}\n}\n"
}
```

If this is the only witness in the capsule, the capsule’s overall status will also be **SKIP**.

### 4) Run by **capsule file** or a single **witness**

**By file/glob:**

```bash
python scripts/run_witnesses.py capsules \
  --capsule-file 'capsules/llm.pr_risk_tags_v1.yaml' \
  --json
```

**Only this witness inside the capsule:**

```bash
python scripts/run_witnesses.py capsules \
  --capsule llm.pr_risk_tags_v1 \
  --witness pr_review_covers_risks \
  --json
```

---

## Troubleshooting

* **“I expected FAIL but got PASS.”** Check `inputs.review` in the witness JSON — it shows the actual file used. With OS-env precedence, `REVIEW_PATH=…` should override the capsule’s `env:`.
* **“No risks in the diff.”** You’ll see `status:"SKIP"`; informational and exits 0.
* **Regex too simple?** By design — start explainable; tune per org or upgrade to AST-based checks later.