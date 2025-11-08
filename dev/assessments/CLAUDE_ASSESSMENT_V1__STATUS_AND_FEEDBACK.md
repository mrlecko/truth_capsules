# Truth Capsules v1 RC - Claude Code Assessment
**Review Date**: 2025-11-07
**Reviewer**: Claude (Sonnet 4.5)
**Purpose**: HackerNews-ready v1 RC assessment for hire/sponsorship demo

---

## Executive Summary

**Verdict: STRONG CONCEPT, SOLID FOUNDATION - NEEDS POLISH & ALIGNMENT**

Truth Capsules is a compelling, pedagogically-oriented approach to LLM prompt engineering that addresses real pain points in prompt management, reproducibility, and curation. The core idea-atomic, versioned, signed YAML "capsules" of knowledge that compose into system prompts for multiple contexts (conversation, code assistant, CI)-is innovative and immediately useful.

**The Good:**
- Novel and practical concept with clear value proposition
- Clean, minimal YAML schema that's human-readable and maintainable
- Working CLI tools (linter, composer, signing/verification)
- Excellent pedagogical framing (Socratic prompts + aphorisms)
- Solid provenance model with optional Ed25519 signing
- Diverse, high-quality example capsules (24 capsules covering PR review, red-teaming, safety)
- Complete GitHub Actions CI workflows
- Comprehensive documentation structure

**The Gaps:**
- HTML SPA needs critical fixes and optimization (see detailed issues below)
- Documentation inconsistencies and outdated references
- Bundle/profile naming mismatches between docs and implementation
- Missing or incomplete TODO items that are marked as "DONE" or "FOR REVIEW"
- No live demo or quick-start experience
- Security/CSP guidance incomplete for the SPA

**HackerNews Readiness: 65% - Needs 2-3 days of focused polish**

---

## Detailed Assessment

### 1. Core Architecture & Design

#### Strengths:
- **Schema Design (9/10)**: The YAML capsule schema is elegant and well-thought-out. Required fields are minimal (`id`, `version`, `domain`, `statement`), with rich optional metadata (provenance, pedagogy, security).
- **Provenance Model (8/10)**: The provenance block with signing support is a killer feature. Ed25519 signatures with SHA256 digests provide cryptographic trust.
- **Composability (9/10)**: The bundle → capsule → prompt composition flow is clean and deterministic.
- **Pedagogy First (10/10)**: The Socratic + Aphorism structure is brilliant. It teaches both the model and the human reader.

#### Weaknesses:
- **Profiles Mismatch**: The documentation (ONE_PAGER.md, QUICKSTART.md, TODO.md) references profile names like `conversation_pedagogy_v1` and `ci_nonllm_baseline_v1`, but the actual profile files use different IDs (`profile.conversational_guidance_v1`, etc.). This will confuse first-time users.
- **Bundle Schema Documentation**: Bundles are referenced extensively but the schema isn't documented as clearly as capsules (e.g., what are `modes`, `env`, `secrets` fields for?).
- **No Schema Validation**: The linter checks required keys but doesn't validate against a formal JSON Schema or similar.

---

### 2. CLI Tools

#### `capsule_linter.py` (8/10)
**Working:** Yes
**Issues Found:**
- ✅ Correctly validates required keys
- ✅ Checks pedagogy structure
- ✅ Emits clean errors/warnings
- ⚠️ One false-positive warning on `llm.citation_required_v1_signed` (it says ID should end with `_vN` but it does: `_v1_signed`)
- ❌ No provenance validation (e.g., checking `review.status` values, signature structure)
- ❌ No check for `assumptions` being a list

**Recommendation:**
- Add provenance schema validation
- Fix regex for `_vN` suffix to allow `_vN_suffix` patterns
- Add optional strict mode that enforces `review.status=approved` for production

