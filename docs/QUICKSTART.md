# Truth Capsules - Quickstart Guide

Get started with Truth Capsules in 5 minutes. This guide covers installation, basic usage, and common workflows.

---

## Installation

Truth Capsules requires Python 3.11+ and PyYAML.

```bash
# Clone the repository
git clone <repository-url>
cd truth-capsules-v1

# Install dependencies
pip install pyyaml

# Optional: For bundle schema validation
pip install jsonschema

# Verify installation
python scripts/capsule_linter.py capsules
```

**Expected output:**
```
Capsules: 24  errors: 0  warnings: 0
```

---

## Basic Usage

### 1. List Available Profiles

```bash
python scripts/compose_capsules_cli.py --root . --list-profiles
```

**Output:**
```
Available Profiles:

  profile.conversational_guidance_v1
    Title: Conversational Guidance
    Aliases: conversational

  profile.ci_deterministic_gate_v1
    Title: CI Gate - Deterministic
    Aliases: ci_det
  ...
```

### 2. List Available Bundles

```bash
python scripts/compose_capsules_cli.py --root . --list-bundles
```

**Output:**
```
Available Bundles:

  conversation_red_team_baseline_v1
    Capsules: 10
    Applies to: conversation, code_assistant
  ...
```

### 3. Compose Your First Prompt

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out prompt.txt
```

**What this does:**
- Loads the `conversational` profile
- Includes all 10 capsules from the `conversation_red_team_baseline_v1` bundle
- Writes the composed prompt to `prompt.txt`

### 4. View the Generated Prompt

```bash
cat prompt.txt
```

**Output structure:**
```
SYSTEM: Profile=Conversational Guidance
POLICY: Cite or abstain; follow Plan→Verify→Answer; ask ONE crisp follow-up if required.
FORMAT: Natural language (no JSON required).

SYSTEM: Capsule Rules (Selected)
BEGIN CAPSULE id=llm.red_team_assessment_v1 version=1.0.0 domain=llm
TITLE: Red-team assessment
STATEMENT: Before finalizing, probe weak points in reasoning...
...
```

---

## Common Workflows

### Generate Prompt with Manifest

The manifest is a lockfile that records exactly which capsules and versions were used:

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out prompt.txt \
  --manifest manifest.json
```

**Manifest contains:**
- Profile ID and version
- Bundle names and versions
- Capsule IDs with SHA256 hashes
- Generation timestamp
- Composer version

**Example manifest.json:**
```json
{
  "profile": "profile.conversational_guidance_v1",
  "profile_version": "1.0.0",
  "bundles": [{"name": "conversation_red_team_baseline_v1", "version": "1.0.0"}],
  "capsules": [
    {"id": "llm.red_team_assessment_v1", "file": "./capsules/...", "sha256": "..."}
  ],
  "composer_version": "1.1.0",
  "generated_at": "2025-11-08T..."
}
```

---

### Compact Mode (No Pedagogy)

Exclude Socratic prompts and aphorisms for shorter prompts:

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --compact \
  --out compact_prompt.txt
```

**Use compact mode when:**
- Prompt token limits are tight
- Pedagogy isn't needed for the task
- Machine-parsing is the primary use case
- CI/automated workflows

---

### Control Table (Priority Summary)

**New in v1.1:** Add a capsule priority table to help LLMs understand rule precedence:

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --control-table \
  --out prompt_with_table.txt
```

**Control table example:**
```
SYSTEM: Capsule Control Table (compiled)
| Pri | Capsule ID                           | Directive                  |
|-----|--------------------------------------|----------------------------|
|   1 | llm.safety_refusal_guard_v1          | FORBID unsafe outputs      |
|   2 | llm.pii_redaction_guard_v1           | FORBID raw PII             |
|   3 | llm.citation_required_v1             | MUST cite or abstain       |
|   4 | llm.plan_verify_answer_v1            | MUST Plan→Verify→Answer    |
```

**When to use control tables:**
- Conversational contexts (helps LLMs prioritize)
- Complex bundles with many capsules
- When rule conflicts are possible

---

