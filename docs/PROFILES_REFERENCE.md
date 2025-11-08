# Profiles Reference

Profiles define the context and output format for composed prompts. Each profile specifies a response format (natural language, JSON, etc.) and policy guidance.

## Available Profiles

### Conversational

**ID:** `profile.conversational_guidance_v1`
**Alias:** `conversational`
**Format:** Natural language
**Use case:** Interactive Q&A, chat interfaces

Emphasizes reasoning guardrails with "cite or abstain" policy and Plan→Verify→Answer workflow.

**Example:**
```bash
python compose_capsules_cli.py \
  --root truth-capsules-v1 \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out prompt.txt
```

---

### Pedagogical / Socratic

**ID:** `profile.pedagogical_v1`
**Alias:** `pedagogical`
**Format:** Natural language with teaching prompts
**Use case:** Educational contexts, learning assistance

Focuses on Socratic questioning and guided learning.

---

### Code Patch Assistant

**ID:** `profile.code_patch_v1`
**Alias:** `code_patch`
**Format:** Code diffs and structured comments
**Use case:** PR reviews, code changes

Optimized for reviewing diffs and suggesting patches.

---

### Tool Runner / Function Caller

**ID:** `profile.tool_runner_v1`
**Alias:** `tool_runner`
**Format:** JSON with function calls
**Use case:** Agent systems with tool/function calling

Enforces strict JSON schemas for tool invocation.

---

### CI Gate - Deterministic

**ID:** `profile.ci_deterministic_gate_v1`
**Alias:** `ci_det`
**Format:** JSON pass/fail reports
**Use case:** Non-LLM CI checks, linting gates

Machine-parseable output for automated workflows.

**Example:**
```bash
python compose_capsules_cli.py \
  --root truth-capsules-v1 \
  --profile ci_det \
  --bundle ci_nonllm_baseline_v1 \
  --out ci_prompt.txt
```

---

### CI Gate - LLM Judge

**ID:** `profile.ci_llm_judge_v1`
**Alias:** `ci_llm`
**Format:** JSON with scored rubrics
**Use case:** LLM-as-judge CI gates, quality assessment

Uses an LLM to evaluate outputs against capsule criteria.

---

### Rules Generator

**ID:** `profile.rules_generator_v1`
**Alias:** `rules_gen`
**Format:** Structured rule definitions
**Use case:** Generating new capsules or policies

Meta-profile for capsule authoring assistance.

---

## Using Profiles

### By Alias (Recommended)

```bash
python compose_capsules_cli.py \
  --root truth-capsules-v1 \
  --profile conversational \
  --bundle my_bundle \
  --out prompt.txt
```

### By Full ID

```bash
python compose_capsules_cli.py \
  --root truth-capsules-v1 \
  --profile profile.conversational_guidance_v1 \
  --bundle my_bundle \
  --out prompt.txt
```

### List All Profiles

```bash
python compose_capsules_cli.py --root truth-capsules-v1 --list-profiles
```

## Profile Structure

Profiles are YAML files with this structure:

```yaml
kind: profile
id: profile.example_v1
title: Human-Readable Title
version: 1.0.0
description: Brief description of use case

response:
  format: natural | json | markdown
  policy: |
    Brief policy statement (e.g., "Cite sources")
  system_block: |
    Pre-formatted system prompt block.
    Can include multiple lines with SYSTEM:, POLICY:, FORMAT: markers.
  schema_ref: optional.schema.v1  # For JSON output validation

download:
  suggested_ext: txt | json | md
```

---

## Projections (v1.1)

**New in v1.1:** Profiles can define **projections** to control which capsule fields are rendered and how they're formatted.

### What Are Projections?

Projections filter and slice capsule fields for different contexts. Think of them as "views" on capsules:
- **Full view:** All fields, all pedagogy
- **Compact view:** Core fields only, no pedagogy
- **CI view:** Minimal fields for machine parsing
- **Custom views:** Profile-specific field selections

### Profile Projection Structure

```yaml
response:
  format: natural
  policy: |
    Cite or abstain; follow Plan→Verify→Answer.
  system_block: |
    SYSTEM: Profile=My Profile
    POLICY: ...

  # Projection configuration
  projection:
    include:
      - title
      - statement
      - assumptions[:5]           # Limit to first 5 assumptions
      - pedagogy.socratic[:3]     # Limit to first 3 Socratic prompts
      - pedagogy.aphorisms[:3]    # Limit to first 3 aphorisms
    render:
      capsule_header: "BEGIN CAPSULE id={id} version={version} domain={domain}"
      assumption_bullet: "  - {text}"
      socratic_bullet: "  - {text}"
      aphorism_bullet: "  - {text}"
      enforcement_footer: "ENFORCEMENT: Obey or abstain. END CAPSULE"
```

### Projection Fields

