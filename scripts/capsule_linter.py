#!/usr/bin/env python3
"""
Truth Capsule Linter - Schema validation for capsule YAML files.

Validates required fields, provenance structure, pedagogy format, and detects
common issues like unicode escape sequences in YAML source.

Can optionally validate against a JSON Schema file for stricter validation.
"""
import sys
import os
import json
import argparse
import yaml
import re
from typing import Dict, List, Tuple, Optional

try:
    import jsonschema
    from jsonschema import Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# Schema constants
REQUIRED_KEYS = ["id", "version", "domain", "statement"]
ALLOWED_PEDAGOGY_KINDS = {"Socratic", "Aphorism"}
ALLOWED_REVIEW_STATUSES = {"draft", "in_review", "approved", "deprecated"}
ALLOWED_WITNESS_LANGUAGES = {"python", "node", "bash", "shell"}
ALLOWED_WITNESS_FS_MODES = {"ro", "rw"}

# Unicode escape pattern for detection in raw YAML
UNICODE_ESCAPE_PATTERN = re.compile(r'\\u[0-9a-fA-F]{4}')

# ID pattern: domain.name_vN or domain.name_vN_suffix
ID_PATTERN = re.compile(r'^[a-z0-9_.-]+_v\d+(?:_[a-z0-9_]+)?$')


def load_capsules(path: str) -> List[Dict]:
    """Load all YAML capsules from the specified directory.

    Recursively walks subdirectories (e.g., capsules/llm/*.yaml).

    Returns:
        List of dicts with capsule data plus __file__ and __raw__ metadata.
        On parse errors, includes __error__ key instead.
    """
    items = []
    for root, dirs, files in os.walk(path):
        for filename in sorted(files):
            if filename.endswith((".yaml", ".yml")):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        raw = f.read()
                    data = yaml.safe_load(raw) or {}
                    data["__file__"] = filepath
                    data["__raw__"] = raw
                    items.append(data)
                except Exception as e:
                    items.append({
                        "__file__": filepath,
                        "__error__": f"Parse error: {str(e)}"
                    })
    return items