### Mix Bundles and Individual Capsules

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --capsule llm.pii_redaction_guard_v1 \
  --capsule llm.judge_answer_quality_v1 \
  --out extended_prompt.txt
```

**This composes:**
- All capsules from `conversation_red_team_baseline_v1` bundle
- Plus `llm.pii_redaction_guard_v1`
- Plus `llm.judge_answer_quality_v1`

**De-duplication:** Capsules are automatically de-duplicated by ID.

---

### Validate Capsules Before Composing

```bash
# Lint all capsules
python scripts/capsule_linter.py capsules

# Strict mode (enforce approved status)
python scripts/capsule_linter.py capsules --strict

# JSON output for CI
python scripts/capsule_linter.py capsules --json > lint_results.json
```

**Linter checks:**
- Required fields (id, version, domain, statement)
- ID format (`domain.name_vN`)
- Provenance structure
- Unicode escape sequences
- Domain/path consistency

---

### Validate Bundles

**New in v1.1:** Validate bundle schema and referenced capsules:

```bash
# Validate all bundles
python scripts/bundle_linter.py bundles --root .

# Strict mode (schema errors are fatal)
python scripts/bundle_linter.py bundles --root . --strict

# JSON output
python scripts/bundle_linter.py bundles --root . --json
```

**Bundle linter checks:**
- Schema compliance (v1.1 fields)
- Capsule ID existence
- Exclude/include conflicts
- Version format
- Priority override ranges

---

## Advanced Features (v1.1)

### Bundle with Excludes

Create a bundle that removes specific capsules:

```yaml
# bundles/my_custom_bundle.yaml
name: my_custom_bundle_v1
version: 1.0.0
capsules:
  - llm.safety_refusal_guard_v1
  - llm.citation_required_v1
  - llm.red_team_assessment_v1
excludes:
  - llm.red_team_assessment_v1  # Remove this one
```

**Result:** Only safety and citation capsules are included.

---

### Bundle with Priority Overrides

Override default capsule priorities for control tables:

```yaml
# bundles/priority_test_bundle.yaml
name: priority_test_bundle_v1
version: 1.0.0
capsules:
  - llm.safety_refusal_guard_v1    # Default priority: 1
  - llm.citation_required_v1       # Default priority: 3
priority_overrides:
  llm.citation_required_v1: 1      # Make citations highest priority
  llm.safety_refusal_guard_v1: 10  # Lower safety priority
```

---

### Bundle with Explicit Ordering

Control the order capsules appear in the prompt:

```yaml
# bundles/ordered_bundle.yaml
name: ordered_bundle_v1
version: 1.0.0
capsules:
  - llm.safety_refusal_guard_v1
  - llm.citation_required_v1
  - llm.plan_verify_answer_v1
order:
  - llm.plan_verify_answer_v1     # First
  - llm.safety_refusal_guard_v1   # Second
  # citation_required will be third (not in order list)
```

---

### Profile with Projection

**New in v1.1:** Control which capsule fields are rendered:

```yaml
# profiles/my_profile.yaml
kind: profile
id: profile.my_custom_v1
title: My Custom Profile
version: 1.0.0

response:
  format: natural
  projection:
    include:
      - title
      - statement
      - assumptions[:3]           # Only 3 assumptions
      - pedagogy.socratic[:2]     # Only 2 Socratic prompts
      - pedagogy.aphorisms[:1]    # Only 1 aphorism