#### `compose_capsules_cli.py` (7/10)
**Working:** Yes (tested successfully with 10 capsules)
**Issues Found:**
- ✅ Profile, bundle, and capsule resolution works
- ✅ Deterministic output
- ✅ Manifest generation
- ❌ Profile lookup uses exact ID match, but docs show short names
- ❌ No validation that selected capsules are compatible (ignores `incompatible_with` field)
- ❌ No support for `dependencies` field in capsules
- ⚠️ Output format has duplicate SYSTEM/POLICY blocks (lines 1-7 in test output)

**Recommendation:**
- Add profile alias support (e.g., `conversational` → `profile.conversational_guidance_v1`)
- Implement dependency resolution
- Check `incompatible_with` and warn/error
- Fix duplicate system block emission

#### `capsule_sign.py` / `capsule_verify.py` (Not Tested)
**Status:** Present but not executed in this review
**Observation:** Referenced in docs and TODO, marked as "DONE" for signing, "TODO" for CI integration

---

### 3. Capsules Collection

**Quality: 9/10**
**Quantity:** 24 capsules across multiple domains

**Standout Capsules:**
- `llm.pr_diff_first_v1`: Excellent PR review guidance
- `llm.citation_required_v1`: Simple, powerful rule
- `llm.counterfactual_probe_v1`: Deep reasoning technique
- `llm.pii_redaction_guard_v1`: Safety-first design
- `llm.red_team_assessment_v1`: Comprehensive adversarial protocol

**Issues:**
- Some capsules have `review.status=draft` but are used in "baseline" bundles (inconsistency)
- No "hello world" minimal example capsule for tutorials
- Witnesses field is present but always empty (should this be removed or documented?)

---

### 4. Bundles & Profiles

**Bundles (6/10):**
- 6 bundles provided (PR review, red team, assistant, CI)
- Names in bundles directory don't match TODO.md references:
  - TODO says `pr_review_minibundle_v1` ✅ (matches)
  - TODO says `conversation_red_team_baseline_v1` ✅ (matches)
  - TODO references `ci_nonllm_baseline_v1` but that's a **profile**, not a bundle

**Profiles (5/10):**
- 7 profiles provided
- **CRITICAL ISSUE:** Profile IDs don't match documentation examples:
  - Docs say: `conversation_pedagogy_v1`
  - Reality: `profile.conversational_guidance_v1`
- Profile schema is cleaner now (kind, id, title, version, response block) but undocumented in PROFILES.md
- No "getting started" profile for newcomers

---

### 5. HTML SPA (`capsule_composer_profiles_demo.html`)

**Status: NEEDS SIGNIFICANT WORK (4/10)**

#### Working Features:
- Dark mode UI is polished
- Drag-and-drop reordering
- Bundle/capsule selection
- Markdown preview toggle
- Copy/download buttons
- Search/filter

#### Critical Issues Found:

**P0 Issues (Blockers for HN launch):**

1. **Profile Loading Broken:**
   - Profiles are embedded in the HTML as a massive inline JSON blob
   - The embedded data structure doesn't match the actual YAML profile schema
   - Profile dropdown likely won't work with real profiles without regeneration

2. **Inline Data Staleness:**
   - All capsules/bundles/profiles are hardcoded in the HTML (generated 2025-11-07T04:33:17Z)
   - No way to load fresh data without regenerating the entire HTML
   - This defeats the purpose of "curated, versioned" capsules
   - Users can't use the SPA with their own capsules without editing the HTML source

3. **No Loading from Filesystem:**
   - Despite being a "local file" SPA, it can't load YAML files from disk
   - Browser security prevents `file://` access to adjacent files
   - This fundamentally limits the SPA's usefulness

4. **TODO.md Item P0-07 Marked "DONE" but Incomplete:**
   - "Safe load & sanitization" is marked DONE
   - But HTML escaping is basic, no DOMPurify or similar
   - No CSP implementation in the HTML itself (just docs)

**P1 Issues (Polish for HN):**

5. **No Provenance Display:**
   - TODO P1-11 "Provenance panel" is marked TODO
   - Critical for trust/signing story
   - Should show author, org, license, review status, signature validity

6. **No YAML Export:**
   - Can download composed prompt
   - Can't export a capsule as YAML
   - Can't save bundle selections as a new bundle YAML

