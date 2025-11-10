# Capsule Schema v1

A capsule is a YAML file with these required fields:

## Minimal Example

```yaml
id: example.capsule_v1          # REQUIRED: unique ID ending with _vN
version: 1.0.0                  # REQUIRED: semantic version
domain: pr_review               # REQUIRED: domain tag
statement: "Normative statement of rule/method"  # REQUIRED: what this capsule enforces
```

## Complete Example

```yaml
id: example.capsule_v1
version: 1.0.0
domain: pr_review
title: Human-readable title   # OPTIONAL but recommended

statement: "Normative statement describing rule, method, or requirement"

assumptions:                   # OPTIONAL: list of context assumptions
  - "CI runs on every commit"
  - "Reviewers understand the domain"

pedagogy:                      # OPTIONAL: teaching prompts
  - kind: Socratic             # Socratic | Aphorism
    text: "What changed and why?"
  - kind: Aphorism
    text: "One failing test beats ten opinions"

witnesses:                     # OPTIONAL: executable verification code
  - name: five_step_gate       # REQUIRED: witness identifier
    language: python           # REQUIRED: python | node | bash | shell
    entrypoint: python3        # OPTIONAL: command to run (default: language name)
    args: []                   # OPTIONAL: command-line arguments
    env:                       # OPTIONAL: environment variables (explicit allowlist)
      PS_REPORT: "artifacts/examples/problem_solving_ok.json"
    workdir: "."               # OPTIONAL: working directory
    timeout_ms: 5000           # OPTIONAL: execution timeout in milliseconds
    memory_mb: 128             # OPTIONAL: memory limit (not enforced by default)
    net: false                 # OPTIONAL: network access (not enforced by default)
    fs_mode: ro                # OPTIONAL: filesystem mode (ro|rw, not enforced by default)
    stdin: ""                  # OPTIONAL: input to pass via stdin
    code: |-
      import json, os

      p = os.getenv("PS_REPORT", "artifacts/examples/problem_solving_ok.json")
      r = json.load(open(p))

      need = ["objective", "assumptions", "plan", "evidence", "summary"]
      missing = [k for k in need if not r.get(k)]

      assert not missing, f"Missing fields: {missing}"
      assert isinstance(r["assumptions"], list) and len(r["assumptions"]) >= 1

provenance:                    # OPTIONAL but strongly recommended
  schema: provenance.v1
  author: Your Name
  org: Your Org
  license: MIT
  source_url: https://example.com/capsules
  created: 2025-11-07T00:00:00Z
  updated: 2025-11-07T00:00:00Z
  review:
    status: draft            # draft | in_review | approved | deprecated
    reviewers: []
    last_reviewed: null
  signing:
    method: ed25519
    key_id: null
    pubkey: null
    digest: "<sha256 of core content>"
    signature: null

applies_to:                    # OPTIONAL: context hints
  - conversation
  - code_assistant
  - ci

dependencies: []               # OPTIONAL: capsule dependencies (future)
incompatible_with: []          # OPTIONAL: exclusion list (future)

security:                      # OPTIONAL: sensitivity metadata
  sensitivity: low             # low | medium | high
  notes: ""
```

---

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier matching pattern `domain.name_vN` or `domain.name_vN_suffix` |
| `version` | string | Semantic version (e.g., `1.0.0`, `2.1.3`) |
| `domain` | string | Domain tag (e.g., `llm`, `business`, `ops`, `pedagogy`) |
| `statement` | string | Core normative statement of the rule, method, or requirement |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Human-readable title (recommended) |
| `assumptions` | list[string] | Context assumptions that must be true for capsule to apply |
| `pedagogy` | list[object] | Teaching prompts (Socratic questions + aphorisms) |
| `witnesses` | list[object] | Executable verification code (see Witnesses section) |
| `provenance` | object | Authorship, licensing, review status, and signing metadata |
| `applies_to` | list[string] | Context hints (`conversation`, `code_assistant`, `ci`) |
| `dependencies` | list[string] | IDs of capsules this depends on (not yet implemented) |
| `incompatible_with` | list[string] | IDs of capsules incompatible with this one (not yet implemented) |
| `security` | object | Sensitivity classification and notes |

---

## Pedagogy Structure

