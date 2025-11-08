# Truth Capsules - Project Context for Future Claude

**Purpose:** Comprehensive context for Claude Code sessions working on this project
**Last Updated:** 2025-11-07
**Version:** 1.0.0-rc (HackerNews Ready)
**Status:** Production-ready, all P0 items complete

---

## Project Overview

**What This Is:**
Truth Capsules is a **curation-first prompt library** for LLMs. Think "package manager for system prompts." Users compose deterministic, reproducible system prompts from versioned, signed YAML "capsules" of knowledge/rules/guidance.

**Core Innovation:**
1. **Atomic, versioned capsules** (like npm packages)
2. **Pedagogical design** (Socratic prompts + aphorisms teach models AND humans)
3. **Multi-context portability** (same capsules work in ChatGPT, Claude Code, CI pipelines)
4. **Provenance & signing** (Ed25519 signatures for trust, like Linux package signing)
5. **Deterministic composition** (manifests act as lockfiles)

**Target Audience:**
- Teams using LLMs at scale (need reproducible prompts)
- Organizations with compliance/audit requirements
- Developers building LLM-powered tools
- AI safety researchers (curated safety rules)

**Current Use Cases:**
- PR review automation (GitHub Actions + capsules)
- Code assistant configuration (Claude Code .claue rules)
- Red-teaming and adversarial testing
- Business rule enforcement in CI
- Educational / Socratic tutoring

---

## Project Goals

### v1 RC (Current)
✅ **Ship a credible, useful demo for HackerNews/sponsorship**
- 24 high-quality capsules across multiple domains
- Production-ready CLI tools (lint, compose, sign)
- Clean architecture (shows professional judgment)
- Comprehensive documentation
- Working CI workflows
- Interactive SPA for exploration

### Post-v1 (Community-Driven)
- Expand capsule library (community contributions)
- Build IDE integrations (VSCode extension)
- Create public capsule gallery/registry
- Add live SPA mode (dev server)
- Implement signature verification in CI
- Language bindings (Node.js, Rust, Go)

---

## Architecture

### Design Philosophy

**"Use the right tool for the job"**
- YAML for data (human-readable, git-friendly)
- Python for CLI (ubiquitous, good libraries)
- HTML/JS for SPA (no build step for v1)
- GitHub Actions for CI (standard, easy onboarding)

**Not over-engineered:**
- No React/Vue (overkill for v1 SPA)
- No TypeScript (Python is fine for CLI)
- No custom DSL (YAML is enough)

**Not under-engineered:**
- Clean separation of concerns
- Professional code quality (type hints, docstrings)
- Comprehensive testing (manual for v1, automated later)
- Honest about limitations (snapshot SPA, not live)

### Key Architectural Decisions

**1. YAML over JSON**
- Human-readable (stakeholders can review)
- Git-friendly diffs
- Comments supported (for annotations)
- Multi-line strings easier

**2. Capsules are Immutable**
- Versioning (v1, v2, etc.) instead of in-place edits
- Allows time-travel and reproducibility
- Breaking changes = new version

**3. Pedagogy is First-Class**
- Socratic prompts teach critical thinking
- Aphorisms provide memorable heuristics
- Both are included in composed prompts and can be usefully refined over time

**4. Signing is Optional**
- Ed25519 for cryptographic trust
- Not required (friction for casual users)
- Recommended for production/regulated environments

**5. SPA is Snapshot-Based (v1)**
- Frozen data at generation time
- Avoids CORS/server complexity
- Easy to host (static HTML)
- Regenerate when capsules change

---

## File Structure