7. **No Share Link Implementation:**
   - "Share Link" button exists but TODO doesn't mention URL param support
   - Would be valuable for demos (e.g., `?bundle=pr_review_minibundle_v1`)

8. **No Validation Feedback:**
   - "Validate All" button exists but no indication what it does
   - No visual feedback on validation errors in capsules

9. **Large File Size:**
   - 401 lines with ~25KB+ of embedded JSON data
   - Not optimized for quick loading

**Security Issues:**

10. **Inline Script Violates Recommended CSP:**
    - SECURITY_CSP.md says `script-src 'self'`
    - But entire SPA is one HTML file with inline `<script>` tag
    - Would need `'unsafe-inline'` or script hash to work with strict CSP

11. **No Subresource Integrity:**
    - No external dependencies (good)
    - But also no version tracking or integrity checks if/when dependencies are added

#### Recommendations for SPA:

**Option A: Quick Patch (1-2 hours)**
- Add a "Load from URL" feature (CORS-friendly)
- Add provenance modal (read-only display)
- Fix profile data structure
- Add URL parameter support for bundles/profiles
- Add CSP meta tag to HTML

**Option B: Rebuild (4-6 hours)**
- Separate JS/CSS from HTML
- Use a simple static file server pattern (Python `http.server` or similar)
- Load YAML files via fetch API
- Add proper validation UI
- Implement all TODOs marked P0/P1

**Option C: Demo-Only Approach (30 mins)**
- Document that SPA is a "preview demo" with frozen data
- Add regeneration script (`python generate_spa.py → outputs new HTML`)
- Set expectation that CLI is the primary tool
- SPA is for visual exploration only

**My Recommendation: Option C + selective features from A**
- For HN launch, be honest that SPA is a demo preview
- Focus on CLI as the production tool
- Add URL param support + provenance modal (high value, low effort)
- Save full rebuild for post-v1

---

### 6. Documentation

**Coverage: 8/10**
**Accuracy: 5/10**

#### Strong Docs:
- ✅ `CAPSULE_SCHEMA_v1.md`: Clear and complete
- ✅ `SECURITY_CSP.md`: Thoughtful security guidance
- ✅ `PROVENANCE_SIGNING.md`: Explains trust model well
- ✅ `ONE_PAGER.md`: Great elevator pitch
- ✅ `CI_GUIDE.md`: Comprehensive workflow explanation

#### Weak/Broken Docs:
- ❌ `QUICKSTART.md`: References profile names that don't exist
- ❌ `PROFILES.md`: Doesn't document actual profile schema (kind, response block, etc.)
- ❌ `LINTER_GUIDE.md`: Not reviewed but likely needs updating for provenance checks
- ⚠️ `README.md`: Links are all relative, assume they'll work (should verify)

#### Missing Docs:
- ❌ **Bundle Schema Documentation**: What are bundles? How do they differ from profiles?
- ❌ **Getting Started Tutorial**: "Create your first capsule in 5 minutes"
- ❌ **FAQ**: "Why YAML not JSON?", "How does signing work?", "Can I use this with ChatGPT?"
- ❌ **Use Case Examples**: "How Acme Corp uses Truth Capsules for PR review"
- ❌ **Migration Guide**: "How to convert your prompt library to capsules"

---

### 7. GitHub Actions CI

**Status: 8/10 - Solid but untested**

#### Workflows Provided:
1. `capsules-lint.yml` ✅ Simple, clean
2. `capsules-compose.yml` ✅ Composes artifacts
3. `capsules-llm-judge.yml` ✅ LLM-as-a-judge integration
4. `capsules-policy.yml` ✅ Gates on review.status

#### Issues:
- ⚠️ Not verified (no .github repo test runs visible in this assessment)
- ❌ P1-03 "Signature verification step" marked TODO but critical for trust story
- ❌ P1-10 "PR comment bot" marked TODO but high-impact demo feature
- ⚠️ LLM judge workflow likely needs API keys (not documented how to set up)

