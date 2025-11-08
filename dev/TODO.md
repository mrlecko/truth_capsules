
# Truth Capsules - v1 Sponsorship Demo TODO

Goal: a sensible, polished **v1** that proves value quickly (hire/sponsorship bait). Not feature-complete - but credible, safe, and demonstrably useful.

| ID | Priority | In v1? | Area | Item | Description | Owner | Status |
|---|---|---:|---|---|---|---|---|
| P0-01 | P0 | Yes | Spec | **Capsule schema v1** | Freeze a minimal schema (YAML keys + semantics) and examples. | JM | DONE |
| P0-02 | P0 | Yes | Linter | **Enforce schema v1** | Linter requires id, version, domain, statement, provenance block; clean errors. Enhanced with unicode detection, strict mode, assumptions validation. | JM | DONE |
| P0-03 | P0 | Yes | Provenance | **Provenance header** | author/org/license/source_url/created/updated/review/signing/digest. | JM | DONE |
| P0-04 | P0 | Yes | CLI | **Composer CLI** | Build prompt + manifest from profile + bundles; deterministic order. Enhanced with profile aliases, --list-profiles/--list-bundles, fixed duplicate system block. | JM | DONE |
| P0-05 | P0 | Yes | CI | **Workflows: lint & compose** | GitHub Actions: capsules-lint + capsules-compose (artifacts). | JM | DONE |
| P0-06 | P0 | Yes | SPA | **YAML Preview Modal** | View + copy capsule YAML safely; sanitize. | JM | DONE |
| P0-07 | P0 | Yes | SPA | **Safe load & sanitization** | Strict text rendering, escape HTML, basic CSP note in README. | JM | TODO |
| P0-08 | P0 | Yes | Bundles | **Red Team bundle** | Adversarial eval (counterfactuals, assumptions→tests, bias audit). | JM | DONE |
| P0-09 | P0 | Yes | Bundles | **PR Review mini-bundle** | Diff-first, risk tags, test hints, deploy checklist, change impact. | JM | DONE |
| P0-10 | P0 | Yes | Capsules | **PII Redaction Guard** | Don’t output raw PII; placeholders or abstain. | JM | DONE |
| P0-11 | P0 | Yes | Capsules | **Tool JSON Contract** | Enforce function/JSON argument schema before tool calls. | JM | DONE |
| P0-12 | P0 | Yes | Docs | **Examples/CI README** | How to lint/compose locally + workflows explanation. | JM | DONE |
| P0-16 | P0 | Yes | Capsules | **Unicode escape fixes** | Fix \\u escape sequences (e.g., \\u2265 → ≥) in 13 capsules. Add fix_unicode_escapes.py tool. | JM | DONE |
| P0-17 | P0 | Yes | Docs | **Profile alias docs** | Document profile aliases and create PROFILES_REFERENCE.md with examples. | JM | DONE |
| P0-18 | P0 | Yes | Docs | **QUICKSTART fix** | Update QUICKSTART.md with correct profile IDs/aliases and working examples with Claude/OpenAI. | JM | DONE |
| P0-19 | P0 | Yes | Docs | **ONE_PAGER fix** | Update ONE_PAGER.md with correct profile aliases. | JM | DONE |
| P0-13 | P0 | Yes | SPA | **Drag to reorder (fixed)** | Drag-and-drop works with correct index calc; logs removed. | JM | DONE |
| P0-14 | P0 | Yes | SPA | **Bundle clearing (fixed)** | Removing a bundle clears its capsules from selection. | JM | DONE |
| P0-15 | P0 | Yes | SPA | **Left-pane width fix** | Remove horizontal scrollbar; responsive layout. | JM | DONE |
| P1-01 | P1 | Yes | Security | **CSP & static hosting guide** | Recommend headers/CSP and static host patterns to avoid XSS. | JM | FOR REVIEW |
| P1-02 | P1 | Yes | Linter | **Provenance gating** | Fail CI if `review.status=approved` is missing on release branches. Implemented via --strict flag. | JM | DONE |
| P1-03 | P1 | Yes | CI | **Signature verification step** | Optional ed25519 verification for approved capsules. | JM | TODO |
| P1-04 | P1 | Yes | CLI | **Author/license banner** | Surface provenance banner in composed prompt. | JM | DONE |
| P1-05 | P1 | Yes | Docs | **LICENSE + CONTRIBUTING + CoC** | Add MIT LICENSE file, CONTRIBUTING.md, CODE_OF_CONDUCT.md. | JM | FOR REVIEW |
| P1-06 | P1 | Yes | Profiles | **Context profiles** | Ship baseline profiles: conversation, code-assistant, ci (nonLLM & LLM-judge). | JM | DONE |
| P1-07 | P1 | Yes | Capsules | **Secrets handling** | “Don’t echo secrets”, “ask for minimal artifact”, “mask-by-default”. | JM | TODO |
| P1-08 | P1 | Yes | Capsules | **Retrieval & citation** | Strict citation-required variant + abstain policy. | JM | DONE |
| P1-09 | P1 | Yes | Examples | **Fixtures & goldens** | Minimal deterministic fixtures for judge capsules & PR bundle. | JM | TODO |
| P1-10 | P1 | Yes | CI | **PR comment bot** | Action that posts composed prompt / judge score on PR. | JM | TODO |
| P1-11 | P1 | Yes | SPA | **Provenance panel** | Modal to show provenance JSON + copy buttons. | JM | TODO |
| P1-12 | P1 | Yes | SPA | **Markdown export** | Rendered markdown compose/preview, copy/export. | JM | DONE |
| P1-13 | P1 | Yes | Search | **Capsule search & tags** | Filter by domain/tags/text. | JM | TODO |
| P1-14 | P1 | Yes | Tags | **Tags in capsules** | Add `tags: [...]` (e.g., risk, pedagogy, ops, pr). Update linter. | JM | TODO |
| P1-15 | P1 | Yes | Docs | **Quickstart repo template** | “Start here” template with bundles, profiles, CI ready. | JM | FOR REVIEW |
| P1-16 | P1 | Yes | Capsules | **SQL/tool safety** | Plan→execute for SQL/code tools; guardrails & dry-run option. | JM | TODO |
| P1-17 | P1 | Yes | Capsules | **Risk acceptance** | Document risk decisions w/ owner, expiry, revisit date. | JM | TODO |
| P1-18 | P1 | Yes | Capsules | **Deprecated handling** | Capsule state & migration notes; linter warns. | JM | TODO |
| P2-01 | P2 | No | Packaging | **PyPI package** | Ship `capsule-linter` and `capsule-compose` CLIs on PyPI. | JM | DEFER |
| P2-02 | P2 | No | DevEx | **Devcontainer / Docker** | One-command dev environment with pinned deps. | JM | DEFER |
| P2-03 | P2 | No | SPA | **Signer UI** | In-browser signing (only with explicit user key); likely out-of-scope. | JM | DEFER |
| P2-04 | P2 | No | SPA | **Full-text search** | Client-side index for fast search. | JM | DEFER |
| P2-05 | P2 | No | Provenance | **Transparency registry** | Public listing of approved, signed capsules. | JM | DEFER |
| P2-06 | P2 | No | Testing | **Playwright e2e** | Automated UI flows for the SPA. | JM | DEFER |
| P2-07 | P2 | No | A11y | **Accessibility pass** | Keyboard navigation, ARIA roles, color contrast. | JM | DEFER |
| P2-08 | P2 | No | Intl | **i18n** | Localization hooks and translation docs. | JM | DEFER |
| P2-09 | P2 | No | IDE | **VSCode helper** | Compose prompts and lint in-editor. | JM | DEFER |
| P2-10 | P2 | No | CI | **Multi-provider judge** | Hooks for Anthropic, OpenAI, local evals; leakage guards. | JM | DEFER |
| P2-11 | P2 | No | Lockfiles | **Bundle lockfile** | Record exact capsule versions/digests for reproducible runs. | JM | DEFER |
| P2-12 | P2 | No | Migrations | **Schema migration tool** | v1→v2 converter, with diffs and safety checks. | JM | DEFER |
| P2-13 | P2 | No | Perf | **Cache compose** | Cache composed outputs by bundle/profile hash. | JM | DEFER |
| P2-14 | P2 | No | Docs | **Website / landing** | Simple docs site + sponsor page. | JM | DEFER |
| P2-15 | P2 | No | Outreach | **Sponsor one-pager** | Value prop, use cases, pricing for sponsorship. | JM | DEFER |
| P2-16 | P2 | No | Metrics | **Adoption telemetry (opt-in)** | Strictly anonymous counts of compose/lint usage. | JM | DEFER |
| P2-17 | P2 | No | Governance | **Capsule review workflow** | Lightweight RFC / approval process. | JM | DEFER |
| P2-18 | P2 | No | Examples | **More domains** | Data QA bundle, on-call runbooks, incident write-up templates. | JM | DEFER |
| P2-19 | P2 | No | Capsules | **Judge leakage guard** | Separate “work” vs “grade” prompts; randomized rubric phrasing. | JM | DEFER |
| P2-20 | P2 | No | Profiles | **Org-level profiles** | Opinionated presets per org; inheritance/overrides. | JM | DEFER |

**Legend**  
- Priority: **P0** (must-have for v1), **P1** (nice-to-have for v1), **P2** (post‑v1).  
- Status: TODO / IN PROGRESS / DONE / DEFER.  
- Owner defaults to **JM** (can be adjusted).

## Notes
- v1 objective: demonstrate **curated, composable, signed** capsules; show **conversation**, **code assistant**, and **CI** flows; ship **two compelling bundles** (Red Team, PR Review) and **safe SPA**.
- Signing: CLI scripts provided; integrate verification into CI (P1-03). Keep private keys out of repo.
- Sponsorship pitch: focus on **curation is king**, reproducibility, and instant policy onboarding.