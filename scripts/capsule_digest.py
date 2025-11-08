#!/usr/bin/env python3
"""
Truth Capsule Digest Manager - Calculate and update SHA256 digests for capsules.

This script computes the canonical digest for capsule core fields and updates
the provenance.signing.digest field. Use this to initialize or reset digests.

Usage:
    python capsule_digest.py capsules/           # Update all capsules
    python capsule_digest.py capsules/ --verify  # Verify without updating
    python capsule_digest.py capsules/ --json    # JSON output
"""
import os
import sys
import json
import hashlib
import argparse
import yaml
from typing import Dict, Any, List


def canonical_json(obj: Any) -> str:
    """
    Convert object to canonical JSON string (deterministic ordering).

    Arrays are unchanged, objects are sorted by key alphabetically.
    This matches the canonicalJSON function in the SPA.
    """
    if isinstance(obj, list):
        return "[" + ",".join(canonical_json(item) for item in obj) + "]"
    elif isinstance(obj, dict):
        keys = sorted(obj.keys())
        pairs = [json.dumps(k) + ":" + canonical_json(obj[k]) for k in keys]
        return "{" + ",".join(pairs) + "}"
    else:
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def core_for_digest(capsule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract core fields used for digest calculation.

    Matches the coreForDigest function in the SPA JavaScript.
    """
    pedagogy = capsule.get("pedagogy") or []
    if isinstance(pedagogy, list):
        pedagogy = [{"kind": p.get("kind"), "text": p.get("text")} for p in pedagogy if isinstance(p, dict)]
    else:
        pedagogy = []

    return {
        "id": capsule.get("id"),
        "version": capsule.get("version"),
        "domain": capsule.get("domain"),
        "title": capsule.get("title"),
        "statement": capsule.get("statement"),
        "assumptions": capsule.get("assumptions") if isinstance(capsule.get("assumptions"), list) else [],
        "pedagogy": pedagogy
    }


def calculate_digest(capsule: Dict[str, Any]) -> str:
    """
    Calculate SHA256 digest of canonical JSON representation of core fields.
    """
    core = core_for_digest(capsule)
    canonical = canonical_json(core)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def update_capsule_digest(filepath: str, verify_only: bool = False) -> Dict[str, Any]:
    """
    Update or verify digest for a single capsule file.

    Args:
        filepath: Path to capsule YAML file
        verify_only: If True, verify without updating

    Returns:
        dict with status, old_digest, new_digest, updated
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            capsule = yaml.safe_load(f)
    except Exception as e:
        return {
            "file": filepath,
            "status": "error",
            "error": f"Failed to load YAML: {str(e)}",
            "updated": False
        }

    if not isinstance(capsule, dict):
        return {
            "file": filepath,
            "status": "error",
            "error": "Invalid YAML structure (not a dict)",
            "updated": False
        }

    # Calculate new digest
    new_digest = calculate_digest(capsule)

    # Get existing digest (if any)
    provenance = capsule.get("provenance") or {}
    signing = provenance.get("signing") or {}
    old_digest = signing.get("digest")

    # Determine status
    if old_digest == new_digest:
        status = "ok"
    elif old_digest is None:
        status = "missing"
    else:
        status = "mismatch"

    result = {
        "file": filepath,
        "id": capsule.get("id"),
        "status": status,
        "old_digest": old_digest,
        "new_digest": new_digest,
        "updated": False
    }

    # Update if needed and not verify-only
    if status != "ok" and not verify_only:
        # Ensure provenance structure exists
        if "provenance" not in capsule:
            capsule["provenance"] = {}
        if "signing" not in capsule["provenance"]:
            capsule["provenance"]["signing"] = {}

        # Update digest
        capsule["provenance"]["signing"]["digest"] = new_digest

        # Write back to file
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.safe_dump(capsule, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
            result["updated"] = True
            result["status"] = "updated"
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"Failed to write YAML: {str(e)}"

    return result


def process_directory(dirpath: str, verify_only: bool = False) -> List[Dict[str, Any]]:
    """
    Process all capsule YAML files in a directory.

    Args:
        dirpath: Directory containing capsule files
        verify_only: If True, verify without updating

    Returns:
        List of result dicts for each file
    """
    results = []

    for root, dirs, files in os.walk(dirpath):
        for filename in sorted(files):
            if filename.endswith((".yaml", ".yml")):
                filepath = os.path.join(root, filename)
                result = update_capsule_digest(filepath, verify_only=verify_only)
                results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="capsules",
        help="Directory containing capsule YAML files (default: capsules)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify digests without updating"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(f"ERROR: {args.path} is not a directory", file=sys.stderr)
        sys.exit(2)

    # Process all capsules
    results = process_directory(args.path, verify_only=args.verify)

    # Compute summary
    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "updated": sum(1 for r in results if r["updated"]),
        "missing": sum(1 for r in results if r["status"] == "missing"),
        "mismatch": sum(1 for r in results if r["status"] == "mismatch"),
        "errors": sum(1 for r in results if r["status"] == "error")
    }

    # Output results
    if args.json:
        output = {
            "summary": summary,
            "results": results
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        mode = "Verification" if args.verify else "Update"
        print(f"\nDigest {mode} Summary:")
        print(f"  Total:    {summary['total']}")
        print(f"  OK:       {summary['ok']}")

        if not args.verify:
            print(f"  Updated:  {summary['updated']}")

        if summary['missing'] > 0:
            print(f"  Missing:  {summary['missing']}")
        if summary['mismatch'] > 0:
            print(f"  Mismatch: {summary['mismatch']}")
        if summary['errors'] > 0:
            print(f"  Errors:   {summary['errors']}")

        # Show details for non-ok items
        print()
        for result in results:
            if result["status"] == "ok":
                continue

            capsule_id = result.get("id") or "?"
            status_symbol = {
                "updated": "✓",
                "missing": "◯",
                "mismatch": "✗",
                "error": "⚠"
            }.get(result["status"], "?")

            print(f"{status_symbol} {result['file']}  ({capsule_id})")

            if result["status"] == "error":
                print(f"  ERROR: {result.get('error')}")
            elif result["status"] == "mismatch":
                print(f"  OLD: {result.get('old_digest', 'none')[:16]}...")
                print(f"  NEW: {result.get('new_digest', 'none')[:16]}...")
            elif result["status"] == "missing":
                print(f"  NEW: {result.get('new_digest', 'none')[:16]}...")

            if result.get("updated"):
                print(f"  → Updated")

    # Exit with error code if there are issues
    if args.verify:
        # In verify mode, exit with error if any mismatches or errors
        sys.exit(1 if (summary["mismatch"] > 0 or summary["errors"] > 0) else 0)
    else:
        # In update mode, exit with error only if there are errors
        sys.exit(1 if summary["errors"] > 0 else 0)


if __name__ == "__main__":
    main()