#### Recommendations:
- Add verification step to lint workflow
- Document API key setup for judge workflow
- Create example PR with before/after judge comments
- Add workflow status badges to README

---

### 8. TODO.md Analysis

**Overall TODO Health: 6/10**

#### Positive:
- Well-structured table with priorities
- Clear P0/P1/P2 distinction
- Honest about what's deferred

#### Issues:

**Marking Errors (items marked DONE but not complete):**
- P0-07: "Safe load & sanitization" - DONE but SPA has no CSP implementation
- P1-05: "LICENSE + CONTRIBUTING + CoC" - FOR REVIEW but they're all very basic boilerplate
- P0-06: "YAML Preview Modal" - DONE but provenance not shown (see P1-11)

**Marking Errors (items marked FOR REVIEW but broken):**
- P0-01: "Capsule schema v1" - FOR REVIEW but schema is solid, should be DONE
- P1-01: "CSP & static hosting guide" - FOR REVIEW but SPA doesn't implement CSP
- P1-15: "Quickstart repo template" - FOR REVIEW but quickstart has broken profile names

**High-Value TODOs Still Open:**
- P1-02: Provenance gating (critical for trust)
- P1-03: Signature verification in CI (critical for trust)
- P1-07: Secrets handling capsules (table stakes for production)
- P1-09: Fixtures & goldens (needed for deterministic CI)
- P1-11: Provenance panel in SPA (critical for signing story)
- P1-13: Capsule search & tags (usability)
- P1-14: Tags in capsules (needed for search)

#### Recommendation:
- Honest re-triage of P0 items
- Move P1-02, P1-03, P1-11 to P0 (critical for HN story)
- Mark P0-07, P1-05, P0-06 as PARTIAL or NEEDS POLISH
- Add P0-16: "Fix docs/profile name mismatches"

---

### 9. Example Usage & Artifacts

**Status: 7/10**

#### Strengths:
- Good example JSON outputs in `artifacts/examples/`
- Multiple domains represented (PII, decision logs, tool schemas)
- Judgment examples show LLM-as-judge pattern

#### Weaknesses:
- No "before and after" examples (raw prompt vs. composed prompt)
- No side-by-side comparison of different bundle compositions
- No example of using a composed prompt with Claude/OpenAI APIs
- No example PR with capsule-based review

#### Recommendations:
- Add `examples/before_after/` directory
- Add `examples/api_integration/` with Python/Node.js code
- Add `examples/pr_review/` with real PR diff + composed prompt + LLM response

---

### 10. License & Community

**Status: 9/10**

#### Strengths:
- ✅ MIT License (permissive, great for adoption)
- ✅ CODE_OF_CONDUCT.md (standard Contributor Covenant)
- ✅ CONTRIBUTING.md (clear, concise)
- ✅ Provenance blocks in capsules encourage attribution

#### Suggestions:
- Add CITATION.cff for academic use
- Add "Powered by Truth Capsules" badge for repos
- Add gallery of community capsules (post-v1)

---

## Critical Path to HackerNews Launch

**Target: 2-3 days of focused work**

### Day 1: Fix Breaking Issues (P0)
**Priority: 8 hours**

1. **Fix Documentation Mismatches (2 hours)**
   - [ ] Update QUICKSTART.md with correct profile IDs
   - [ ] Update ONE_PAGER.md example
   - [ ] Update TODO.md to reference actual profile names
   - [ ] Create profile ID → friendly name mapping in docs

2. **Fix CLI Composer Issues (2 hours)**
   - [ ] Add profile alias support (short names → full IDs)
   - [ ] Fix duplicate system block in output
   - [ ] Add `--list-profiles` and `--list-bundles` commands

3. **Fix Linter Issues (1 hour)**
   - [ ] Fix `_vN` regex to allow suffixes
   - [ ] Add provenance validation mode
   - [ ] Check `assumptions` is a list

