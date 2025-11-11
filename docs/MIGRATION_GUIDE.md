# Capsule Schema Migration Guide

Quick reference for validating and migrating Truth Capsules between schema versions.

## Prerequisites

```bash
# Install jsonschema if not already installed
pip install jsonschema

# Or update requirements
source .venv/bin/activate
pip install jsonschema
```

---

## Schema Validation

### Validate Against a JSON Schema

```bash
# Validate all capsules against a schema
make lint-schema SCHEMA=schemas/capsule.schema.v1.json

# Using the script directly
python scripts/capsule_linter.py capsules --schema schemas/capsule.schema.v1.json

# Strict mode + schema validation
python scripts/capsule_linter.py capsules --strict --schema schemas/capsule.schema.v1.json

# JSON output for automation
python scripts/capsule_linter.py capsules --schema schemas/capsule.schema.v1.json --json
```

---

## Migration Commands

### Dry Run (Preview Changes)

**Always start with a dry run to see what will change:**

```bash
# Preview migration for a directory
make migrate TARGET=capsules FROM_VERSION=v1.0 TO_VERSION=v1.1 DRY_RUN=1

# Preview migration for a single file
make migrate TARGET=capsules/llm/citation_required_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1 DRY_RUN=1

# Preview migration for bundle-referenced capsules
make migrate TARGET=bundles/macgyverisms_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1 DRY_RUN=1
```

### Live Migration

```bash
# Migrate entire directory (recursive)
make migrate-dir DIR=capsules FROM_VERSION=v1.0 TO_VERSION=v1.1

# Migrate all capsules in a specific subdomain
make migrate-dir DIR=capsules/llm FROM_VERSION=v1.0 TO_VERSION=v1.1

# Migrate capsules referenced in a bundle
make migrate-bundle BUNDLE=bundles/macgyverisms_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1

# Migrate a single capsule file
make migrate TARGET=capsules/llm/citation_required_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1
```

### Using Custom Migration Rules

```bash
# Migrate with custom transformation rules
make migrate TARGET=capsules \
  MIGRATION_RULES=schemas/v1.0_to_v1.1_rules.json

# Combined: custom rules + schema validation
python scripts/capsule_migrator.py capsules \
  --rules schemas/v1.0_to_v1.1_rules.json \
  --to-schema schemas/capsule.schema.v1.1.json
```

### Using Schema Files Directly

```bash
# Validate old schema → migrate → validate new schema
python scripts/capsule_migrator.py capsules \
  --from-schema schemas/capsule.schema.v1.0.json \
  --to-schema schemas/capsule.schema.v1.1.json \
  --rules schemas/v1.0_to_v1.1_rules.json
```

---

## Migration Rules

### Built-in Rules

The migrator includes built-in rules for common schema transitions (e.g., v1.0 → v1.1). Specify version numbers to use them:

```bash
make migrate TARGET=capsules FROM_VERSION=v1.0 TO_VERSION=v1.1
```

### Custom Rules Format

Create a JSON file with migration rules:

```json
{
  "description": "Migration from v1.0 to v1.1",
  "from_version": "v1.0",
  "to_version": "v1.1",
  "rules": [
    {
      "type": "set_default",
      "params": {
        "path": "applies_to",
        "value": ["conversation"]
      }
    },
    {
      "type": "rename_field",
      "params": {
        "old_path": "metadata.author",
        "new_path": "provenance.author"
      }
    },
    {
      "type": "transform_field",
      "params": {
        "path": "tags",
        "transform": "to_list"
      }
    },
    {
      "type": "add_field",
      "params": {
        "path": "security.sensitivity",
        "value": "low"
      }
    },
    {
      "type": "remove_field",
      "params": {
        "path": "deprecated_field"
      }
    }
  ]
}
```

### Rule Types

| Rule Type | Description | Example |
|-----------|-------------|---------|
| `set_default` | Add field if missing | Set `applies_to: ["conversation"]` |
| `add_field` | Always add field (nested paths ok) | Add `security.notes: ""` |
| `rename_field` | Move field to new path | Rename `author` → `provenance.author` |
| `transform_field` | Transform value | Convert string to list |
| `remove_field` | Delete deprecated field | Remove `old_field` |

### Transform Types

- `to_list` - Convert value to single-item list
- `to_string` - Convert value to string
- `format:{template}` - Format string (e.g., `format:{}_v1`)

---

## Common Workflows

### 1. Update Schema Version

