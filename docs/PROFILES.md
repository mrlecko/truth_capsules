# Profiles

Profiles capture **execution context** and response norms.

Examples:
- `conversation_pedagogy_v1` - pedagogy-first, explains method, allows light style.
- `code_assistant_baseline_v1` - stricter JSON/tool discipline, short answers.
- `ci_nonllm_baseline_v1` - deterministic outputs; no calls to external models.
- `ci_llm_judge_v1` - composes a judge profile with a scoring rubric.

The composer uses: Profile + Bundles + Capsules → **SYSTEM** prompt block.
