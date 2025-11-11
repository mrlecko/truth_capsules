import json
import re
import subprocess
import sys
from typing import Dict, List, Any, Optional
import pytest

def _status(data):
    # tiny helper if you like
    return data[0]["status"]

def _extract_first_json_array(text: str) -> str:
    """
    Find the first JSON array that starts at beginning of a line and
    return exactly that balanced array (quote/escape aware).
    This avoids '[' that appear inside the 'Env :' echo line.
    """
    # find '[' that begins a line
    for m in re.finditer(r'(?m)^\[', text):
        i = m.start()
        s = text[i:]
        depth = 0
        in_str = False
        esc = False
        for j, ch in enumerate(s):
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == '[':
                    depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0:
                        cand = s[: j + 1]
                        # verify it's JSON
                        json.loads(cand)
                        return cand
        # if this start didn't produce valid JSON, continue to next start
    raise ValueError("No top-level JSON array found in output")

def _build_env_vars_arg(env_vars: Optional[Dict[str, str]]) -> str:
    """
    Build the single ENV_VARS string exactly as the Makefile expects.
    Do not add quoting; values must not contain spaces.
    """
    if not env_vars:
        return ""
    parts = []
    for k, v in env_vars.items():
        if " " in str(v):
            raise ValueError(f"ENV var {k} contains spaces; add a fixture that writes a file and pass the path.")
        parts.append(f"-e {k}={v}")
    return " ".join(parts)