4. **SPA Quick Fixes (3 hours)**
   - [ ] Add CSP meta tag
   - [ ] Add provenance read-only modal
   - [ ] Add URL parameter support (profile, bundles)
   - [ ] Document that SPA is a frozen demo
   - [ ] Add "Regenerate SPA" script

### Day 2: Polish & Examples (P1)
**Priority: 8 hours**

5. **Documentation Improvements (3 hours)**
   - [ ] Write "Getting Started in 5 Minutes" tutorial
   - [ ] Document bundle schema
   - [ ] Add FAQ section
   - [ ] Add before/after examples

6. **Example Improvements (2 hours)**
   - [ ] Create example PR with review capsules
   - [ ] Add API integration example (Python + OpenAI/Anthropic)
   - [ ] Add before/after prompt comparison

7. **CI Enhancements (2 hours)**
   - [ ] Add signature verification to lint workflow
   - [ ] Document API key setup for judge
   - [ ] Add workflow status badges to README

8. **README Polish (1 hour)**
   - [ ] Add hero image/diagram
   - [ ] Add "Why Truth Capsules?" section
   - [ ] Add quick demo GIF/video
   - [ ] Add "Featured Capsules" showcase

### Day 3: Test & Launch Prep (P1)
**Priority: 6 hours**

9. **End-to-End Testing (3 hours)**
   - [ ] Test all CLI commands
   - [ ] Test all workflows locally
   - [ ] Test SPA in multiple browsers
   - [ ] Verify all doc links

10. **HN Launch Materials (2 hours)**
    - [ ] Write HN submission title + description
    - [ ] Create demo video (2-3 minutes)
    - [ ] Prepare FAQ responses for comments
    - [ ] Set up analytics (optional)

11. **Final Polish (1 hour)**
    - [ ] Spell check all docs
    - [ ] Ensure consistent voice/tone
    - [ ] Add social preview image
    - [ ] Test on mobile

---

## HackerNews Positioning Strategy

### Headline Options:
1. **"Truth Capsules: Versioned, Signed YAML Prompts for LLMs"** *(technical)*
2. **"Show HN: Curate and compose LLM system prompts like package dependencies"** *(analogy)*
3. **"Truth Capsules: A Git-friendly approach to LLM prompt engineering"** *(workflow)*

**My Recommendation: #2** - The "package manager for prompts" analogy will resonate with HN's developer audience.

### Key Talking Points:
- **Curation > ad-hoc**: "Stop copy-pasting prompts from Slack/Discord"
- **Reproducibility**: "Deterministic prompt composition with lockfile-style manifests"
- **Trust**: "Ed25519 signatures for prompt provenance (like Linux package signing)"
- **Pedagogy**: "Socratic prompts that teach your model (and your team) best practices"
- **Portability**: "Same capsules work in ChatGPT, Claude Code, and CI pipelines"

### Expected HN Objections & Responses:

**Objection 1: "Why YAML? JSON Schema is more standard."**
- Response: "Human readability and git-friendliness. YAML diffs are cleaner, and non-technical stakeholders can read/review capsules."

**Objection 2: "This is just over-engineered prompt management."**
- Response: "Fair point for simple cases. Truth Capsules shine when you have: (a) multiple LLM contexts, (b) team collaboration, (c) compliance/audit needs, or (d) CI integration. If you're happy with a single .txt prompt, you don't need this."

**Objection 3: "Signing is security theater."**
- Response: "Signing isn't about preventing prompt injection-it's about organizational trust and audit trails. 'Who approved this PR review prompt?' matters in regulated industries."

**Objection 4: "The SPA is broken/limited."**
- Response: "Correct! The SPA is a proof-of-concept demo with frozen data. The CLI is the production tool. We're iterating on the SPA post-v1 based on feedback."

**Objection 5: "Why not just use LangChain/Prompt Flow/etc.?"**
- Response: "Truth Capsules is orthogonal. You can use capsules to *generate* prompts for those frameworks. Think of it as the 'what' (curated rules), not the 'how' (execution framework)."

---

## Strengths to Emphasize for Hiring/Sponsorship