```bash
# 1. Create new schema file
cp schemas/capsule.schema.v1.json schemas/capsule.schema.v2.json
# Edit v2 schema...

# 2. Create migration rules
cat > schemas/v1_to_v2_rules.json <<EOF
{
  "description": "Migrate v1 to v2",
  "rules": [
    {"type": "add_field", "params": {"path": "new_field", "value": "default"}}
  ]
}
EOF

# 3. Dry run migration
make migrate TARGET=capsules \
  MIGRATION_RULES=schemas/v1_to_v2_rules.json \
  DRY_RUN=1

# 4. Run live migration
make migrate TARGET=capsules \
  MIGRATION_RULES=schemas/v1_to_v2_rules.json

# 5. Validate against new schema
make lint-schema SCHEMA=schemas/capsule.schema.v2.json
```

### 2. Migrate Specific Domain

```bash
# Test on single capsule first
make migrate TARGET=capsules/llm/citation_required_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1 DRY_RUN=1

# Then migrate entire domain
make migrate-dir DIR=capsules/llm FROM_VERSION=v1.0 TO_VERSION=v1.1

# Verify
make lint-schema SCHEMA=schemas/capsule.schema.v1.1.json
```

### 3. Migrate Bundle Capsules

```bash
# See which capsules are in the bundle
head bundles/macgyverisms_v1.yaml

# Dry run
make migrate-bundle BUNDLE=bundles/macgyverisms_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1 DRY_RUN=1

# Migrate
make migrate-bundle BUNDLE=bundles/macgyverisms_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1

# Validate
make lint
```

### 4. Incremental Migration

```bash
# Start with one capsule
make migrate TARGET=capsules/llm/citation_required_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1

# Check result
cat capsules/llm/citation_required_v1.yaml

# Expand to domain
make migrate-dir DIR=capsules/llm FROM_VERSION=v1.0 TO_VERSION=v1.1

# Finally, everything
make migrate-dir DIR=capsules FROM_VERSION=v1.0 TO_VERSION=v1.1
```

---

## Safety Features

### Automatic Backups

Every migration creates timestamped backups:

```bash
# Original file
capsules/llm/citation_required_v1.yaml

# Backup (auto-created)
capsules/llm/citation_required_v1.yaml.backup.20250111_143022
```

### Restore from Backup

```bash
# Find backup
ls -lt capsules/llm/*.backup.*

# Restore
mv capsules/llm/citation_required_v1.yaml.backup.20250111_143022 \
   capsules/llm/citation_required_v1.yaml
```

### Version Control

```bash
# Before migration: commit current state
git add capsules/
git commit -m "Pre-migration snapshot"

# Run migration
make migrate-dir DIR=capsules FROM_VERSION=v1.0 TO_VERSION=v1.1

# Review changes
git diff capsules/

# Rollback if needed
git restore capsules/
```

---

## Troubleshooting

### Migration Fails

```bash
# 1. Check error message
make migrate TARGET=capsules FROM_VERSION=v1.0 TO_VERSION=v1.1

# 2. Try single file to debug
make migrate TARGET=capsules/llm/citation_required_v1.yaml \
  FROM_VERSION=v1.0 TO_VERSION=v1.1

# 3. Validate before migration
make lint

# 4. Check schema compatibility
python scripts/capsule_linter.py \
  capsules/llm/citation_required_v1.yaml \
  --schema schemas/capsule.schema.v1.0.json
```

### Schema Validation Errors

```bash
# Get detailed error report
python scripts/capsule_linter.py capsules --schema schemas/capsule.schema.v1.json --json

# Check specific capsule
python scripts/capsule_linter.py \
  capsules/llm/citation_required_v1.yaml \
  --schema schemas/capsule.schema.v1.json

# List all errors
python scripts/capsule_linter.py capsules \
  --schema schemas/capsule.schema.v1.json | grep "ERR:"
```

### Custom Rules Not Working

```bash
# Validate JSON syntax
python -m json.tool schemas/custom_rules.json

# Test rules file
python scripts/capsule_migrator.py capsules/llm/test.yaml \
  --rules schemas/custom_rules.json \
  --dry-run
```

---

## Quick Reference

```bash
# Lint with schema
make lint-schema SCHEMA=schemas/capsule.schema.v1.json

# Preview migration
make migrate TARGET=capsules FROM_VERSION=v1.0 TO_VERSION=v1.1 DRY_RUN=1

# Migrate directory
make migrate-dir DIR=capsules FROM_VERSION=v1.0 TO_VERSION=v1.1

# Migrate bundle capsules
make migrate-bundle BUNDLE=bundles/bundle.yaml FROM_VERSION=v1.0 TO_VERSION=v1.1

# Custom rules
make migrate TARGET=capsules MIGRATION_RULES=schemas/rules.json

# Validate after migration
make lint-schema SCHEMA=schemas/capsule.schema.v1.1.json
```

---

## See Also

- `schemas/migration_example.json` - Example migration rules file
- `schemas/capsule.schema.v1.json` - Current schema definition
- `scripts/capsule_linter.py --help` - Linter options
- `scripts/capsule_migrator.py --help` - Migrator options