def _run_make(capsule: str, witness: str, env_vars: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    cmd = ["make", "witness-sandbox", f"CAPSULE={capsule}", f"WITNESS={witness}", "JSON=1"]
    env_str = _build_env_vars_arg(env_vars)
    if env_str:
        cmd.append(f"ENV_VARS={env_str}")

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = proc.stdout

    try:
        payload = _extract_first_json_array(out)
        data = json.loads(payload)
        assert isinstance(data, list) and data, f"Runner returned empty/invalid JSON: {payload}"
        return data
    except Exception as e:
        print("----- runner stdout begin -----", file=sys.stderr)
        print(out, file=sys.stderr)
        print("----- runner stdout end   -----", file=sys.stderr)
        raise AssertionError(f"Failed to parse witness JSON for {capsule}::{witness}: {e}")



def _assert_capsule_status(data: List[Dict[str, Any]], expected_status: str):
    cap = data[0]
    got = cap.get("status")
    assert got == expected_status, f"Expected capsule status {expected_status}, got {got}. Full: {json.dumps(cap, indent=2)}"

def _env_ci_license():
    return {
        "SBOM_PATH": "artifacts/examples/ci/sbom.json",
        "ALLOWED_LICENSES_JSON": '["MIT","Apache-2.0","BSD-3-Clause","BSD-2-Clause","ISC","Python-2.0"]',
        "STRICT_FIELDS_ONLY": "true",
        "IGNORE_NUMERIC_TOKENS": "true",
    }

def _env_ci_container():
    return {"DOCKERFILE_PATH": "artifacts/examples/ci/Dockerfile"}

def _env_ci_repro():
    return {
        "BUILD_CMD": "/bin/true",
        "ARTIFACT_PATH": "artifacts/examples/ci/build/out/demo-artifact.txt",
    }

def _env_ci_env_secrets():
    return {
        "ENV_DUMP_PATH": "artifacts/examples/ci/env_dump.txt",
        "FORBIDDEN_PREFIXES_JSON": '["AWS_","GCP_","AZURE_","GH_TOKEN","SLACK_","PRIVATE_KEY","OPENAI_API_KEY","SECRET","TOKEN"]',
    }

def _env_dev_risks(all_green: bool):
    return {
        "REVIEW_PATH": (
            "artifacts/examples/dev/pr_review_good.md"
            if all_green else
            "artifacts/examples/pr_review_bad.md"
        ),
        "DIFF_PATH": "artifacts/examples/pr_diff.patch",
    }

def _env_dev_todo(all_green: bool):
    return {
        "DIFF_PATH": (
            "artifacts/examples/pr_diff_norisk.patch"
            if all_green else
            "artifacts/examples/pr_diff.patch"
        ),
        "TICKET_REGEX": r"(PROJ|JIRA)-[0-9]+",
    }

def _env_dev_secret_scan():
    return {
        "REPO_PATH": "artifacts",
        "MAX_FILES": "2000",
        "SKIP_DIRS_JSON": '[".git","node_modules","venv",".venv",".cache","dist","build","__pycache__"]',
    }

def _env_support_pii():
    return {"EXAMPLES_PATH": "artifacts/examples/support_agent/examples.txt", "FAIL_ON_ANY": "true"}

def _env_support_intents():
    return {
        "RULES_PATH": "artifacts/examples/support_agent/intent_rules.json",
        "QUERIES_PATH": "artifacts/examples/support_agent/queries.jsonl",
        "TOPK": "1",
    }

# ----- 1) CI QUALITY GATES -----

def test_ci_sbom_present():
    data = _run_make("ci.sbom_present_v1", "sbom_file_exists", {})
    _assert_capsule_status(data, "GREEN")

def test_ci_license_compliance():
    data = _run_make("ci.license_compliance_v1", "spdx_allowlist_only", _env_ci_license())
    _assert_capsule_status(data, "GREEN")

def test_ci_container_hardening():
    data = _run_make("ci.container_hardening_v1", "dockerfile_has_nonroot_nocache_pins", _env_ci_container())
    _assert_capsule_status(data, "GREEN")

def test_ci_reproducible_hash():
    data = _run_make("ci.reproducible_artifact_hash_v1", "repeatable_hash_check", _env_ci_repro())
    _assert_capsule_status(data, "GREEN")

def test_ci_secrets_in_env():
    data = _run_make("ci.secrets_in_build_env_v1", "no_forbidden_env_keys", _env_ci_env_secrets())
    _assert_capsule_status(data, "GREEN")

# ----- 2) DEVELOPER VELOCITY -----


def test_dev_diff_risk_tags(all_green):
    data = _run_make("dev.diff_risk_tags_v1", "pr_review_covers_risks", _env_dev_risks(all_green))
    assert _status(data) == ("GREEN" if all_green else "RED")
    if not all_green:
        # Demo scenario: we expect RED (missing 'security'); mark expected failure so suite still passes.
        if data[0].get("status") != "RED":
            pytest.fail(f"Expected RED demo, got {data[0].get('status')}")
        pytest.xfail("Intentional RED demo when ALL_GREEN=0 (missing security tag).")
    _assert_capsule_status(data, "GREEN")


def test_dev_enforce_todo_ticket(all_green):
    data = _run_make("dev.enforce_todo_ticket_v1", "todo_refs_present", _env_dev_todo(all_green))
    assert _status(data) == ("GREEN" if all_green else "RED")
    if not all_green:
        # Demo scenario: we expect RED (TODO without ticket)
        if data[0].get("status") != "RED":
            pytest.fail(f"Expected RED demo, got {data[0].get('status')}")
        pytest.xfail("Intentional RED demo when ALL_GREEN=0 (TODO missing ticket).")
    _assert_capsule_status(data, "GREEN")

def test_dev_secret_scan_baseline():
    data = _run_make("dev.secret_scan_baseline_v1", "no_high_entropy_or_keys", _env_dev_secret_scan())
    _assert_capsule_status(data, "GREEN")

# ----- 3) SUPPORT COPILOT -----

def test_support_pii_redaction_smoke():
    data = _run_make("support.pii_redaction_smoke_v1", "no_plaintext_pii_in_examples", _env_support_pii())
    _assert_capsule_status(data, "GREEN")

def test_support_intent_router_sanity():
    data = _run_make("support.intent_router_sanity_v1", "routes_top_intents_correctly", _env_support_intents())
    _assert_capsule_status(data, "GREEN")

# ----- 4) META EXPLAINER -----

def test_meta_truth_capsules_digest():
    data = _run_make("meta.truth_capsules_v1", "canonical_digest_demo", {})
    _assert_capsule_status(data, "GREEN")
