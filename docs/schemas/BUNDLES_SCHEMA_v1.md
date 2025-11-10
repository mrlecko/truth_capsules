# Bundle Schema v1.1 Reference

**Version:** 1.1.0
**Schema File:** `schemas/bundle.schema.v1.json`
**Effective:** 2025-11-08

---

## Overview

Bundles are collections of capsules grouped for specific contexts (conversation, CI, code assistant, etc.). Bundle Schema v1.1 introduces powerful composition features for advanced use cases.

**What's New in v1.1:**
- **`version`** - Semantic versioning for bundles
- **`excludes`** - Remove specific capsules from the bundle
- **`priority_overrides`** - Override default capsule priorities for control tables
- **`projection`** - Override profile's default projection
- **`order`** - Explicit ordering of capsules
- **`tags`** - Metadata for categorization
- **`notes`** - Human-readable context

---

## Schema Fields

### Required Fields

#### `name` (string, required)
Unique bundle identifier following the pattern: `<name>_v<N>`

**Example:**
```yaml
name: conversation_red_team_baseline_v1
```

**Pattern:** `^[a-z0-9_]+_v\d+$`

---

#### `capsules` (array, required)
List of capsule IDs to include in this bundle.

**Example:**
```yaml
capsules:
  - llm.citation_required_v1
  - llm.plan_verify_answer_v1
  - llm.safety_refusal_guard_v1
```

**Minimum:** 1 capsule required

---

### Recommended Fields

#### `version` (string, recommended)
Semantic version number (MAJOR.MINOR.PATCH).

**Example:**
```yaml
version: 1.0.0
```

**Pattern:** `^\d+\.\d+\.\d+$`
**Default:** `1.0.0` if not specified

**When to increment:**
- **MAJOR** - Breaking changes (incompatible capsule updates)
- **MINOR** - New capsules added or significant changes
- **PATCH** - Bug fixes, documentation updates

---

#### `applies_to` (array, recommended)
Contexts where this bundle is applicable.

**Example:**
```yaml
applies_to:
  - conversation
  - code_assistant
```

**Valid values:**
- `conversation` - Chat/Q&A contexts
- `code_assistant` - IDE integrations
- `ci` - Continuous integration pipelines
- `assistant` - General AI assistants
- `tool_runner` - Function-calling contexts

---

### v1.1 Features (Optional)

#### `excludes` (array, optional)
Remove specific capsules from the bundle. Useful for creating derived bundles.

**Example:**
```yaml
capsules:
  - llm.red_team_assessment_v1
  - llm.safety_refusal_guard_v1
  - llm.citation_required_v1
excludes:
  - llm.red_team_assessment_v1  # Exclude this one
```

**Use cases:**
- Create "lite" versions of bundles
- Remove incompatible capsules for specific contexts
- Override parent bundle selections

**Note:** If a capsule is in both `capsules` and `excludes`, it will be excluded.

---

#### `priority_overrides` (object, optional)
Override default capsule priorities for control table generation.

**Example:**
```yaml
priority_overrides:
  llm.citation_required_v1: 1      # Highest priority (default was 3)
  llm.plan_verify_answer_v1: 10    # Lower priority (default was 4)
```

**Values:**
- Range: 1-100 (lower = higher priority)
- Type: Integer

**Default priorities:**
- `llm.safety_refusal_guard_v1`: 1
- `llm.pii_redaction_guard_v1`: 2
- `llm.citation_required_v1`: 3
- `llm.plan_verify_answer_v1`: 4
- All others: 5

**Use cases:**
- Emphasize specific capsules in certain contexts
- Reorder control table based on business requirements
- Test different priority configurations

---

#### `order` (array, optional)
Explicit ordering of capsule IDs. Capsules not listed will append in original order.

**Example:**
```yaml
capsules:
  - llm.safety_refusal_guard_v1
  - llm.citation_required_v1
  - llm.plan_verify_answer_v1
order:
  - llm.plan_verify_answer_v1     # First
  - llm.safety_refusal_guard_v1   # Second
  # citation_required will be third (not in order list, so appends)
```

**Use cases:**
- Ensure critical capsules appear first
- Optimize for LLM attention (important rules early)
- Create consistent ordering across environments

---

#### `projection` (string, optional)
Override the profile's default projection.

**Example:**
```yaml
projection: ci  # Use CI projection instead of profile default
```

**Valid values:**
- `default` - Use profile's projection
- `ci` - Minimal output for CI contexts
- `compact` - Exclude pedagogy
- `full` - All fields included
- Custom projection names (if defined)

**Use cases:**
- Bundle-specific rendering preferences
- Override verbose profile defaults for specific bundles
- A/B test different projection configurations

---

#### `tags` (array, optional)
Metadata tags for categorization and search.

**Example:**
```yaml
tags:
  - security
  - baseline
  - production
```

**Use cases:**
- Filter bundles in tooling
- Categorize bundles by purpose
- Enable search and discovery

---

#### `notes` (string, optional)
Human-readable context, usage notes, or warnings.

**Example:**
```yaml
notes: |
  This bundle is for red-team testing in conversational contexts.
  Use with caution in production environments.

  Last updated: 2025-11-08
  Owner: Security Team
```