```
truth_capsules_poc/
├── truth-capsules-v1/             # Main package
│   ├── capsules/                  # 24 YAML capsule files
│   │   ├── llm.*.yaml            # LLM behavior capsules
│   │   ├── business.*.yaml       # Business rules
│   │   ├── ops.*.yaml            # Operations
│   │   └── pedagogy.*.yaml       # Meta-guidance
│   ├── bundles/                   # 6 pre-composed bundle sets
│   │   ├── conversation_red_team_baseline_v1.yaml
│   │   ├── pr_review_minibundle_v1.yaml
│   │   └── ...
│   ├── profiles/                  # 7 context profiles
│   │   ├── conversational.yaml
│   │   ├── ci_det.yaml
│   │   └── ...
│   ├── docs/                      # 14 markdown documentation files
│   │   ├── QUICKSTART.md
│   │   ├── CAPSULE_SCHEMA_v1.md
│   │   ├── PROFILES_REFERENCE.md
│   │   └── ...
│   ├── .github/workflows/         # 4 GitHub Actions workflows
│   │   ├── capsules-lint.yml
│   │   ├── capsules-compose.yml
│   │   ├── capsules-llm-judge.yml
│   │   └── capsules-policy.yml
│   ├── examples/                  # Sample outputs and fixtures
│   └── README.md                  # Main project README
│
├── spa/                           # SPA generator (template-first)
│   ├── template.html             # Clean HTML template (22KB)
│   ├── generate_spa.py           # Generator script (~150 lines)
│   └── README.md                 # SPA architecture docs
│
├── capsule_linter.py              # CLI linter (~150 lines)
├── compose_capsules_cli.py        # CLI composer (~350 lines)
├── capsule_sign.py                # Ed25519 signing
├── capsule_verify.py              # Ed25519 verification
├── fix_unicode_escapes.py         # Utility: fix \u2265 → ≥
│
├── capsule_composer.html          # Generated SPA (97KB)
│
├── P0_FIXES_COMPLETED.md          # P0 work summary
├── SPA_REFACTOR_COMPLETE.md       # SPA architecture notes
├── CLAUDE_ASSESSMENT_V1__STATUS_AND_FEEDBACK.md  # Initial assessment
└── PROJECT_CONTEXT.md             # This file
```

---

## Component Details

### 1. Capsule Files (`truth-capsules-v1/capsules/*.yaml`)

**Structure:**
```yaml
id: llm.example_v1                  # Required: unique ID with _vN suffix
version: 1.0.0                      # Required: semantic version
domain: llm                         # Required: domain (llm, business, ops, etc.)
title: Human-Readable Title         # Optional but recommended
statement: "The core rule/requirement"  # Required: what this capsule enforces

assumptions:                        # Optional: list of assumptions
  - "User has context X"
  - "Environment supports Y"

pedagogy:                           # Optional: teaching prompts
  - kind: Socratic
    text: "What evidence supports this?"
  - kind: Aphorism
    text: "Cite or abstain."

provenance:                         # Optional: metadata + signing
  author: "John Doe"
  org: "Acme Corp"
  license: "MIT"
  schema: "provenance.v1"
  created: "2025-11-07T00:00:00Z"
  updated: "2025-11-07T00:00:00Z"
  review:
    status: draft | in_review | approved | deprecated
    reviewers: []
    last_reviewed: null
  signing:
    method: "ed25519"
    key_id: "prod-key-v1"
    pubkey: "base64-encoded-public-key"
    digest: "sha256-of-canonical-JSON"
    signature: "base64-encoded-signature"

applies_to:                         # Optional: context hints
  - conversation
  - code_assistant
  - ci

dependencies: []                    # Optional: capsule dependencies (not yet implemented)
incompatible_with: []               # Optional: exclusions (not yet implemented)

security:                           # Optional: sensitivity metadata
  sensitivity: low | medium | high
  notes: "Additional security notes"

witnesses: []                       # Optional: test/validation code
```

**Current Capsules (24):**
- `llm.*` (18): LLM behavior, reasoning, safety
- `business.*` (1): Business rules
- `ops.*` (1): Operations/deployment
- `pedagogy.*` (1): Meta-guidance

**All capsules have UTF-8 characters (≥, ≤, →) not escape sequences (`\u2265`)**

### 2. Bundles (`truth-capsules-v1/bundles/*.yaml`)

