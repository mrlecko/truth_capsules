# Truth Capsules - One Pager

**What**: A curated, signed library of small YAML “truth capsules” that encode reasoning discipline, guardrails, and teaching prompts. A composer (CLI + SPA) assembles them into deterministic **SYSTEM prompts** and **JSON manifests** usable by LLMs, code assistants, and CI.

**Why it’s different**: 
- *Curation is king*: versioned, reviewable artifacts (YAML) rather than ad‑hoc prompts.
- *Trustable*: provenance header, digest, optional Ed25519 signature; CI policy gate.
- *Portable*: same capsules drive conversation, code‑assistant, and CI flows.
- *Pedagogical*: Socratic + aphorisms teach the model (and the human) the house style.

**Where it helps today**:
- **PR reviews**: Diff‑first, risk tags, deploy checklist, change‑impact prompts.
- **Red‑team & safety**: PII redaction, Plan→Verify→Answer, tool JSON contracts.
- **Agent CI**: lint + compose prompts on PR; model judge gate with labeled rubrics.

**How to try** (3 mins):
```bash
python capsule_linter.py truth-capsules-v1/capsules
python compose_capsules_cli.py --root truth-capsules-v1 --profile conversational --bundle conversation_red_team_baseline_v1 --out examples/prompt.txt --manifest examples/prompt.manifest.json
```
Open the SPA: `capsule_composer.html` and click a few bundles.

**Sponsorship / hire**:
- Looking for day‑rate work to tailor capsules to your org (CI policy, PR flows, on‑call runbooks), integrate model judges, and wire provenance signatures.
- Contact: John Macgregor - see repository provenance headers.
