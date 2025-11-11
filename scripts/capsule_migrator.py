#!/usr/bin/env python3
"""
Truth Capsule Migrator - Migrate capsules between schema versions.

Supports migrating individual capsules, directories, or bundles from one schema
version to another. Can apply automated transformations and defaults for new
required fields.

Usage:
    # Migrate a single capsule
    ./capsule_migrator.py capsule.yaml --from v1.0 --to v1.1

    # Migrate all capsules in a directory
    ./capsule_migrator.py capsules/ --from v1.0 --to v1.1

    # Migrate capsules referenced in a bundle
    ./capsule_migrator.py bundles/bundle.yaml --from v1.0 --to v1.1

    # Dry run (show changes without writing)
    ./capsule_migrator.py capsules/ --from v1.0 --to v1.1 --dry-run

    # Apply custom migration rules
    ./capsule_migrator.py capsules/ --from v1.0 --to v1.1 --rules migrations/v1.0_to_v1.1.json
"""
import sys
import os
import json
import argparse
import yaml
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class MigrationRule:
    """Represents a single migration transformation."""

    def __init__(self, rule_type: str, **kwargs):
        self.rule_type = rule_type
        self.params = kwargs

    def apply(self, capsule: Dict) -> Dict:
        """Apply this rule to a capsule."""
        if self.rule_type == "add_field":
            return self._add_field(capsule)
        elif self.rule_type == "rename_field":
            return self._rename_field(capsule)
        elif self.rule_type == "remove_field":
            return self._remove_field(capsule)
        elif self.rule_type == "transform_field":
            return self._transform_field(capsule)
        elif self.rule_type == "set_default":
            return self._set_default(capsule)
        else:
            raise ValueError(f"Unknown rule type: {self.rule_type}")

    def _add_field(self, capsule: Dict) -> Dict:
        """Add a new field with a default value."""
        path = self.params["path"].split(".")
        value = self.params["value"]

        current = capsule
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        if path[-1] not in current:
            current[path[-1]] = value

        return capsule

    def _rename_field(self, capsule: Dict) -> Dict:
        """Rename a field."""
        old_path = self.params["old_path"].split(".")
        new_path = self.params["new_path"].split(".")

        # Get the value from old path
        current = capsule
        for key in old_path[:-1]:
            if key not in current:
                return capsule
            current = current[key]

        if old_path[-1] not in current:
            return capsule

        value = current.pop(old_path[-1])

        # Set at new path
        current = capsule
        for key in new_path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[new_path[-1]] = value

        return capsule

    def _remove_field(self, capsule: Dict) -> Dict:
        """Remove a field."""
        path = self.params["path"].split(".")

        current = capsule
        for key in path[:-1]:
            if key not in current:
                return capsule
            current = current[key]

        current.pop(path[-1], None)

        return capsule

    def _transform_field(self, capsule: Dict) -> Dict:
        """Transform a field value using a simple expression."""
        path = self.params["path"].split(".")
        transform = self.params["transform"]

        current = capsule
        for key in path[:-1]:
            if key not in current:
                return capsule
            current = current[key]

        if path[-1] not in current:
            return capsule

        # Apply simple transforms
        if transform == "to_list":
            if not isinstance(current[path[-1]], list):
                current[path[-1]] = [current[path[-1]]]
        elif transform == "to_string":
            current[path[-1]] = str(current[path[-1]])
        elif transform.startswith("format:"):
            # e.g., "format:{}_v1" -> "foo" becomes "foo_v1"
            fmt = transform.split(":", 1)[1]
            current[path[-1]] = fmt.format(current[path[-1]])

        return capsule

    def _set_default(self, capsule: Dict) -> Dict:
        """Set a default value if field is missing."""
        return self._add_field(capsule)


