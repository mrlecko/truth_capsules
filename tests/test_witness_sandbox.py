# tests/test_witness_sandbox.py
"""
Sandbox smoke-tests for running witnesses in an isolated container.

What this validates:
- The sandbox image builds and runs.
- The witness runner works inside the sandbox.
- PASS / FAIL / SKIP behaviors and exit codes are correct.
- Paths are resolved relative to repo root and mounted read-only.

Prereqs:
- Docker (or Podman) available and usable.
- Example fixtures in artifacts/examples/ (from the repo).
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "artifacts" / "examples"

# Example files expected by the sample witnesses
PR_DIFF = EXAMPLES / "pr_diff.patch"
PR_REVIEW_GOOD = EXAMPLES / "pr_review.md"
PR_REVIEW_BAD = EXAMPLES / "pr_review_bad.md"
ANS_GOOD = EXAMPLES / "answer_with_citation.json"
ANS_BAD = EXAMPLES / "answer_with_citation_bad.json"


def _engine_available() -> str | None:
    """Return 'docker' or 'podman' if available, otherwise None."""
    for exe in ("docker", "podman"):
        if shutil.which(exe):
            try:
                # Quick sanity check (non-zero is fine if daemon is down)
                subprocess.run([exe, "--version"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return exe
            except Exception:
                pass
    return None


def _require_examples():
    missing = [p for p in [PR_DIFF, PR_REVIEW_GOOD, PR_REVIEW_BAD, ANS_GOOD, ANS_BAD] if not p.exists()]
    if missing:
        pytest.skip(f"Missing example fixtures: {', '.join(str(m.relative_to(REPO_ROOT)) for m in missing)}")


@pytest.fixture(scope="session")
def sandbox_engine():
    eng = _engine_available()
    if not eng:
        pytest.skip("No container engine (docker/podman) available on PATH")
    return eng


@pytest.fixture(scope="session", autouse=True)
def build_sandbox_image(sandbox_engine):
    """Build the runner image once for this session."""
    env = os.environ.copy()
    env["SANDBOX_ENGINE"] = sandbox_engine
    # Allow overriding the image tag if the Makefile supports SANDBOX_IMAGE
    cmd = ["make", "sandbox-build"]
    r = subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("--- sandbox-build stdout ---\n" + r.stdout + "\n")
        sys.stderr.write("--- sandbox-build stderr ---\n" + r.stderr + "\n")
        pytest.skip("Failed to build sandbox image (see logs above)")


def _run_make_witness(capsule: str | None, witness: str | None, env_vars: str = "", json_out: bool = True) -> tuple[int, list[dict]]:
    """
    Invoke: make witness-sandbox [CAPSULE=...] [WITNESS=...] [ENV_VARS='-e K=V ...'] [JSON=1]
    Returns (exit_code, parsed_json_list)
    """
    args = ["make", "witness-sandbox"]
    if capsule:
        args.append(f"CAPSULE={capsule}")
    if witness:
        args.append(f"WITNESS={witness}")
    if env_vars:
        args.append(f"ENV_VARS={env_vars}")
    if json_out:
        args.append("JSON=1")

    proc = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)
    stdout = proc.stdout

    # The target may echo banners/commands. Extract the last JSON array from stdout.
    # Strategy: find the last '[' ... ']' that parses as JSON list.
    def _extract_last_json_array(s: str) -> list[dict]:
    # Walk closing brackets from the end until we parse a JSON list.
        last_close = s.rfind("]")
        while last_close != -1:
            last_open = s.rfind("[", 0, last_close + 1)
            if last_open == -1:
                break
            candidate = s[last_open:last_close + 1].strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, list):
                    return data
            except Exception:
                pass
            last_close = s.rfind("]", 0, last_close)  # move left
        raise AssertionError(f"Could not parse JSON from stdout.\n--- stdout ---\n{s}\n")


    data = _extract_last_json_array(stdout)
    return proc.returncode, data


def _assert_one_result(data: list[dict]) -> dict:
    assert isinstance(data, list) and len(data) == 1, f"Expected single result list, got: {data!r}"
    res = data[0]
    assert "status" in res and "witness_results" in res, f"Malformed result: {res!r}"
    return res


def _find_wr(res: dict) -> dict:
    wrs = res.get("witness_results") or []
    assert len(wrs) == 1, f"Expected single witness result, got {wrs!r}"
    wr = wrs[0]
    assert "status" in wr and "returncode" in wr and "stdout" in wr, f"Malformed witness result: {wr!r}"
    return wr


# -----------------------------
# PR Risk-Coverage witness tests
# -----------------------------

@pytest.mark.slow
def test_sandbox_pr_risk_pass(build_sandbox_image):
    _require_examples()
    rc, data = _run_make_witness(
        capsule="llm.pr_risk_tags_v1",
        witness="pr_review_covers_risks",
        env_vars=f"'-e REVIEW_PATH={PR_REVIEW_GOOD.relative_to(REPO_ROOT)} -e DIFF_PATH={PR_DIFF.relative_to(REPO_ROOT)}'",
        json_out=True,
    )
    assert rc == 0, f"Expected exit 0 on PASS, got {rc}"
    res = _assert_one_result(data)
    assert res["status"] == "GREEN"
    wr = _find_wr(res)
    assert wr["status"] == "PASS"
    assert wr["returncode"] == 0


@pytest.mark.slow
def test_sandbox_pr_risk_fail_missing_mitigation(build_sandbox_image):
    _require_examples()
    rc, data = _run_make_witness(
        capsule="llm.pr_risk_tags_v1",
        witness="pr_review_covers_risks",
        env_vars=f"'-e REVIEW_PATH={PR_REVIEW_BAD.relative_to(REPO_ROOT)} -e DIFF_PATH={PR_DIFF.relative_to(REPO_ROOT)}'",
        json_out=True,
    )
    # GNU make exits with 2 for any recipe error, even if the underlying
    # command returned 1. The witness itself returns 1 on FAIL, and that
    # is reflected in the JSON payload (w["returncode"] == 1).
    # Accept (1, 2) at the process level and assert failure via JSON.
    assert rc in (1, 2), f"Expected non-zero on FAIL, got {rc}"
    res = _assert_one_result(data)
    assert res["status"] == "RED"
    wr = _find_wr(res)
    assert wr["status"] == "FAIL"
    assert wr["returncode"] != 0


# -----------------------------
# Citations witness tests
# -----------------------------

@pytest.mark.slow
def test_sandbox_citations_pass(build_sandbox_image):
    _require_examples()
    rc, data = _run_make_witness(
        capsule="llm.citation_required_v1",
        witness="citations_cover_claims",
        env_vars="",  # default ANSWER_PATH points to good example in capsule env
        json_out=True,
    )
    assert rc == 0
    res = _assert_one_result(data)
    assert res["status"] == "GREEN"
    wr = _find_wr(res)
    assert wr["status"] == "PASS"
    assert wr["returncode"] == 0


@pytest.mark.slow
def test_sandbox_citations_fail_bad_coverage(build_sandbox_image):
    _require_examples()
    rc, data = _run_make_witness(
        capsule="llm.citation_required_v1",
        witness="citations_cover_claims",
        env_vars=f"'-e ANSWER_PATH={ANS_BAD.relative_to(REPO_ROOT)}'",
        json_out=True,
    )
    assert rc in (1, 2)
    res = _assert_one_result(data)
    assert res["status"] == "RED"
    wr = _find_wr(res)
    assert wr["status"] == "FAIL"
    assert wr["returncode"] != 0
    # Optional: check reason present in stdout JSON
    assert "coverage-too-low" in (wr["stdout"] or "")


@pytest.mark.slow
def test_sandbox_citations_skip_opinion(build_sandbox_image):
    _require_examples()
    rc, data = _run_make_witness(
        capsule="llm.citation_required_v1",
        witness="citations_cover_claims",
        env_vars="'-e DOC_CLASS=opinion'",
        json_out=True,
    )
    # SKIP is a clean 0 exit
    assert rc == 0
    res = _assert_one_result(data)
    assert res["status"] == "SKIP"
    wr = _find_wr(res)
    assert wr["status"] == "SKIP"
    assert wr["returncode"] == 0