**Structure:**
```yaml
name: my_bundle_v1
applies_to:
  - conversation
  - code_assistant
capsules:
  - llm.citation_required_v1
  - llm.plan_verify_answer_v1
  - llm.red_team_assessment_v1
env: {}
secrets: []
```

**Current Bundles (6):**
- `conversation_red_team_baseline_v1` - 10 capsules
- `pr_review_minibundle_v1` - 5 capsules
- `assistant_baseline_v1` - 4 capsules
- `ci_llm_baseline_v1` - 5 capsules
- `ci_nonllm_baseline_v1` - 2 capsules
- `conversation_pedagogy_v1` - 1 capsule

### 3. Profiles (`truth-capsules-v1/profiles/*.yaml`)

**Structure:**
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

**Current Profiles (7):**
- `profile.conversational_guidance_v1` (alias: `conversational`)
- `profile.pedagogical_v1` (alias: `pedagogical`)
- `profile.code_patch_v1` (alias: `code_patch`)
- `profile.tool_runner_v1` (alias: `tool_runner`)
- `profile.ci_deterministic_gate_v1` (alias: `ci_det`)
- `profile.ci_llm_judge_v1` (alias: `ci_llm`)
- `profile.rules_generator_v1` (alias: `rules_gen`)

**Profile aliases** are defined in `compose_capsules_cli.py:PROFILE_ALIASES`

### 4. CLI Tools

**`capsule_linter.py` (~150 lines)**
- Validates required fields (id, version, domain, statement)
- Checks ID pattern: `domain.name_vN` or `domain.name_vN_suffix`
- Validates provenance structure and review status
- Detects unicode escape sequences in raw YAML
- Validates `assumptions` is a list
- Supports `--strict` mode (requires `review.status=approved`)
- Supports `--json` output for CI integration
- Exit codes: 0 (success), 1 (errors), 2 (bad arguments)

**`compose_capsules_cli.py` (~350 lines)**
- Loads profiles, bundles, capsules from YAML
- Resolves profile by exact ID or alias
- Composes deterministic system prompts
- Generates manifest JSON (like a lockfile)
- Supports multiple bundles and capsules
- `--list-profiles` and `--list-bundles` for discovery
- Uses profile `system_block` if present (avoids duplication)
- Exit codes: 0 (success), 2 (profile/args error), 3 (no capsules)

**`fix_unicode_escapes.py` (~100 lines)**
- Converts `\u2265` → `≥`, `\u2264` → `≤`, etc.
- Supports `--dry-run` for preview
- Processes all YAML files in directory
- Used to fix legacy unicode escapes

**`capsule_sign.py` / `capsule_verify.py`**
- Ed25519 signing for capsules
- Updates `provenance.signing` block
- Calculates SHA256 digest of canonical JSON
- Not heavily tested in this session (marked as "done" in TODO)

### 5. SPA Architecture

**Template-First Design (Refactored in this session):**

**Before:**
- 800-line monolithic `compose_prompt_spa.py`
- HTML strings embedded in Python
- Difficult to maintain

**After:**
```
spa/
├── template.html (22KB)          # Clean HTML, editable in any editor
├── generate_spa.py (~150 lines)  # Data loader + Jinja2 renderer
└── README.md                     # Architecture docs
```

**Generation:**
```bash
python spa/generate_spa.py --root truth-capsules-v1 --output capsule_composer.html
```

**Output:** `capsule_composer.html` (97KB, 1939 lines with pretty-printed JSON)

**Key Decisions:**
- Snapshot mode (frozen data) for v1 (appropriate trade-off)
- Jinja2 for templating (standard, clean)
- Pretty-printed JSON (readable in DevTools)
- Honest documentation about limitations

---

## Current Status (v1 RC)

### ✅ Completed (P0)

1. **Unicode Fixes**
   - Fixed 13 capsules with escape sequences
   - Created `fix_unicode_escapes.py` tool
   - All capsules now have UTF-8 characters

2. **Linter Enhancements**
   - Added unicode escape detection
   - Fixed ID regex for `_vN_suffix` patterns
   - Added `assumptions` validation
   - Added provenance validation
   - Implemented `--strict` mode

