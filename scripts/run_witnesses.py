#!/usr/bin/env python3
"""
Truth Capsule Witness Runner - Execute witness code with sandboxing support.

Runs executable witnesses embedded in capsule YAML files. Witnesses are code
artifacts that verify adherence to capsule rules.

⚠️  WARNING: Witnesses execute arbitrary code. Use appropriate sandboxing
    for untrusted capsules. This script provides basic process isolation only.

For production use, run witnesses in containers, VMs, or other isolation.
See WITNESSES_GUIDE.md for security best practices.
"""
import sys
import os
import json
import argparse
import subprocess
import tempfile
import yaml
from typing import Dict, List, Any
from pathlib import Path

# Supported languages and their default entrypoints
LANGUAGE_ENTRYPOINTS = {
    "python": "python3",
    "node": "node",
    "bash": "bash",
    "shell": "sh",
}


def load_capsules(path: str) -> List[Dict[str, Any]]:
    """Load all YAML capsules from the specified path.

    Args:
        path: File or directory path

    Returns:
        List of capsule dicts with __file__ metadata
    """
    items = []

    if os.path.isfile(path):
        # Single file
        files = [path]
    elif os.path.isdir(path):
        # Directory: find all YAML files
        files = []
        for root, dirs, filenames in os.walk(path):
            for filename in sorted(filenames):
                if filename.endswith((".yaml", ".yml")):
                    files.append(os.path.join(root, filename))
    else:
        return items

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f.read()) or {}
            data["__file__"] = filepath
            items.append(data)
        except Exception as e:
            items.append({
                "__file__": filepath,
                "__error__": f"Parse error: {str(e)}"
            })

    return items


def run_witness(witness: Dict[str, Any], capsule_file: str) -> Dict[str, Any]:
    """Run a single witness and return the result.

    Args:
        witness: Witness configuration dict
        capsule_file: Path to capsule file (for context)

    Returns:
        Result dict with name, status, returncode, stdout, stderr
    """
    name = witness.get("name", "unnamed")
    language = witness.get("language")
    code = witness.get("code", "")
    entrypoint = witness.get("entrypoint") or LANGUAGE_ENTRYPOINTS.get(language, language)
    args = witness.get("args", [])
    env_config = witness.get("env", {})
    workdir = witness.get("workdir", ".")
    timeout_ms = witness.get("timeout_ms", 5000)
    stdin_data = witness.get("stdin", "")

    # Validate required fields
    if not language or language not in LANGUAGE_ENTRYPOINTS:
        return {
            "name": name,
            "status": "ERROR",
            "returncode": -1,
            "stdout": "",
            "stderr": f"Unsupported or missing language: {language}"
        }

    if not code:
        return {
            "name": name,
            "status": "ERROR",
            "returncode": -1,
            "stdout": "",
            "stderr": "Missing witness code"
        }

    # Determine file extension
    ext_map = {"python": ".py", "node": ".js", "bash": ".sh", "shell": ".sh"}
    ext = ext_map.get(language, ".txt")

    # Write code to temporary file
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=ext,
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            code_file = f.name

        # Prepare environment (explicit allowlist only)
        # Start with minimal environment
        safe_env = {}
        for key, value in env_config.items():
            safe_env[key] = str(value)

        # Prepare command
        cmd = [entrypoint, code_file] + args

        # Change to workdir if specified
        cwd = os.path.abspath(workdir)

        # Execute with timeout
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout_ms / 1000.0,
                env=safe_env if safe_env else None,
                cwd=cwd,
                input=stdin_data.encode('utf-8') if stdin_data else None
            )

            status = "PASS" if result.returncode == 0 else "FAIL"

            return {
                "name": name,
                "status": status,
                "returncode": result.returncode,
                "stdout": result.stdout.decode('utf-8', errors='replace'),
                "stderr": result.stderr.decode('utf-8', errors='replace')
            }

        except subprocess.TimeoutExpired:
            return {
                "name": name,
                "status": "TIMEOUT",
                "returncode": 124,
                "stdout": "",
                "stderr": f"Execution exceeded {timeout_ms}ms timeout"
            }

        except FileNotFoundError:
            return {
                "name": name,
                "status": "ERROR",
                "returncode": -1,
                "stdout": "",
                "stderr": f"Entrypoint not found: {entrypoint}"
            }

    except Exception as e:
        return {
            "name": name,
            "status": "ERROR",
            "returncode": -1,
            "stdout": "",
            "stderr": f"Execution error: {str(e)}"
        }

    finally:
        # Clean up temporary file
        try:
            if 'code_file' in locals():
                os.unlink(code_file)
        except:
            pass