```yaml
pedagogy:
  - kind: Socratic           # Open-ended question that reveals assumptions
    text: "What evidence supports this claim?"

  - kind: Aphorism           # Memorable compression of wisdom
    text: "No citation, no claim"
```

**Guidelines:**
- ≤5 Socratic prompts per capsule
- ≤5 aphorisms per capsule
- Socratic questions should be open-ended (not yes/no)
- Aphorisms should be 3-7 words and actionable

---

## Witnesses Structure

Witnesses are **executable code artifacts** that verify adherence to a capsule's rules. They are treated as **data** (not executable YAML tags) and run in a controlled environment that the user manages.

### Minimal Witness

```yaml
witnesses:
  - name: my_check
    language: python
    code: |-
      # Your validation code here
      assert condition, "Error message"
```

### Complete Witness

```yaml
witnesses:
  - name: decision_log_gate
    language: python           # REQUIRED: python | node | bash | shell
    entrypoint: python3        # OPTIONAL: executable name (default: language)
    args: []                   # OPTIONAL: additional args to entrypoint
    env:                       # OPTIONAL: explicit environment allowlist
      DEC_REPORT: "artifacts/examples/decision_log.json"
    workdir: "."               # OPTIONAL: working directory
    timeout_ms: 5000           # OPTIONAL: max execution time (milliseconds)
    memory_mb: 128             # OPTIONAL: memory limit (advisory)
    net: false                 # OPTIONAL: network access flag (advisory)
    fs_mode: ro                # OPTIONAL: filesystem mode (ro|rw, advisory)
    stdin: ""                  # OPTIONAL: data to pass via stdin
    code: |-
      import json, os

      path = os.getenv("DEC_REPORT", "artifacts/examples/decision_log.json")
      data = json.load(open(path))

      assert data.get("decision"), "Missing decision field"
      assert len(data.get("options", [])) >= 3, "Need >= 3 options"
```

### Witness Field Reference

| Field | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `name` | ✅ | string | - | Unique identifier for this witness |
| `language` | ✅ | string | - | Execution language: `python`, `node`, `bash`, `shell` |
| `code` | ✅ | string | - | Executable code (use YAML block literal `\|-`) |
| `entrypoint` | ❌ | string | `{language}` | Command to execute (e.g., `python3`, `node`, `bash`) |
| `args` | ❌ | list[string] | `[]` | Additional command-line arguments |
| `env` | ❌ | dict | `{}` | Environment variables (explicit allowlist) |
| `workdir` | ❌ | string | `"."` | Working directory for execution |
| `timeout_ms` | ❌ | integer | `5000` | Max execution time in milliseconds |
| `memory_mb` | ❌ | integer | `128` | Memory limit (advisory, not enforced by default) |
| `net` | ❌ | boolean | `false` | Network access (advisory, not enforced by default) |
| `fs_mode` | ❌ | string | `"ro"` | Filesystem mode: `ro` (read-only) or `rw` (read-write) |
| `stdin` | ❌ | string | `""` | Input to pass via stdin |

### YAML Formatting for Code Blocks

**✅ Recommended: Block Literal (`|-`)**

```yaml
code: |-
  import json
  data = json.load(open("file.json"))
  assert data["key"] == "value"
```

**Why?**
- Preserves newlines exactly
- No escaping hassles
- Colons, hashes, dashes inside code can't confuse parser
- `|-` strips final trailing newline for stable digests

**❌ Avoid: Multi-line Quoted Strings**

```yaml
code: '
  import json
  data = json.load(open("file.json"))
'
```

**Why not?**
- Requires escaping quotes and special characters
- Easy to make mistakes with newlines
- Hard to read and maintain

### Security Considerations

**⚠️ IMPORTANT: Witnesses execute arbitrary code. Users are responsible for safe execution.**

Recommended practices:
1. **Parse YAML safely**: Use `yaml.safe_load()` (Python) or default loader (Node)
2. **Sandbox execution**: Run in containers, VMs, or isolated processes
3. **Limit resources**: Enforce `timeout_ms`, `memory_mb`, CPU limits
4. **Restrict network**: Disable network access (`net: false`)
5. **Read-only filesystem**: Use `fs_mode: ro` where possible
6. **Explicit environment**: Only pass required env vars via `env:` allowlist
7. **Capture output**: Collect stdout/stderr/exit code; don't let code self-certify
8. **Drop privileges**: Run as non-root user with minimal permissions

