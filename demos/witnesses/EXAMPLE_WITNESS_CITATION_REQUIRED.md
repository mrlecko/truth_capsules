# Example Witness #2: **Citation Integrity (Coverage + Provenance Diversity)**

## What it demonstrates

A **deterministic, offline** gate that turns “cite your work” into an **executable rule**:

* **Coverage:** a configurable fraction of declarative sentences must have **[n]** citations.
* **Integrity:** each **[n]** must exist in `references` with a valid URL.
* **Diversity:** references shouldn’t be a single-domain echo chamber (policy-tunable).
* **Context-aware SKIP:** opinion pieces can **SKIP** by policy (no hard fail).

## Why teams use it

* **Research/Editorial:** enforce evidence discipline with reproducible checks.
* **Compliance:** provenance & source diversity without any network calls.
* **LLM Safety:** fail low-evidence answers in CI instead of trusting vibes.

## How it works

The witness (in `llm.citation_required_v1`) reads a JSON file:

```json
{
  "answer": "Claim one [1]. Claim two [2].",
  "references": [
    {"id": 1, "url": "https://www.nature.com/..."},
    {"id": 2, "url": "https://arxiv.org/abs/..."}
  ]
}
```

It:

1. splits `answer` into sentences,
2. checks `[n]` present on ≥ `COVERAGE_MIN` of them,
3. validates that each cited `[n]` is in `references`,
4. enforces provenance diversity (≤ `DIVERSITY_MAX` share from any one domain),
5. allows **SKIP** if `DOC_CLASS=opinion`.

## Run it (focused with filters)

**PASS**

```bash
python scripts/run_witnesses.py capsules \
  --capsule llm.citation_required_v1 \
  --witness citations_cover_claims \
  --json
```

**FAIL** (bad sources / low coverage)

```bash
ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json \
python scripts/run_witnesses.py capsules \
  --capsule llm.citation_required_v1 \
  --witness citations_cover_claims \
  --json
```

**SKIP** (opinion policy)

```bash
DOC_CLASS=opinion \
python scripts/run_witnesses.py capsules \
  --capsule llm.citation_required_v1 \
  --witness citations_cover_claims \
  --json
```

**Expected statuses**

* PASS run → `"capsule":"GREEN"`, `"witness":"PASS"`
* FAIL run → `"capsule":"RED"`,   `"witness":"FAIL"`
* SKIP run → `"capsule":"SKIP"`,  `"witness":"SKIP"`

> Tip: the runner prints each witness’s `inputs` (paths) in stdout JSON so you can confirm which fixture was used. OS env vars **override** capsule `env:`.

## Makefile shortcuts (optional)

```make
witness-citations-pass:
	$(PY) scripts/run_witnesses.py capsules \
	  --capsule llm.citation_required_v1 \
	  --witness citations_cover_claims --json

witness-citations-fail:
	ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json \
	$(PY) scripts/run_witnesses.py capsules \
	  --capsule llm.citation_required_v1 \
	  --witness citations_cover_claims --json

witness-citations-skip:
	DOC_CLASS=opinion \
	$(PY) scripts/run_witnesses.py capsules \
	  --capsule llm.citation_required_v1 \
	  --witness citations_cover_claims --json
```

## Security notes

* **Zero network** (pure text checks).
* Treat JSON fixtures as untrusted input; runner already has **timeouts** and minimal env.
* For CI, prefer **containerized** execution (no-net, read-only FS).