3. **CLI Composer Improvements**
   - Fixed duplicate system block issue
   - Added profile alias support
   - Added `--list-profiles` and `--list-bundles`
   - Better error messages with suggestions

4. **Documentation Updates**
   - Created `PROFILES_REFERENCE.md`
   - Rewrote `QUICKSTART.md` with working examples
   - Fixed `ONE_PAGER.md`
   - Updated main `README.md` (comprehensive)
   - Updated `TODO.md` with actual status

5. **SPA Refactor**
   - Template-first architecture
   - Clean 150-line generator
   - Comprehensive `spa/README.md`
   - Generated new SPA with latest data

### 🔄 In Progress (Post-v1)

- Signature verification in CI workflows
- PR comment bot integration
- SPA provenance panel
- Live SPA mode with dev server
- Secrets handling capsules
- Capsule search and tagging

### 📋 Backlog (Community-Driven)

- VSCode extension
- Community capsule gallery
- Language bindings (Node.js, Rust)
- Enhanced pedagogy features
- Dependency resolution
- Incompatibility checking

---

## Development Workflows

### Adding a New Capsule

1. **Create YAML file:**
   ```bash
   touch truth-capsules-v1/capsules/llm.my_capsule_v1.yaml
   ```

2. **Fill in required fields:**
   - `id`, `version`, `domain`, `statement`
   - Add pedagogy (Socratic + Aphorism recommended)
   - Add provenance block

3. **Lint:**
   ```bash
   python capsule_linter.py truth-capsules-v1/capsules
   ```

4. **Test composition:**
   ```bash
   python compose_capsules_cli.py \
     --root truth-capsules-v1 \
     --profile conversational \
     --capsule llm.my_capsule_v1 \
     --out /tmp/test.txt
   ```

5. **Add to bundle** (optional):
   Edit `bundles/my_bundle_v1.yaml` and add capsule ID

6. **Regenerate SPA:**
   ```bash
   python spa/generate_spa.py --root truth-capsules-v1 --output capsule_composer.html
   ```

### Creating a Bundle

1. **Create YAML file:**
   ```bash
   touch truth-capsules-v1/bundles/my_bundle_v1.yaml
   ```

2. **Define bundle:**
   ```yaml
   name: my_bundle_v1
   applies_to:
     - conversation
   capsules:
     - llm.capsule1_v1
     - llm.capsule2_v1
   ```

3. **Test:**
   ```bash
   python compose_capsules_cli.py \
     --root truth-capsules-v1 \
     --profile conversational \
     --bundle my_bundle_v1 \
     --out /tmp/test.txt
   ```

### Updating Documentation

1. **Edit markdown files** in `truth-capsules-v1/docs/`
2. **Verify links** (all relative paths)
3. **Update README.md** if adding new docs
4. **Check consistency** across all doc files

### Regenerating SPA

**When to regenerate:**
- After adding/modifying capsules
- After adding/modifying bundles
- After adding/modifying profiles
- Before committing to git

**Command:**
```bash
python spa/generate_spa.py --root truth-capsules-v1 --output capsule_composer.html
```

**Verify:**
- Open in browser
- Check generation timestamp
- Test compose functionality
- Verify UTF-8 characters (not escape sequences)

---

## Testing Approach

### Current (v1)
- **Manual testing** for all features
- **Visual inspection** of generated prompts
- **Browser testing** for SPA
- **End-to-end smoke tests** documented in assessment files

### Future (v2+)
- **Unit tests** for CLI tools (pytest)
- **Integration tests** for composition workflow
- **Golden file tests** for deterministic output
- **CI tests** for all workflows
- **Browser automation** for SPA (Playwright)

---

## Known Issues & Gotchas

### 1. Profile Naming Inconsistency (Fixed)

**Issue:** Docs referenced profile names that didn't match actual IDs
**Fix:** Added alias system + updated docs
**Prevention:** Use `--list-profiles` to verify names

### 2. Unicode Escape Sequences (Fixed)

