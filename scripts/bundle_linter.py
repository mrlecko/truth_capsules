#!/usr/bin/env python3
"""
Truth Capsule Bundle Linter - Schema validation for bundle YAML files.

Validates bundle structure against schemas/bundle.schema.v1.json and checks
that referenced capsules exist.
"""
import sys
import os
import json
import argparse
import yaml
import glob
from typing import Dict, List, Tuple

# Try to import jsonschema, but make it optional
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def load_bundles(path: str) -> List[Dict]:
    """Load all YAML bundles from the specified directory.

    Returns:
        List of dicts with bundle data plus __file__ metadata.
        On parse errors, includes __error__ key instead.
    """
    items = []
    pattern = os.path.join(path, "*.yaml")
    for filepath in sorted(glob.glob(pattern)):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            data["__file__"] = filepath
            items.append(data)
        except Exception as e:
            items.append({
                "__file__": filepath,
                "__error__": f"Parse error: {str(e)}"
            })
    return items


def load_capsule_ids(root: str) -> set:
    """Load all capsule IDs from the capsules directory.

    Returns:
        Set of capsule IDs found in the capsules directory.
    """
    ids = set()
    pattern = os.path.join(root, "capsules", "**", "*.yaml")
    for filepath in sorted(glob.glob(pattern, recursive=True)):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            capsule_id = data.get("id")
            if capsule_id:
                ids.add(capsule_id)
        except Exception:
            pass  # Skip unparseable capsules
    return ids


def lint_bundle(bundle: Dict, schema: Dict = None, capsule_ids: set = None, strict: bool = False) -> Tuple[List[str], List[str]]:
    """Validate a single bundle.

    Args:
        bundle: Parsed bundle dict with __file__ key
        schema: JSON schema dict for validation (optional)
        capsule_ids: Set of valid capsule IDs (optional)
        strict: If True, enforce stricter checks

    Returns:
        (errors, warnings) tuple of message lists
    """
    errs, warns = [], []

    # Check for parse errors
    if "__error__" in bundle:
        errs.append(bundle["__error__"])
        return errs, warns

    # Validate required keys
    if not bundle.get("name"):
        errs.append("Missing required key: name")
    if not bundle.get("capsules"):
        errs.append("Missing required key: capsules")

    # Validate capsules is a list
    capsules = bundle.get("capsules")
    if capsules is not None and not isinstance(capsules, list):
        errs.append("capsules must be a list")
    elif capsules and len(capsules) == 0:
        warns.append("Bundle has no capsules listed")

    # Validate against JSON schema if available
    if schema and HAS_JSONSCHEMA:
        try:
            # Remove metadata keys before validation
            bundle_copy = {k: v for k, v in bundle.items() if not k.startswith("__")}
            jsonschema.validate(bundle_copy, schema)
        except jsonschema.ValidationError as e:
            if strict:
                errs.append(f"Schema validation error: {e.message}")
            else:
                warns.append(f"Schema validation warning: {e.message}")
        except jsonschema.SchemaError as e:
            warns.append(f"Invalid schema: {e.message}")

    # Check that referenced capsules exist
    if capsule_ids is not None and capsules:
        for cap_id in capsules:
            if cap_id not in capsule_ids:
                warns.append(f"Referenced capsule not found: {cap_id}")

    # Check excludes don't conflict with capsules
    excludes = bundle.get("excludes", [])
    if excludes and capsules:
        for exc_id in excludes:
            if exc_id in capsules:
                warns.append(
                    f"Capsule '{exc_id}' is both included and excluded "
                    "(will be excluded)"
                )

    # Validate version format if present
    version = bundle.get("version")
    if version:
        parts = str(version).split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            warns.append(
                f"Version should be semantic version (e.g., 1.0.0), got: {version}"
            )
    elif strict:
        warns.append("Bundle missing 'version' field (recommended for v1.1)")

    # Validate priority_overrides if present
    priority_overrides = bundle.get("priority_overrides")
    if priority_overrides:
        if not isinstance(priority_overrides, dict):
            errs.append("priority_overrides must be an object/dict")
        else:
            for cap_id, priority in priority_overrides.items():
                if not isinstance(priority, int):
                    warns.append(
                        f"priority_overrides['{cap_id}'] should be an integer"
                    )
                elif priority < 1 or priority > 100:
                    warns.append(
                        f"priority_overrides['{cap_id}'] should be between 1-100"
                    )

    # Validate order if present
    order = bundle.get("order")
    if order:
        if not isinstance(order, list):
            errs.append("order must be a list")
        elif capsules:
            # Check that all order items are in capsules
            for cap_id in order:
                if cap_id not in capsules:
                    warns.append(
                        f"order contains '{cap_id}' which is not in capsules list"
                    )

    return errs, warns


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "path",
        help="Path to bundles directory"
    )
    ap.add_argument(
        "--root",
        help="Path to truth-capsules root (for capsule ID validation)"
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation (schema errors become fatal)"
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    args = ap.parse_args()

    # Load schema
    schema = None
    if HAS_JSONSCHEMA:
        # Try to find schema relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(script_dir, "..", "schemas", "bundle.schema.v1.json")
        if os.path.exists(schema_path):
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load schema: {e}", file=sys.stderr)
    else:
        if not args.json:
            print("Warning: jsonschema not installed; schema validation disabled", file=sys.stderr)
            print("Install with: pip install jsonschema", file=sys.stderr)

    # Load capsule IDs if root provided
    capsule_ids = None
    if args.root:
        capsule_ids = load_capsule_ids(args.root)

    # Load and lint bundles
    bundles = load_bundles(args.path)

    total_errors = 0
    total_warnings = 0
    results = []

    for bundle in bundles:
        errs, warns = lint_bundle(bundle, schema, capsule_ids, args.strict)
        total_errors += len(errs)
        total_warnings += len(warns)

        result = {
            "file": bundle.get("__file__", "?"),
            "name": bundle.get("name", "?"),
            "errors": errs,
            "warnings": warns
        }
        results.append(result)

    # Output results
    if args.json:
        print(json.dumps({
            "bundles": len(bundles),
            "errors": total_errors,
            "warnings": total_warnings,
            "results": results
        }, indent=2))
    else:
        print(f"Bundles: {len(bundles)}  errors: {total_errors}  warnings: {total_warnings}")
        print()

        for result in results:
            if result["errors"] or result["warnings"]:
                print(f"- {os.path.basename(result['file'])}  ({result['name']})")
                for err in result["errors"]:
                    print(f"  ERROR: {err}")
                for warn in result["warnings"]:
                    print(f"  WARNING: {warn}")
                print()
            else:
                print(f"- {os.path.basename(result['file'])}  ({result['name']})")
                print()

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