**Use cases:**
- Document bundle purpose
- Provide usage warnings
- Track ownership and updates

---

### Legacy Fields (Compatibility)

#### `modes` (array, optional)
Operational modes. Used in some workflows but not part of core schema.

**Example:**
```yaml
modes:
  - baseline
  - red_team
```

---

#### `env` (object, optional)
Environment variable hints. Used for documentation purposes.

**Example:**
```yaml
env:
  OPENAI_API_KEY: "Required for LLM calls"
```

---

#### `secrets` (array, optional)
List of secret keys required by capsules in this bundle.

**Example:**
```yaml
secrets:
  - ANTHROPIC_API_KEY
  - DATABASE_URL
```

---

## Complete Example

```yaml
# Bundle demonstrating all v1.1 features
name: advanced_bundle_v1
version: 1.1.0

applies_to:
  - conversation
  - code_assistant

capsules:
  - llm.safety_refusal_guard_v1
  - llm.pii_redaction_guard_v1
  - llm.citation_required_v1
  - llm.plan_verify_answer_v1
  - llm.red_team_assessment_v1

# v1.1 features
excludes:
  - llm.red_team_assessment_v1

priority_overrides:
  llm.citation_required_v1: 1
  llm.plan_verify_answer_v1: 10

order:
  - llm.safety_refusal_guard_v1
  - llm.citation_required_v1
  - llm.plan_verify_answer_v1

projection: ci

tags:
  - security
  - baseline
  - v1.1

notes: |
  Advanced bundle showcasing all v1.1 features.

  Features demonstrated:
  - Excludes: Removes red_team_assessment
  - Priority overrides: Citations prioritized
  - Order: Explicit capsule ordering
  - Projection: CI-optimized rendering

  Maintained by: Platform Team
  Last reviewed: 2025-11-08

# Legacy fields
modes:
  - baseline
env: {}
secrets: []
```

---

## Validation

Bundles are validated using `scripts/bundle_linter.py`:

```bash
# Validate all bundles
python scripts/bundle_linter.py bundles --root .

# Strict mode (enforce schema compliance)
python scripts/bundle_linter.py bundles --root . --strict

# JSON output
python scripts/bundle_linter.py bundles --root . --json
```

**Validation checks:**
- Schema compliance (`schemas/bundle.schema.v1.json`)
- Capsule ID existence
- Conflicts (capsules in both `capsules` and `excludes`)
- Version format
- Priority override ranges

---

## Composition Behavior

### Excludes Processing
1. Load all capsules from `capsules` list
2. Remove any capsule IDs listed in `excludes`
3. Continue with remaining capsules

### Order Processing
1. Start with empty ordered list
2. For each ID in `order`, add corresponding capsule
3. Append remaining capsules (not in `order`) in original order

### Priority Overrides
1. Use default priorities for known capsules
2. Apply bundle-specific `priority_overrides`
3. Generate control table with adjusted priorities

---

## Migration Guide

### Upgrading to v1.1

**Old bundle (v1.0):**
```yaml
name: my_bundle_v1
applies_to: [conversation]
capsules:
  - llm.citation_required_v1
  - llm.plan_verify_answer_v1
```

**New bundle (v1.1):**
```yaml
name: my_bundle_v1
version: 1.0.0              # Add version
applies_to: [conversation]
capsules:
  - llm.citation_required_v1
  - llm.plan_verify_answer_v1

# Optional v1.1 features
tags: [baseline]
notes: "Baseline conversation bundle"
```

**Backward compatibility:** v1.0 bundles work without changes. The `version` field defaults to `1.0.0`.

---

## Best Practices

### 1. Always Specify Version
```yaml
version: 1.0.0  # Enables proper versioning and tracking
```

### 2. Use Excludes Sparingly
Excludes can make bundles harder to understand. Prefer creating separate bundles.

**Bad:**
```yaml
name: bundle_without_redteam_v1
capsules: [a, b, c, d, e]
excludes: [c, d]  # Confusing
```

**Good:**
```yaml
name: bundle_core_v1
capsules: [a, b, e]  # Clear intent
```

### 3. Document Priority Overrides
```yaml
priority_overrides:
  llm.citation_required_v1: 1
notes: |
  Citations prioritized due to compliance requirements.
  Priority override approved by Legal team (2025-11-08).
```

### 4. Use Tags Consistently
```yaml
tags:
  - baseline      # Indicates core bundle
  - security      # Domain/purpose
  - production    # Deployment environment
```

### 5. Keep Order Lists Minimal
Only specify `order` for capsules where sequence matters:

```yaml
order:
  - llm.safety_refusal_guard_v1  # Must be first
  # Other capsules can be in any order
```

---

## See Also

- [Profile Reference](PROFILES_REFERENCE.md) - Profile configuration including projections
- [Quickstart Guide](QUICKSTART.md) - Using bundles with the composer
- [Capsule Schema](CAPSULE_SCHEMA_v1.md) - Capsule format specification
- [Bundle Schema JSON](../schemas/bundle.schema.v1.json) - Machine-readable schema