```

**Result:** Each capsule is rendered with limited fields, reducing prompt size.

---

## CLI Reference

### Basic Flags

```bash
--root <path>              # Path to truth-capsules root directory (required)
--profile <name>           # Profile ID or alias (required for composition)
--bundle <name>            # Bundle name (can be repeated)
--capsule <id>             # Capsule ID or file path (can be repeated)
--out <path>               # Output prompt file path (required for composition)
--manifest <path>          # Output manifest JSON (optional)
```

### v1.1 Flags

```bash
--compact                  # Exclude pedagogy fields
--control-table            # Include capsule priority table
--projection <name>        # Override profile's projection (future feature)
```

### Utility Flags

```bash
--list-profiles            # List all available profiles
--list-bundles             # List all available bundles
```

---

## File Structure

```
truth-capsules-v1/
├── capsules/              # 24 capsule YAML files
│   ├── llm.*.yaml
│   ├── business.*.yaml
│   ├── ops.*.yaml
│   └── pedagogy.*.yaml
├── bundles/               # 7 bundle YAML files
│   ├── conversation_red_team_baseline_v1.yaml
│   ├── pr_review_minibundle_v1.yaml
│   └── ...
├── profiles/              # 7 profile YAML files
│   ├── conversational.yaml
│   ├── ci_det.yaml
│   └── ...
├── schemas/               # JSON schemas
│   └── bundle.schema.v1.json
├── scripts/               # CLI tools
│   ├── compose_capsules_cli.py
│   ├── capsule_linter.py
│   ├── bundle_linter.py
│   └── ...
└── docs/                  # Documentation
    ├── QUICKSTART.md (this file)
    ├── BUNDLES_SCHEMA_v1.md
    ├── PROFILES_REFERENCE.md
    └── ...
```

---

## Examples by Use Case

### 1. Conversational AI Assistant

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out chatbot_prompt.txt \
  --manifest chatbot_manifest.json
```

**Use the generated `chatbot_prompt.txt` as your system prompt.**

---

### 2. CI Pipeline Gate

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile ci_det \
  --bundle ci_nonllm_baseline_v1 \
  --compact \
  --out ci_gate_prompt.txt
```

**Integrate into CI:**
```yaml
# .github/workflows/lint.yml
- name: Generate CI prompt
  run: python scripts/compose_capsules_cli.py --root . --profile ci_det --bundle ci_nonllm_baseline_v1 --compact --out ci_prompt.txt

- name: Run linter with capsule rules
  run: python ci_linter.py --rules ci_prompt.txt
```

---

### 3. Code Review Assistant

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile code_patch \
  --bundle pr_review_minibundle_v1 \
  --out pr_review_prompt.txt
```

**Use with GitHub Actions:**
```yaml
# .github/workflows/pr-review.yml
- name: Generate PR review prompt
  run: python scripts/compose_capsules_cli.py --root . --profile code_patch --bundle pr_review_minibundle_v1 --out pr_prompt.txt

- name: Review PR with LLM
  run: python scripts/llm_pr_reviewer.py --prompt pr_prompt.txt --pr ${{ github.event.pull_request.number }}
```

---

## Troubleshooting

### Profile not found

**Error:**
```
ERROR: Profile not found: my_profile
```

**Solution:**
```bash
# List available profiles
python scripts/compose_capsules_cli.py --root . --list-profiles

# Use exact ID or alias
python scripts/compose_capsules_cli.py --root . --profile conversational ...
```

---

### Bundle not found

**Error:**
```
WARNING: Bundle not found: my_bundle
```

**Solution:**
```bash
# List available bundles
python scripts/compose_capsules_cli.py --root . --list-bundles

# Check bundle file exists
ls bundles/my_bundle.yaml
```

---

### Capsule not found

**Error:**
```
WARNING: Capsule not found: llm.missing_v1
```

**Solution:**
```bash
# List all capsules
python scripts/capsule_linter.py capsules

# Check ID spelling
grep "id:" capsules/*.yaml
```

---

### No capsules selected

**Error:**
```
ERROR: No capsules selected. Specify at least one --bundle or --capsule
```

**Solution:**
Provide at least one bundle or capsule:
```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out prompt.txt
```

---

## Next Steps

- **Read [Bundle Schema v1.1](BUNDLES_SCHEMA_v1.md)** - Learn about advanced bundle features
- **Read [Profile Reference](PROFILES_REFERENCE.md)** - Understand projections and profiles
- **Read [Capsule Schema](CAPSULE_SCHEMA_v1.md)** - Create your own capsules
- **Explore [Use Cases](USE_CASES.md)** - See real-world examples

---

## Getting Help

- **Linter errors:** Run with `--json` for detailed error messages
- **Schema questions:** Check `schemas/bundle.schema.v1.json`
- **CLI help:** Run any script with `--help` or `-h`
- **Examples:** See `examples/` directory for sample outputs

---

**Happy composing!** 🎉