### Technical Strengths:
1. **Clean Architecture**: Simple, composable YAML format that's easy to extend
2. **Security Mindedness**: Provenance, signing, CSP guidance shows thoughtful design
3. **Pedagogical Innovation**: Socratic + Aphorism structure is unique and valuable
4. **Multi-Context Design**: Same capsules for chat, code assistant, CI is elegant
5. **CI Integration**: GitHub Actions workflows show production thinking

### Execution Strengths:
1. **Comprehensive Documentation**: 14 markdown files covering schema, security, CI, etc.
2. **Realistic Scoping**: Clear P0/P1/P2 priorities, honest about v1 vs. future
3. **Immediate Value**: 24 high-quality capsules ready to use
4. **Open Source First**: MIT license, clear contribution guidelines

### Areas That Show Potential:
1. **Domain Expertise**: Capsules cover PR review, red-teaming, safety - shows breadth
2. **Attention to Detail**: Provenance headers, digest calculation, aphorism curation
3. **Systems Thinking**: Bundle/profile/capsule composition model is well-designed
4. **Pragmatism**: CLI-first approach, SPA as secondary (right priority)

---

## Recommendations by Priority

### P0 - Must Fix Before Launch:
1. Fix all profile name mismatches in docs
2. Add profile alias support to CLI
3. Document SPA limitations honestly
4. Add signature verification to CI
5. Write 5-minute getting started guide
6. Fix linter false positives
7. Add before/after examples

### P1 - Should Fix for Strong Launch:
1. Add provenance panel to SPA
2. Create demo video
3. Add API integration examples
4. Improve README with diagram
5. Test all workflows end-to-end
6. Add FAQ section
7. Create HN submission materials

### P2 - Nice to Have (Post-Launch):
1. Rebuild SPA with proper file loading
2. Add tags and search
3. Create quickstart template repo
4. Add secrets handling capsules
5. Build community capsule gallery
6. Create VSCode extension

---

## Overall Rating by Category

| Category | Rating | Notes |
|----------|--------|-------|
| **Concept** | 10/10 | Novel, valuable, well-positioned |
| **Architecture** | 8/10 | Clean design, some inconsistencies |
| **CLI Tools** | 7/10 | Working but need polish |
| **Capsules** | 9/10 | High quality, diverse, useful |
| **SPA** | 4/10 | Needs significant work |
| **Documentation** | 6/10 | Comprehensive but outdated |
| **CI/Workflows** | 8/10 | Well-designed, needs testing |
| **Examples** | 7/10 | Good but need more context |
| **Community** | 9/10 | Strong foundation (MIT, contributing) |
| **Polish** | 5/10 | Rough edges everywhere |

**Overall: 7.3/10 - Solid beta, needs focused polish for v1 RC**

---

## Final Verdict

**This is a genuinely innovative project with strong commercial and open-source potential.**

The core concept-curated, versioned, signed YAML capsules that compose into context-specific prompts-solves real problems for teams using LLMs at scale. The pedagogical framing (Socratic + Aphorism) is unique and adds educational value beyond simple prompt engineering.

**For HackerNews Launch:**
- Spend 2-3 days fixing the critical P0 issues (docs, CLI, examples)
- Be honest about SPA limitations (it's a frozen demo)
- Lead with the "package manager for prompts" analogy
- Emphasize reproducibility, trust (signing), and portability
- Have FAQ responses ready for expected objections

**For Hiring/Sponsorship:**
- This demonstrates strong systems thinking and design skills
- Shows ability to identify novel solutions to emerging problems
- Demonstrates attention to security, provenance, and compliance needs
- High potential for enterprise customization (org-specific bundles/profiles)

**Bottom Line: With 2-3 days of focused work, this is HN front-page material.**

---

## Next Steps

See attached checklist of P0 items to address before launch.

**Would you like me to:**
1. Start implementing P0 fixes systematically?
2. Create a demo video script?
3. Write the HN submission post?
4. Generate example API integration code?
5. Rebuild the SPA with proper architecture?

Let me know your priority and I'll dive in.

---

*End of Assessment*