**See `WITNESSES_GUIDE.md` for detailed security guidance and execution examples.**

---

## Provenance Structure

```yaml
provenance:
  schema: provenance.v1        # Schema version
  author: John Doe             # Author name
  org: Acme Corp               # Organization
  license: MIT                 # License identifier
  source_url: https://...      # Source repository or documentation
  created: 2025-11-07T00:00:00Z
  updated: 2025-11-07T00:00:00Z

  review:
    status: draft              # draft | in_review | approved | deprecated
    reviewers: []              # List of reviewer names
    last_reviewed: null        # ISO datetime of last review

  signing:
    method: ed25519            # Signing method
    key_id: prod-key-v1        # Key identifier
    pubkey: "base64..."        # Public key (base64)
    digest: "sha256..."        # SHA256 of canonical JSON
    signature: "base64..."     # Ed25519 signature (base64)
```

### Core-Content Digest

The digest covers these fields only:
- `id`, `version`, `domain`, `title`, `statement`
- `assumptions` (full list)
- `pedagogy` (only `kind` and `text` fields, excluding metadata)

See `capsule_sign.py` and `capsule_verify.py` for signing/verification tools.

---

## Style Guide

### General
- **Keep `statement` concise**: 1-3 sentences maximum
- **Use `assumptions` for scope**: Document context dependencies
- **Prefer verb-first titles**: "PR Review - Diff First", not "First thing to read in PR is diff"
- **Use UTF-8 characters**: Write `≥` not `\u2265`, `→` not `\u2192`

### Pedagogy
- **Socratic prompts**: Open-ended, reveal assumptions, scaffold learning
- **Aphorisms**: 3-7 words, memorable, actionable
- **Limit quantity**: ≤5 Socratic prompts, ≤5 aphorisms per capsule

### Witnesses
- **Use block literals**: `code: |-` for all code blocks
- **Explicit environment**: Only pass needed variables via `env:`
- **Set timeouts**: Use `timeout_ms` to prevent hangs
- **Document purpose**: Name witnesses descriptively (`rollback_present`, not `check1`)
- **Keep focused**: One witness checks one thing; compose multiple if needed

### Versioning
- **Immutable capsules**: Don't edit in place; create new version for breaking changes
- **Version suffix**: `_v1`, `_v2`, etc. in the `id` field
- **Semantic versioning**: Use `version` field for minor updates within same `_vN`

---

## Validation

Use `capsule_linter.py` to validate capsules:

```bash
# Normal mode: schema validation
python capsule_linter.py truth-capsules-v1/capsules

# Strict mode: requires review.status=approved
python capsule_linter.py truth-capsules-v1/capsules --strict

# JSON output for CI
python capsule_linter.py truth-capsules-v1/capsules --json
```

The linter checks:
- Required fields (`id`, `version`, `domain`, `statement`)
- ID pattern (must end with `_vN` or `_vN_suffix`)
- Pedagogy structure (`kind` and `text` fields)
- Witness structure (required fields, valid language enum)
- Provenance (recommended fields, review status)
- Unicode escapes (warns if found, should use UTF-8)
- Assumptions (must be a list if present)

---

## Execution

Use `run_witnesses.py` to execute witnesses:

```bash
# Run all witnesses in capsules directory
python run_witnesses.py truth-capsules-v1/capsules

# Run witnesses for specific capsule
python run_witnesses.py truth-capsules-v1/capsules/pedagogy.problem_solving_v1.yaml
```

**See `WITNESSES_GUIDE.md` for:**
- Execution model and security
- Sandboxing strategies
- Language-specific examples
- Troubleshooting and best practices

---

## Examples

See `/truth-capsules-v1/capsules/` for complete examples:
- `pedagogy.problem_solving_v1.yaml` - Python witness checking problem-solving structure
- `business.decision_log_v1.yaml` - Python witness validating decision records
- `ops.rollback_plan_v1.yaml` - Python witness checking rollback plan completeness

---

## Version History

- **v1.0** (2025-11-07): Initial schema with complete witness support
- Added comprehensive witness fields (`entrypoint`, `timeout_ms`, `env`, etc.)
- Added YAML formatting guidance for code blocks
- Added security considerations and validation tools