def lint_capsule(capsule: Dict, strict: bool = False, schema: Optional[Dict] = None) -> Tuple[List[str], List[str]]:
    """Validate a single capsule.

    Args:
        capsule: Parsed capsule dict with __raw__ key
        strict: If True, enforce stricter checks (e.g., provenance.review.status)
        schema: Optional JSON Schema dict to validate against

    Returns:
        (errors, warnings) tuple of message lists
    """
    errs, warns = [], []

    # Validate against JSON Schema if provided
    if schema is not None:
        if not JSONSCHEMA_AVAILABLE:
            warns.append(
                "JSON Schema validation requested but jsonschema package not installed. "
                "Install with: pip install jsonschema"
            )
        else:
            # Create a clean copy without metadata fields
            clean_capsule = {k: v for k, v in capsule.items()
                           if not k.startswith("__")}

            validator = Draft7Validator(schema)
            schema_errors = sorted(validator.iter_errors(clean_capsule),
                                 key=lambda e: e.path)

            for error in schema_errors:
                path = ".".join(str(p) for p in error.path) if error.path else "root"
                errs.append(f"JSON Schema violation at {path}: {error.message}")

    # Check for unicode escape sequences in raw YAML (indicates bad encoding)
    raw = capsule.get("__raw__", "")
    if UNICODE_ESCAPE_PATTERN.search(raw):
        warns.append(
            "Contains unicode escape sequences (e.g., \\u2265). "
            "Use actual UTF-8 characters instead (e.g., ≥). "
            "Run fix_unicode_escapes.py to fix automatically."
        )

    # Validate required keys
    for key in REQUIRED_KEYS:
        if not capsule.get(key):
            errs.append(f"Missing required key: {key}")

    # Validate ID format
    capsule_id = capsule.get("id", "")
    if capsule_id and not ID_PATTERN.match(capsule_id):
        warns.append(
            f"ID should match pattern: domain.name_vN or domain.name_vN_suffix "
            f"(e.g., llm.citation_v1 or llm.citation_v1_signed)"
        )

    # Check domain/path consistency (warning only)
    # If capsule is in capsules/llm/foo.yaml, domain should be "llm"
    filepath = capsule.get("__file__", "")
    domain = capsule.get("domain", "")
    if filepath and domain:
        # Extract the immediate parent directory name
        # e.g., capsules/llm/foo.yaml → llm
        parts = filepath.replace("\\", "/").split("/")
        # Find "capsules" in the path
        if "capsules" in parts:
            capsules_idx = parts.index("capsules")
            # If there's a subdirectory between capsules/ and the file
            if capsules_idx + 2 < len(parts):  # capsules + subdir + file
                subdir = parts[capsules_idx + 1]
                if subdir != domain:
                    warns.append(
                        f"Domain/path mismatch: domain='{domain}' but file is in '{subdir}/' subdirectory. "
                        f"Consider moving to capsules/{domain}/ for consistency."
                    )

    # Validate assumptions (if present, must be a list)
    if "assumptions" in capsule:
        assumptions = capsule["assumptions"]
        if assumptions is not None and not isinstance(assumptions, list):
            errs.append("assumptions must be a list (or null)")

    # Validate pedagogy structure
    if "pedagogy" in capsule and capsule["pedagogy"]:
        pedagogy = capsule["pedagogy"]
        if not isinstance(pedagogy, list):
            errs.append("pedagogy must be a list")
        else:
            for i, item in enumerate(pedagogy):
                if not isinstance(item, dict):
                    errs.append(f"pedagogy[{i}] must be a dict with 'kind' and 'text'")
                    continue

                kind = item.get("kind")
                text = item.get("text")

                if kind not in ALLOWED_PEDAGOGY_KINDS:
                    warns.append(
                        f"pedagogy[{i}].kind='{kind}' not in {sorted(ALLOWED_PEDAGOGY_KINDS)}"
                    )
                if not text or not isinstance(text, str):
                    errs.append(f"pedagogy[{i}].text must be a non-empty string")

    # Validate witnesses structure (if present)
    if "witnesses" in capsule and capsule["witnesses"]:
        witnesses = capsule["witnesses"]
        if not isinstance(witnesses, list):
            errs.append("witnesses must be a list")
        else:
            for i, witness in enumerate(witnesses):
                if not isinstance(witness, dict):
                    errs.append(f"witnesses[{i}] must be a dict")
                    continue

                # Check required witness fields
                name = witness.get("name")
                language = witness.get("language")
                code = witness.get("code")

                if not name or not isinstance(name, str):
                    errs.append(f"witnesses[{i}].name must be a non-empty string")

                if not language:
                    errs.append(f"witnesses[{i}].language is required")
                elif language not in ALLOWED_WITNESS_LANGUAGES:
                    errs.append(
                        f"witnesses[{i}].language='{language}' not in "
                        f"{sorted(ALLOWED_WITNESS_LANGUAGES)}"
                    )

                if not code or not isinstance(code, str):
                    errs.append(f"witnesses[{i}].code must be a non-empty string")

                # Validate optional witness fields (type checking)
                if "entrypoint" in witness and not isinstance(witness["entrypoint"], str):
                    warns.append(f"witnesses[{i}].entrypoint should be a string")

                if "args" in witness and not isinstance(witness["args"], list):
                    errs.append(f"witnesses[{i}].args must be a list")

                if "env" in witness and not isinstance(witness["env"], dict):
                    errs.append(f"witnesses[{i}].env must be a dict")

                if "workdir" in witness and not isinstance(witness["workdir"], str):
                    warns.append(f"witnesses[{i}].workdir should be a string")

                if "timeout_ms" in witness:
                    timeout = witness["timeout_ms"]
                    if not isinstance(timeout, int) or timeout <= 0:
                        warns.append(f"witnesses[{i}].timeout_ms should be a positive integer")

                if "memory_mb" in witness:
                    memory = witness["memory_mb"]
                    if not isinstance(memory, int) or memory <= 0:
                        warns.append(f"witnesses[{i}].memory_mb should be a positive integer")

                if "net" in witness and not isinstance(witness["net"], bool):
                    warns.append(f"witnesses[{i}].net should be a boolean")

                if "fs_mode" in witness:
                    fs_mode = witness["fs_mode"]
                    if fs_mode not in ALLOWED_WITNESS_FS_MODES:
                        warns.append(
                            f"witnesses[{i}].fs_mode='{fs_mode}' not in "
                            f"{sorted(ALLOWED_WITNESS_FS_MODES)}"
                        )

                if "stdin" in witness and not isinstance(witness["stdin"], str):
                    warns.append(f"witnesses[{i}].stdin should be a string")

    # Validate provenance structure (if present)
    if "provenance" in capsule:
        prov = capsule["provenance"]
        if not isinstance(prov, dict):
            errs.append("provenance must be a dict")
        else:
            # Check for recommended provenance fields
            for field in ["author", "org", "license", "schema", "created"]:
                if field not in prov:
                    warns.append(f"provenance.{field} is recommended")

            # Validate review status
            if "review" in prov and isinstance(prov["review"], dict):
                review = prov["review"]
                status = review.get("status")
                if status and status not in ALLOWED_REVIEW_STATUSES:
                    errs.append(
                        f"provenance.review.status='{status}' not in "
                        f"{sorted(ALLOWED_REVIEW_STATUSES)}"
                    )
                # Strict mode: require approved status for production
                if strict and status != "approved":
                    errs.append(
                        f"Strict mode: provenance.review.status must be 'approved' "
                        f"(found '{status}')"
                    )

    return errs, warns


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "path",
        nargs="?",
        default="./truth-capsules-v1/capsules",
        help="Directory containing capsule YAML files"
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON instead of human-readable format"
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Enforce strict checks (e.g., require review.status=approved)"
    )
    ap.add_argument(
        "--schema",
        type=str,
        help="Path to JSON Schema file for validation (e.g., schemas/capsule.schema.v1.json)"
    )
    args = ap.parse_args()

    if not os.path.isdir(args.path):
        print(f"ERROR: {args.path} is not a directory", file=sys.stderr)
        sys.exit(2)

    # Load JSON Schema if provided
    schema = None
    if args.schema:
        if not os.path.isfile(args.schema):
            print(f"ERROR: Schema file {args.schema} not found", file=sys.stderr)
            sys.exit(2)
        try:
            with open(args.schema, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load schema file: {e}", file=sys.stderr)
            sys.exit(2)

    # Load and lint all capsules
    capsules = load_capsules(args.path)
    report = {
        "summary": {"total": 0, "errors": 0, "warnings": 0},
        "items": []
    }

    for capsule in capsules:
        if "__error__" in capsule:
            entry = {
                "file": capsule["__file__"],
                "id": None,
                "errors": [capsule["__error__"]],
                "warnings": []
            }
        else:
            errors, warnings = lint_capsule(capsule, strict=args.strict, schema=schema)
            entry = {
                "file": capsule.get("__file__"),
                "id": capsule.get("id"),
                "errors": errors,
                "warnings": warnings
            }
        report["items"].append(entry)

    # Compute summary
    for item in report["items"]:
        report["summary"]["total"] += 1
        report["summary"]["errors"] += len(item.get("errors", []))
        report["summary"]["warnings"] += len(item.get("warnings", []))

    # Output report
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        summary = report["summary"]
        print(
            f"Capsules: {summary['total']}  "
            f"errors: {summary['errors']}  "
            f"warnings: {summary['warnings']}"
        )

        for item in report["items"]:
            capsule_id = item.get("id") or "?"
            print(f"\n- {item['file']}  ({capsule_id})")

            for err in item.get("errors", []):
                print(f"  ERR: {err}")
            for warn in item.get("warnings", []):
                print(f"  WRN: {warn}")

    # Exit with error code if there are errors
    sys.exit(1 if report["summary"]["errors"] > 0 else 0)


if __name__ == "__main__":
    main()
