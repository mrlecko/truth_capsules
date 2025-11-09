# tests/test_witnesses.py
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_witnesses.py"
CAPSULES_DIR = ROOT / "capsules"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "pr_risk"

CAPSULE_ID = "llm.pr_risk_tags_v1"
WITNESS_NAME = "pr_review_covers_risks"


def _ensure_fixtures():
    """Create minimal fixtures for PASS/FAIL/SKIP if they don't exist."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    pr_diff = FIXTURES_DIR / "pr_diff.patch"
    pr_review_good = FIXTURES_DIR / "pr_review.md"
    pr_review_bad = FIXTURES_DIR / "pr_review_bad.md"
    pr_diff_norisk = FIXTURES_DIR / "pr_diff_norisk.patch"

    if not pr_diff.exists():
        pr_diff.write_text(
            "diff --git a/app/auth.py b/app/auth.py\n"
            "--- a/app/auth.py\n"
            "+++ b/app/auth.py\n"
            "@@\n"
            "+ import os, requests, shutil, socket\n"
            "+ API_URL = \"https://api.internal.example.com/login\"\n"
            "+ def handler(user_email):\n"
            "+     password = \"supersecret\"  # TODO remove hardcoded password\n"
            "+     token = requests.get(API_URL, timeout=3).text\n"
            "+     with open(\"/tmp/export.csv\", \"w\") as f:\n"
            "+         f.write(f\"user,{user_email}\\n\")\n"
            "+     os.remove(\"/tmp/old.txt\")\n"
            "+     return \"ok\"\n",
            encoding="utf-8",
        )

    if not pr_review_good.exists():
        pr_review_good.write_text(
            "# Review Notes\n\n"
            "Risks observed: auth, net, fs, secrets\n\n"
            "- **auth** — Mitigation: require MFA and feature flag on login path.\n"
            "- **net** — Mitigation: retry/backoff + circuit breaker; restrict domains.\n"
            "- **fs** — Mitigation: confine writes to temp dir; add unit tests.\n"
            "- **secrets** — Mitigation: remove hardcoded password; use secret manager.\n",
            encoding="utf-8",
        )

    if not pr_review_bad.exists():
        pr_review_bad.write_text("Looks fine. Ship it.\n", encoding="utf-8")

    if not pr_diff_norisk.exists():
        pr_diff_norisk.write_text(
            "diff --git a/README.md b/README.md\n"
            "--- a/README.md\n"
            "+++ b/README.md\n"
            "@@\n"
            "+ Minor doc tweak.\n",
            encoding="utf-8",
        )

    return {
        "diff": pr_diff,
        "review_good": pr_review_good,
        "review_bad": pr_review_bad,
        "diff_norisk": pr_diff_norisk,
    }


def _run_runner(env_overrides=None):
    """Run the witness runner with filters for our capsule/witness and return (rc, parsed_json_list)."""
    env = os.environ.copy()
    if env_overrides:
        env.update({k: str(v) for k, v in env_overrides.items()})

    cmd = [
        sys.executable,
        str(RUNNER),
        str(CAPSULES_DIR),
        "--capsule", CAPSULE_ID,
        "--witness", WITNESS_NAME,
        "--json",
    ]

    # We don't use check=True because FAIL is an expected test outcome sometimes.
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    stdout = proc.stdout.strip()

    # Runner prints a JSON list of capsule results
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Runner did not emit valid JSON. rc={proc.returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{proc.stderr}") from e

    return proc.returncode, data


def _extract_result(data):
    """Return (capsule_status, witness_status, witness_stdout_json) for our capsule/witness."""
    # data is a list with exactly one capsule (due to --capsule)
    assert isinstance(data, list) and data, "Runner returned empty result list."
    cap = data[0]
    assert cap.get("capsule") == CAPSULE_ID, f"Unexpected capsule id: {cap.get('capsule')}"
    wits = cap.get("witness_results") or []
    assert len(wits) == 1 and wits[0].get("name") == WITNESS_NAME, "Expected a single PR risk witness result."
    wit = wits[0]

    # Witness writes JSON to stdout; parse it for richer assertions
    stdout_text = wit.get("stdout", "").strip()
    wit_json = {}
    try:
        wit_json = json.loads(stdout_text)
    except Exception:
        # Keep going; we still can assert on statuses
        pass

    return cap.get("status"), wit.get("status"), wit_json


def test_pr_risk_pass():
    fx = _ensure_fixtures()
    rc, data = _run_runner({
        "DIFF_PATH": fx["diff"],
        "REVIEW_PATH": fx["review_good"],
    })
    capsule_status, witness_status, wit_json = _extract_result(data)

    assert rc == 0, f"Expected exit 0 on PASS, got {rc}"
    assert capsule_status == "GREEN", f"Expected capsule GREEN, got {capsule_status}"
    assert witness_status == "PASS", f"Expected witness PASS, got {witness_status}"
    assert wit_json.get("missing") == [], f"Expected no missing mitigations, got {wit_json.get('missing')}"


def test_pr_risk_fail():
    fx = _ensure_fixtures()
    rc, data = _run_runner({
        "DIFF_PATH": fx["diff"],
        "REVIEW_PATH": fx["review_bad"],
    })
    capsule_status, witness_status, wit_json = _extract_result(data)

    assert rc != 0, "Expected non-zero exit on FAIL"
    assert capsule_status == "RED", f"Expected capsule RED, got {capsule_status}"
    assert witness_status == "FAIL", f"Expected witness FAIL, got {witness_status}"
    missing = wit_json.get("missing") or []
    # Should report at least one missing tag
    assert missing and isinstance(missing, list), f"Expected missing list, got {missing}"


def test_pr_risk_skip_no_risks():
    fx = _ensure_fixtures()
    rc, data = _run_runner({
        "DIFF_PATH": fx["diff_norisk"],
        "REVIEW_PATH": fx["review_good"],  # review is irrelevant in SKIP
    })
    capsule_status, witness_status, wit_json = _extract_result(data)

    # SKIP should be a clean 0 exit (informational)
    assert rc == 0, f"Expected exit 0 on SKIP, got {rc}"
    assert capsule_status == "SKIP", f"Expected capsule SKIP, got {capsule_status}"
    assert witness_status == "SKIP", f"Expected witness SKIP, got {witness_status}"
    assert wit_json.get("found_tags") == [], f"Expected no found tags in SKIP, got {wit_json.get('found_tags')}"