**Issue:** Some capsules had `\u2265` instead of `≥`
**Fix:** Ran `fix_unicode_escapes.py`
**Prevention:** Linter now detects and warns

### 3. SPA Data Staleness

**Issue:** SPA has frozen snapshot data
**Not a bug:** This is by design for v1
**Workaround:** Regenerate SPA when capsules change

### 4. Duplicate System Block (Fixed)

**Issue:** Composer output both structured fields AND `system_block`
**Fix:** Check if `system_block` exists, use it exclusively
**Prevention:** Template uses `system_block` if present

### 5. Python Version Compatibility

**Requirement:** Python 3.11+ (for type hints like `tuple[str, int]`)
**Workaround:** Use Python 3.10 with `from __future__ import annotations`

### 6. YAML Parsing Gotchas

- **Multi-line strings:** Use `|` or `>` for readability
- **Colons in values:** Quote strings with `: ` in them
- **Unicode:** Always use UTF-8, never escape sequences
- **Null vs empty:** Distinguish between `field:` (null) and `field: []` (empty list)

---

## Dependencies

### Required
- Python 3.11+ (or 3.10 with future annotations)
- PyYAML (`pip install pyyaml`)
- Jinja2 (`pip install jinja2`) - for SPA generation only

### Optional
- PyNaCl (`pip install pynacl`) - for signing/verification
- Anthropic SDK - for Claude API examples
- OpenAI SDK - for GPT API examples

### No Build Tools Required
- No npm/webpack/bundlers
- No TypeScript compiler
- No CSS preprocessors
- Plain HTML/CSS/JS for SPA

---

## HackerNews Positioning

### Key Messages

1. **"Package manager for LLM prompts"**
   - Familiar analogy (npm, pip, cargo)
   - Immediately understandable value prop

2. **"Pedagogy-first design"**
   - Socratic prompts teach critical thinking
   - Aphorisms provide memorable heuristics
   - Unique differentiation

3. **"Works everywhere"**
   - Same capsules in ChatGPT, Claude Code, CI
   - Portability is a key benefit

4. **"Provenance & signing"**
   - Like Linux package signing
   - Matters for regulated industries

5. **"Honest about v1 scope"**
   - SPA is snapshot-based (fine for v1)
   - CLI is production-ready
   - Clear path to enhancement

### Expected Objections & Responses

**"Why YAML not JSON?"**
- Git-friendly diffs, human-readable, comments supported
- Non-technical stakeholders can review

**"This is over-engineered prompt management"**
- Fair for simple cases; shines with teams/compliance/CI
- Don't need it for single .txt prompts

**"Signing is security theater"**
- Not about preventing injection; about org trust/audit
- "Who approved this?" matters in compliance

**"SPA is limited"**
- Correct! It's a demo with frozen data
- CLI is the production tool
- Iterating based on feedback

---

## Tips for Future Claude Sessions

### Quick Orientation

