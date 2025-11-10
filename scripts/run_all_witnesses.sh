#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/run_all_witnesses.sh               # default (shows two RED demos)
#   ALL_GREEN=1 ./scripts/run_all_witnesses.sh   # force all GREEN

ALL_GREEN="${ALL_GREEN:-0}"
echo "ALL_GREEN=${ALL_GREEN}"

run() {
  local C="$1" W="$2" EV="${3:-}"
  echo "=== $C :: $W ==="
  if [[ -n "${EV}" ]]; then
    make witness-sandbox CAPSULE="$C" WITNESS="$W" JSON=1 ENV_VARS="$EV" || true
  else
    make witness-sandbox CAPSULE="$C" WITNESS="$W" JSON=1 || true
  fi
  echo
}

# --- 1) CI QUALITY GATES ---
run ci.sbom_present_v1              sbom_file_exists

run ci.license_compliance_v1        spdx_allowlist_only \
  "-e SBOM_PATH=artifacts/examples/ci/sbom.json \
   -e ALLOWED_LICENSES_JSON='[\"MIT\",\"Apache-2.0\",\"BSD-3-Clause\",\"BSD-2-Clause\",\"ISC\",\"Python-2.0\"]' \
   -e STRICT_FIELDS_ONLY=true \
   -e IGNORE_NUMERIC_TOKENS=true"

run ci.container_hardening_v1       dockerfile_has_nonroot_nocache_pins \
  "-e DOCKERFILE_PATH=artifacts/examples/ci/Dockerfile"

# Read-only container: skip rebuild and just hash the demo artifact
run ci.reproducible_artifact_hash_v1 repeatable_hash_check \
  "-e BUILD_CMD=/bin/true \
   -e ARTIFACT_PATH=artifacts/examples/ci/build/out/demo-artifact.txt"

run ci.secrets_in_build_env_v1      no_forbidden_env_keys \
  "-e ENV_DUMP_PATH=artifacts/examples/ci/env_dump.txt \
   -e FORBIDDEN_PREFIXES_JSON='[\"AWS_\",\"GCP_\",\"AZURE_\",\"GH_TOKEN\",\"SLACK_\",\"PRIVATE_KEY\",\"OPENAI_API_KEY\",\"SECRET\",\"TOKEN\"]'"

# --- 2) DEVELOPER VELOCITY ---
if [[ "$ALL_GREEN" == "1" ]]; then
  # Good review covers needed risk tags → GREEN
  run dev.diff_risk_tags_v1           pr_review_covers_risks \
    "-e REVIEW_PATH=artifacts/examples/dev/pr_review_good.md \
     -e DIFF_PATH=artifacts/examples/pr_diff.patch"

  # Diff with no TODOs (or TODO already ticketed) → GREEN
  run dev.enforce_todo_ticket_v1      todo_refs_present \
    "-e DIFF_PATH=artifacts/examples/pr_diff_norisk.patch \
     -e TICKET_REGEX='(PROJ|JIRA)-[0-9]+'"
else
  # Intentionally RED: review missing the 'security' risk tag
  run dev.diff_risk_tags_v1           pr_review_covers_risks \
    "-e REVIEW_PATH=artifacts/examples/pr_review_bad.md \
     -e DIFF_PATH=artifacts/examples/pr_diff.patch"

  # Intentionally RED: TODO without a ticket reference
  run dev.enforce_todo_ticket_v1      todo_refs_present \
    "-e DIFF_PATH=artifacts/examples/pr_diff.patch \
     -e TICKET_REGEX='(PROJ|JIRA)-[0-9]+'"
fi

# Baseline secret scan — scoped to fixtures for speed/robustness
run dev.secret_scan_baseline_v1     no_high_entropy_or_keys \
  "-e REPO_PATH=artifacts \
   -e MAX_FILES=2000 \
   -e SKIP_DIRS_JSON='[\".git\",\"node_modules\",\"venv\",\".venv\",\".cache\",\"dist\",\"build\",\"__pycache__\"]'"

# --- 3) SUPPORT COPILOT ---
run support.pii_redaction_smoke_v1  no_plaintext_pii_in_examples \
  "-e EXAMPLES_PATH=artifacts/examples/support_agent/examples.txt \
   -e FAIL_ON_ANY=true"

run support.intent_router_sanity_v1 routes_top_intents_correctly \
  "-e RULES_PATH=artifacts/examples/support_agent/intent_rules.json \
   -e QUERIES_PATH=artifacts/examples/support_agent/queries.jsonl \
   -e TOPK=1"

# --- 4) META EXPLAINER ---
run meta.truth_capsules_v1          canonical_digest_demo