class CapsuleMigrator:
    """Handles capsule migrations between schema versions."""

    def __init__(self, old_schema: Optional[Dict] = None,
                 new_schema: Optional[Dict] = None,
                 rules: Optional[List[MigrationRule]] = None,
                 dry_run: bool = False):
        self.old_schema = old_schema
        self.new_schema = new_schema
        self.rules = rules or []
        self.dry_run = dry_run
        self.stats = {"migrated": 0, "errors": 0, "skipped": 0}

    def migrate_capsule(self, capsule: Dict) -> Dict:
        """Migrate a single capsule through all rules."""
        migrated = capsule.copy()

        # Apply each migration rule in sequence
        for rule in self.rules:
            try:
                migrated = rule.apply(migrated)
            except Exception as e:
                print(f"  ERROR applying rule {rule.rule_type}: {e}", file=sys.stderr)
                raise

        # Validate against new schema if available
        if self.new_schema and JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(migrated, self.new_schema)
            except jsonschema.ValidationError as e:
                print(f"  WARNING: Migrated capsule fails new schema validation: {e.message}",
                      file=sys.stderr)

        return migrated

    def migrate_file(self, filepath: str) -> bool:
        """Migrate a single YAML file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                capsule = yaml.safe_load(f)

            if not capsule:
                print(f"  Skipping empty file: {filepath}")
                self.stats["skipped"] += 1
                return False

            migrated = self.migrate_capsule(capsule)

            if self.dry_run:
                print(f"  [DRY RUN] Would migrate: {filepath}")
                self._print_diff(capsule, migrated)
            else:
                # Backup original
                backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(filepath, backup_path)

                # Write migrated version
                with open(filepath, "w", encoding="utf-8") as f:
                    yaml.dump(migrated, f, default_flow_style=False,
                            allow_unicode=True, sort_keys=False)

                print(f"  Migrated: {filepath}")
                print(f"  Backup:   {backup_path}")

            self.stats["migrated"] += 1
            return True

        except Exception as e:
            print(f"  ERROR migrating {filepath}: {e}", file=sys.stderr)
            self.stats["errors"] += 1
            return False

    def migrate_directory(self, dirpath: str, recursive: bool = True) -> int:
        """Migrate all YAML files in a directory."""
        count = 0
        path = Path(dirpath)

        if recursive:
            pattern = "**/*.yaml"
        else:
            pattern = "*.yaml"

        for filepath in sorted(path.glob(pattern)):
            if self.migrate_file(str(filepath)):
                count += 1

        # Also check for .yml files
        if recursive:
            pattern = "**/*.yml"
        else:
            pattern = "*.yml"

        for filepath in sorted(path.glob(pattern)):
            if self.migrate_file(str(filepath)):
                count += 1

        return count

    def migrate_bundle(self, bundle_path: str, capsules_root: str = "capsules") -> int:
        """Migrate all capsules referenced in a bundle file."""
        try:
            with open(bundle_path, "r", encoding="utf-8") as f:
                bundle = yaml.safe_load(f)

            if not bundle or "capsules" not in bundle:
                print(f"ERROR: Bundle file {bundle_path} has no 'capsules' key",
                      file=sys.stderr)
                return 0

            count = 0
            for capsule_id in bundle["capsules"]:
                # Convert capsule ID to file path
                # e.g., "macgyver.five_rails_v1" -> "capsules/macgyver/five_rails_v1.yaml"
                parts = capsule_id.split(".")
                if len(parts) >= 2:
                    domain = parts[0]
                    name = ".".join(parts[1:])
                    filepath = os.path.join(capsules_root, domain, f"{name}.yaml")

                    if os.path.isfile(filepath):
                        if self.migrate_file(filepath):
                            count += 1
                    else:
                        # Try alternative paths
                        alt_filepath = os.path.join(capsules_root, f"{name}.yaml")
                        if os.path.isfile(alt_filepath):
                            if self.migrate_file(alt_filepath):
                                count += 1
                        else:
                            print(f"  WARNING: Capsule file not found for {capsule_id}",
                                  file=sys.stderr)
                            self.stats["skipped"] += 1

            return count

        except Exception as e:
            print(f"ERROR: Failed to process bundle {bundle_path}: {e}",
                  file=sys.stderr)
            return 0

    def _print_diff(self, old: Dict, new: Dict, prefix: str = ""):
        """Print a simple diff of changes."""
        # Find added/changed fields
        for key in new:
            if key not in old:
                print(f"    + {prefix}{key}: {new[key]}")
            elif old[key] != new[key]:
                if isinstance(new[key], dict) and isinstance(old[key], dict):
                    self._print_diff(old[key], new[key], prefix=f"{prefix}{key}.")
                else:
                    print(f"    ~ {prefix}{key}: {old[key]} -> {new[key]}")

        # Find removed fields
        for key in old:
            if key not in new:
                print(f"    - {prefix}{key}")


def load_migration_rules(rules_path: str) -> List[MigrationRule]:
    """Load migration rules from a JSON file."""
    with open(rules_path, "r", encoding="utf-8") as f:
        rules_data = json.load(f)

    rules = []
    for rule_data in rules_data.get("rules", []):
        rule = MigrationRule(rule_data["type"], **rule_data.get("params", {}))
        rules.append(rule)

    return rules


def get_builtin_rules(from_version: str, to_version: str) -> List[MigrationRule]:
    """Get built-in migration rules for common schema transitions."""
    rules = []

    # Example: v1.0 to v1.1 migration
    if from_version == "v1.0" and to_version == "v1.1":
        # Add new required fields with sensible defaults
        rules.extend([
            MigrationRule("set_default",
                         path="applies_to",
                         value=["conversation"]),
            MigrationRule("set_default",
                         path="security.sensitivity",
                         value="low"),
            MigrationRule("set_default",
                         path="provenance.review.reviewers",
                         value=[]),
            MigrationRule("set_default",
                         path="provenance.review.last_reviewed",
                         value=None),
            MigrationRule("set_default",
                         path="provenance.signing.method",
                         value="none"),
            MigrationRule("set_default",
                         path="provenance.signing.key_id",
                         value=None),
            MigrationRule("set_default",
                         path="provenance.signing.pubkey",
                         value=None),
            MigrationRule("set_default",
                         path="provenance.signing.digest",
                         value=None),
            MigrationRule("set_default",
                         path="provenance.signing.signature",
                         value=None),
        ])

    return rules


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "target",
        help="Path to capsule file, directory, or bundle to migrate"
    )
    ap.add_argument(
        "--from-version",
        type=str,
        help="Source schema version (e.g., v1.0)"
    )
    ap.add_argument(
        "--to-version",
        type=str,
        help="Target schema version (e.g., v1.1)"
    )
    ap.add_argument(
        "--from-schema",
        type=str,
        help="Path to old schema JSON file"
    )
    ap.add_argument(
        "--to-schema",
        type=str,
        help="Path to new schema JSON file"
    )
    ap.add_argument(
        "--rules",
        type=str,
        help="Path to custom migration rules JSON file"
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing files"
    )
    ap.add_argument(
        "--capsules-root",
        type=str,
        default="capsules",
        help="Root directory for capsule files (when migrating bundles)"
    )
    args = ap.parse_args()

    # Load schemas
    old_schema = None
    new_schema = None

    if args.from_schema:
        with open(args.from_schema, "r", encoding="utf-8") as f:
            old_schema = json.load(f)

    if args.to_schema:
        with open(args.to_schema, "r", encoding="utf-8") as f:
            new_schema = json.load(f)

    # Load migration rules
    if args.rules:
        rules = load_migration_rules(args.rules)
        print(f"Loaded {len(rules)} custom migration rules from {args.rules}")
    elif args.from_version and args.to_version:
        rules = get_builtin_rules(args.from_version, args.to_version)
        print(f"Using {len(rules)} built-in migration rules for {args.from_version} -> {args.to_version}")
    else:
        print("WARNING: No migration rules specified. No transformations will be applied.",
              file=sys.stderr)
        print("         Specify --rules, or use --from-version and --to-version for built-in rules.",
              file=sys.stderr)
        rules = []

    # Create migrator
    migrator = CapsuleMigrator(
        old_schema=old_schema,
        new_schema=new_schema,
        rules=rules,
        dry_run=args.dry_run
    )

    # Determine target type and migrate
    target = args.target

    if not os.path.exists(target):
        print(f"ERROR: Target {target} does not exist", file=sys.stderr)
        sys.exit(2)

    print(f"\nMigrating: {target}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    if os.path.isfile(target):
        if target.endswith((".yaml", ".yml")):
            # Check if it's a bundle or capsule
            with open(target, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data and "capsules" in data and "name" in data:
                # It's a bundle
                print("Detected bundle file")
                count = migrator.migrate_bundle(target, args.capsules_root)
            else:
                # It's a capsule
                print("Detected capsule file")
                migrator.migrate_file(target)
                count = 1
        else:
            print(f"ERROR: Target file must be .yaml or .yml", file=sys.stderr)
            sys.exit(2)
    elif os.path.isdir(target):
        print("Detected directory")
        count = migrator.migrate_directory(target, recursive=True)
    else:
        print(f"ERROR: Target {target} is not a file or directory", file=sys.stderr)
        sys.exit(2)

    # Print summary
    print()
    print("=" * 60)
    print(f"Migration {'preview' if args.dry_run else 'complete'}:")
    print(f"  Migrated: {migrator.stats['migrated']}")
    print(f"  Errors:   {migrator.stats['errors']}")
    print(f"  Skipped:  {migrator.stats['skipped']}")

    if migrator.stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