#### `include` (array)
List of fields to render from each capsule. Supports slicing with `[:N]` syntax.

**Simple fields:**
- `title` - Capsule title
- `statement` - Core requirement
- `assumptions` - Full assumptions list
- `assumptions[:N]` - First N assumptions

**Pedagogy fields (special syntax):**
- `pedagogy.socratic[:N]` - First N Socratic prompts
- `pedagogy.aphorisms[:N]` - First N aphorisms

**Example:**
```yaml
include:
  - title
  - statement
  - assumptions[:3]           # Only 3 assumptions
  - pedagogy.socratic[:2]     # Only 2 Socratic prompts
```

#### `render` (object, optional)
Template strings for formatting output. Supports `{variable}` placeholders.

**Available templates:**
- `capsule_header` - Capsule start marker
- `assumption_bullet` - Each assumption line
- `socratic_bullet` - Each Socratic prompt line
- `aphorism_bullet` - Each aphorism line
- `enforcement_footer` - Capsule end marker

**Variables:**
- `{id}` - Capsule ID
- `{version}` - Capsule version
- `{domain}` - Capsule domain
- `{text}` - Item text (for bullets)

**Example:**
```yaml
render:
  capsule_header: "## Capsule: {id} (v{version})"
  assumption_bullet: "* Assumes: {text}"
  enforcement_footer: "---"
```

### Using Projections

Projections are automatically applied when composing:

```bash
# Uses profile's default projection
python compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle my_bundle \
  --out prompt.txt
```

### Override Projection

Use `--compact` to exclude pedagogy regardless of projection:

```bash
# Compact mode: no pedagogy
python compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle my_bundle \
  --compact \
  --out compact_prompt.txt
```

### Projection Example

**Without projection (full output):**
```
BEGIN CAPSULE id=llm.citation_required_v1 version=1.0.0 domain=llm
TITLE: Citations required
STATEMENT: Answers must include at least one citation or abstain.
ASSUMPTIONS:
  - Operating in a general context
  - Citations are available
  - User expects sourced information
  - System has access to references
  - Output format supports citations
SOCRATIC:
  - What evidence supports this claim?
  - Where can I verify this information?
  - What sources did I consult?
  - How recent is this data?
  - What conflicting evidence exists?
APHORISMS:
  - Cite or abstain.
  - Sources build trust.
  - Evidence over assertion.
ENFORCEMENT: Obey or abstain. END CAPSULE
```

**With projection (`assumptions[:2]`, `pedagogy.socratic[:2]`, `pedagogy.aphorisms[:1]`):**
```
BEGIN CAPSULE id=llm.citation_required_v1 version=1.0.0 domain=llm
TITLE: Citations required
STATEMENT: Answers must include at least one citation or abstain.
ASSUMPTIONS:
  - Operating in a general context
  - Citations are available
SOCRATIC:
  - What evidence supports this claim?
  - Where can I verify this information?
APHORISMS:
  - Cite or abstain.
ENFORCEMENT: Obey or abstain. END CAPSULE
```

**With `--compact` (no pedagogy):**
```
BEGIN CAPSULE id=llm.citation_required_v1 version=1.0.0 domain=llm
TITLE: Citations required
STATEMENT: Answers must include at least one citation or abstain.
ASSUMPTIONS:
  - Operating in a general context
  - Citations are available
ENFORCEMENT: Obey or abstain. END CAPSULE
```

### Projection Best Practices

1. **Conversational profiles:** Include pedagogy (Socratic + aphorisms) to teach critical thinking
2. **CI profiles:** Exclude pedagogy for concise, machine-readable output
3. **Code assistant profiles:** Limit to 2-3 pedagogy items to avoid verbosity
4. **Field limits:** Use `[:N]` slicing to prevent prompt bloat

**Recommended limits:**
- `assumptions[:5]` - Top 5 assumptions are usually sufficient
- `pedagogy.socratic[:3]` - 3 Socratic prompts provide good coverage
- `pedagogy.aphorisms[:3]` - 3 aphorisms for memorable heuristics

### Backward Compatibility

Profiles without `projection` will use legacy rendering (all fields, up to 5 items each). This ensures existing workflows continue to work.

---

## Creating Custom Profiles

1. Copy an existing profile from `profiles/` directory
2. Update the `id`, `title`, `description`
3. Customize the `response.policy` and `response.system_block`
4. Save to `profiles/my_profile.yaml`
5. Use with `--profile my_profile` (or full ID)

**Note:** Profile file names don't need to match the `id` field, but it's recommended for clarity.

## Best Practices

- **Conversational profiles:** Use for interactive UX, chatbots, customer support
- **CI profiles:** Use for automated gates, never in user-facing contexts
- **Tool runner profiles:** Use only when function calling is required
- **Pedagogical profiles:** Use for educational tools, tutoring, training

Choose the profile that matches your output format requirements and workflow context.