def run_capsule_witnesses(capsule: Dict[str, Any]) -> Dict[str, Any]:
    """Run all witnesses for a capsule.

    Args:
        capsule: Capsule dict with witnesses list

    Returns:
        Result dict with capsule ID, status, and witness results
    """
    capsule_id = capsule.get("id", "unknown")
    capsule_file = capsule.get("__file__", "")
    witnesses = capsule.get("witnesses", [])

    if not witnesses:
        return {
            "capsule": capsule_id,
            "status": "SKIP",
            "witness_results": []
        }

    results = []
    overall_status = "GREEN"

    for witness in witnesses:
        result = run_witness(witness, capsule_file)
        results.append(result)

        if result["status"] in ("FAIL", "ERROR", "TIMEOUT"):
            overall_status = "RED"

    return {
        "capsule": capsule_id,
        "status": overall_status,
        "witness_results": results
    }


def format_human_output(all_results: List[Dict[str, Any]]) -> str:
    """Format results as human-readable text.

    Args:
        all_results: List of capsule results

    Returns:
        Formatted string
    """
    lines = []

    for result in all_results:
        capsule_id = result["capsule"]
        status = result["status"]
        witness_results = result["witness_results"]

        if status == "SKIP":
            continue

        lines.append(f"\n{capsule_id}:")

        for wr in witness_results:
            name = wr["name"]
            s = wr["status"]

            if s == "PASS":
                lines.append(f"  ✓ {name} PASS")
            elif s == "FAIL":
                lines.append(f"  ✗ {name} FAIL")
                if wr.get("stderr"):
                    for line in wr["stderr"].strip().split("\n"):
                        lines.append(f"    {line}")
            elif s == "TIMEOUT":
                lines.append(f"  ⏱ {name} TIMEOUT")
                lines.append(f"    {wr.get('stderr', 'Execution timeout')}")
            elif s == "ERROR":
                lines.append(f"  ⚠ {name} ERROR")
                lines.append(f"    {wr.get('stderr', 'Execution error')}")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "path",
        help="Capsule file or directory containing capsule YAML files"
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable format"
    )
    ap.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show stdout/stderr for all witnesses (not just failures)"
    )

    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"ERROR: Path not found: {args.path}", file=sys.stderr)
        sys.exit(2)

    # Load capsules
    capsules = load_capsules(args.path)

    if not capsules:
        print(f"No capsules found in: {args.path}", file=sys.stderr)
        sys.exit(2)

    # Run witnesses for each capsule
    all_results = []
    for capsule in capsules:
        if "__error__" in capsule:
            print(f"WARNING: Skipping {capsule['__file__']}: {capsule['__error__']}", file=sys.stderr)
            continue

        result = run_capsule_witnesses(capsule)
        all_results.append(result)

    # Output results
    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        output = format_human_output(all_results)
        print(output)

        # Summary
        total = len([r for r in all_results if r["status"] != "SKIP"])
        passed = len([r for r in all_results if r["status"] == "GREEN"])
        failed = len([r for r in all_results if r["status"] == "RED"])

        print(f"\n{'='*60}")
        print(f"Capsules: {total}  Passed: {passed}  Failed: {failed}")

    # Exit with error if any witnesses failed
    if any(r["status"] == "RED" for r in all_results):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