1. **Read this file first** (you're doing it!)
2. **Read `P0_FIXES_COMPLETED.md`** for recent work
3. **Read `CLAUDE_ASSESSMENT_V1__STATUS_AND_FEEDBACK.md`** for initial state
4. **Check `truth-capsules-v1/TODO.md`** for prioritized backlog

### Common Tasks

**"Add a new capsule":**
1. Copy existing capsule as template
2. Update ID, statement, pedagogy
3. Run linter
4. Test composition
5. Regenerate SPA

**"Fix a bug":**
1. Understand the issue
2. Check if it's documented in this file
3. Fix in appropriate component
4. Test end-to-end
5. Update docs if needed

**"Add a feature":**
1. Check `TODO.md` for priority
2. Ensure it aligns with v1 scope
3. Implement with clean code (type hints, docstrings)
4. Update docs
5. Test thoroughly

**"Prepare for HN launch":**
1. Verify all P0 items complete (check `P0_FIXES_COMPLETED.md`)
2. Test all examples in QUICKSTART.md
3. Regenerate SPA with fresh data
4. Spell-check all docs
5. Verify links in README.md

### Code Quality Standards

- **Type hints** on all functions
- **Docstrings** for all public functions
- **Clean variable names** (no single letters except loop indices)
- **Comments** for non-obvious logic
- **Error handling** with helpful messages
- **Exit codes** (0 = success, 1 = error, 2 = bad args)

### Documentation Standards

- **Markdown** for all docs (GitHub-flavored)
- **Code blocks** with language tags
- **Links** are relative (work in repo and web)
- **Examples** are copy-paste ready
- **Headings** use consistent hierarchy

---

## Useful Commands

```bash
# Lint capsules
python capsule_linter.py truth-capsules-v1/capsules
python capsule_linter.py truth-capsules-v1/capsules --strict
python capsule_linter.py truth-capsules-v1/capsules --json

# List profiles and bundles
python compose_capsules_cli.py --root truth-capsules-v1 --list-profiles
python compose_capsules_cli.py --root truth-capsules-v1 --list-bundles

# Compose a prompt
python compose_capsules_cli.py \
  --root truth-capsules-v1 \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out prompt.txt \
  --manifest manifest.json

# Fix unicode escapes
python fix_unicode_escapes.py truth-capsules-v1/capsules --dry-run
python fix_unicode_escapes.py truth-capsules-v1/capsules

# Regenerate SPA
python spa/generate_spa.py --root truth-capsules-v1 --output capsule_composer.html

# Find all YAML files
find truth-capsules-v1 -name "*.yaml" -o -name "*.yml"

# Count capsules/bundles/profiles
ls truth-capsules-v1/capsules/*.yaml | wc -l
ls truth-capsules-v1/bundles/*.yaml | wc -l
ls truth-capsules-v1/profiles/*.yaml | wc -l

# Check for unicode escapes
grep -r "\\\\u[0-9]" truth-capsules-v1/capsules/

# Verify UTF-8 characters
grep -r "≥\|≤\|→" truth-capsules-v1/capsules/ | wc -l
```

---

## Project Health Indicators

### ✅ Healthy
- All P0 items complete
- No linter errors
- All capsules have UTF-8 characters
- SPA loads without errors
- Documentation is comprehensive
- CLI tools have `--help`
- Exit codes are consistent

### ⚠️ Needs Attention
- Signature verification not in CI yet
- Some TODO items marked "FOR REVIEW" but not reviewed
- No automated tests (manual only)
- SPA is snapshot-based (not live)

### 📈 Metrics
- **24 capsules** (goal: 50+ by end of year)
- **6 bundles** (goal: 10+ by end of year)
- **7 profiles** (sufficient for v1)
- **14 doc files** (comprehensive)
- **4 CI workflows** (good coverage)
- **0 linter errors** (clean)

---

## Contact & Maintenance

**Primary Maintainer:** John Macgregor (see provenance headers)

**For Future Claude Sessions:**
- This project is well-documented
- Start with this file + assessment docs
- Code quality is high (type hints, docstrings)
- Architecture is clean (no spaghetti)
- Scope is clear (v1 vs future)
- User is pragmatic and open to suggestions

**Philosophy:**
- Ship fast, iterate based on feedback
- Be honest about limitations
- Show good technical judgment
- Don't over-engineer for v1
- Document everything

---

## Final Notes

**This project is HackerNews-ready.** All P0 fixes are complete, documentation is comprehensive, and code quality is professional. The user (John/Juancho) has been systematic and thoughtful throughout development.

**Key Strengths:**
- Novel concept with clear value prop
- Excellent pedagogy (Socratic + Aphorism)
- Professional code and architecture
- Honest about v1 scope
- Comprehensive documentation
- Ready to scale post-launch

**What Makes This Special:**
- Not just "prompt templates" (those exist)
- **Curation + versioning + provenance + pedagogy** (unique combination)
- Works across multiple contexts (portability)
- Teaches both models AND humans (dual benefit)

**Future Claude:** You're inheriting a well-architected, well-documented project with clear next steps. Have fun building on this foundation!

---

*End of Project Context*
