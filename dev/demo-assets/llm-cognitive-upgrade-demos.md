Totally-if you want to *prove* “cognitive upgrade,” don’t just run gates. **Show A/B behavior** on the same task with and without a capsule injected into the prompt, then **score both** under a fixed rubric. Below is a turnkey “copy-paste kit” you can use in GPT-5 (or any model) and in your HTML SPA “composer”:

---

# How to demo the cognitive upgrade (Socratic + Aphorisms)

## The pattern (3 steps, <5 minutes)

1. **Baseline run** - ask the question plainly.
2. **Capsule-inflated run** - paste the “Capsule Copypasta” (statement + assumptions + Socratic Qs + aphorisms + acceptance checklist + output format).
3. **Blind judge** - paste the “A/B Judge” prompt that scores both outputs with the *same rubric*.

This isolates the effect of **Socratic prompts + aphorisms**. You’ll see: more structure, fewer omissions, cleaner evidence/citations, and better self-checks.

---

## Reusable “Capsule Copypasta” (drop into your SPA’s “Copy” button)

> Replace the bracketed fields; or wire your SPA to pull from a selected capsule YAML.

```
You are to operate under the following capsule.

STATEMENT
- [One-line normative statement. E.g., “Each factual claim must cite a credible source and sensitive data must not be exposed.”]

ASSUMPTIONS
- [List 3–5 realistic assumptions relevant to the task.]
- [Assumption 2]
- [Assumption 3]

SOCrATIC QUESTIONS (answer briefly, before drafting)
1) What is the precise objective and success criterion?
2) What key assumptions must hold true?
3) What plan will you follow (3–5 steps)?
4) What evidence will you produce, and how will you verify it?
5) What could make this wrong, and how would you detect it?

APHORISMS (apply as you work)
- One failing test beats ten opinions.
- Show me your plan before your answer.
- Cite it, or it didn’t happen.
- Prefer reversible steps; minimize blast radius.

ACCEPTANCE CHECKLIST (you MUST satisfy all)
- Includes: Objective, Assumptions, Plan, Evidence, Final Answer.
- Provides ≥1 explicit citation (title + URL) for factual claims.
- Avoids disclosing PII or secrets; redact if present.
- Evidence includes ≥1 item with ≥10 characters (not just “OK”).
- End with a Self-Check where you tick off each item as PASS/FAIL.

OUTPUT FORMAT (use these section headers, in this exact order)
Objective:
Assumptions:
Plan:
Evidence:
Final Answer:
Self-Check:
```

---

# Three A/B demos you can run by copy-paste

Each demo includes: (A) **Baseline Prompt**, (B) **Capsule-inflated Prompt** (paste the copypasta with fields filled), (C) **A/B Judge** to score both answers.

## Demo 1 - “Citations + PII hygiene” on a short factual answer

**A) Baseline Prompt (paste first):**

```
Q: What caused the Therac-25 accidents? Answer in 5–8 sentences.
```

**B) Capsule-inflated Prompt (paste second):**
Use the “Capsule Copypasta” with these quick fills:

* STATEMENT: “Each factual claim must cite a credible source and sensitive data must not be exposed.”
* ASSUMPTIONS: “You have general historical knowledge; you can cite web sources you’ve seen before; you will avoid any email/phone-like strings.”
* SOCrATIC: (keep the 5 standard questions)
* APHORISMS: (as given)
* CHECKLIST: (as given)

**C) A/B Judge (paste third, with both model outputs pasted into A: and B:)**

```
You are a strict rubric judge. Score two answers (A) and (B) to the same question using this rubric (0–5 each; total /25):

1) Structure completeness (Objective, Assumptions, Plan, Evidence, Final Answer)
2) Evidence quality (at least one citation with title + URL; relevance)
3) PII hygiene (no emails/phones/secrets or they are explicitly redacted)
4) Specificity/precision (concrete claims vs vague statements)
5) Self-Check quality (explicit PASS/FAIL against checklist)

Return a table:
| Criterion | A score | B score | Notes |
Then a final line: Verdict: A or B (tie if equal).
```

**What you’ll observe:** The **capsule run** reliably includes the five sections, at least one citation, explicit self-check, and avoids PII patterns. Baseline often omits a section or forgets to cite.

---

## Demo 2 - “PR Review Risk & Change Impact” on a tiny diff

**A) Baseline Prompt:**

```
You're reviewing a pull request. Summarize risks and change impact. Here is the diff:

- Added logging to retry loop; increased retries from 3 to 8; default timeout lowered from 10s to 5s.
- Moved token refresh to a background task.

Return your review.
```

**B) Capsule-inflated Prompt:**

* STATEMENT: “Every PR review must identify blast radius, reversibility, and test hints; no hand-waving.”
* ASSUMPTIONS: “It’s a backend service; SLAs matter; logs cost money; retries can amplify failure.”
* (Keep standard Socratic + Aphorisms)
* ADD one more Aphorism for this demo: “Prefer reversible steps; roll forward > rollback only when safe.”
* Acceptance: include “Risk Tags: [latency][cost][reliability][security] present/not present” and “Test Hints.”

**C) A/B Judge:**

```
Score answers on:
1) Risk tags coverage (latency, cost, reliability, security)
2) Blast radius reasoning and reversibility
3) Concrete test hints tied to the diff
4) Specificity (numbers, parameters) and actionability
5) Self-Check quality

Return the scoring table and a short verdict.
```

**What you’ll observe:** The capsule run annotates risks, proposes concrete tests (e.g., “simulate token expiry + 5s timeout”), and shows reversibility; baseline is more generic.

---

## Demo 3 - “5-Step Problem Solving” on an ops incident

**A) Baseline Prompt:**

```
Our API error rate spiked to 7% between 02:00–03:00 UTC after a deploy. Draft a resolution plan.
```

**B) Capsule-inflated Prompt:**

* STATEMENT: “Operational responses must include objective, assumptions, plan, evidence, and summary; verify the plan before declaring success.”
* ASSUMPTIONS: “Deploy occurred ≤30 min before spike; we have metrics/logs; we can do a canary.”
* (Keep standard Socratic + Aphorisms)
* Acceptance tweak: include “backtest” (simulate plan against a simple counterfactual: “If retries were at 8 and timeout 5s, would errors drop or climb?”)

**C) A/B Judge:**

```
Score answers on:
1) 5-step completeness (objective, assumptions, plan, evidence, summary)
2) Backtest presence (simulate or reason about the counterfactual)
3) Risk mitigation & reversibility
4) Evidence quality (metrics/logs described, not hand-wavy)
5) Self-Check quality
```

**What you’ll observe:** The capsule run proposes a **reversible** plan (e.g., “rollback retry bump; restore 10s timeout; canary 10%”) and performs a simple **backtest** in text; baseline often declares a plan without verification.

---

# Optional: “One-paste judge” for live demos

If you want zero navigation overhead, use this single prompt **after** collecting A and B:

```
Act as a strict double-blind judge. You will receive two answers (A and B) produced by different prompting strategies to the same question. Use the rubric:

- Structure completeness (Objective, Assumptions, Plan, Evidence, Final Answer)
- Evidence quality (≥1 citation, relevance)
- Specificity/precision
- Risk/reversibility (if applicable)
- Self-Check quality

Score each item 0–5. Return:

1) A vs B scoring table with one-line notes per criterion.
2) A final verdict line: “Verdict: A wins | B wins | Tie”.
```

---

# How to wire this into your SPA composer

* Add three **Copy** buttons for any selected capsule:

  1. **Copy Baseline** (you drop in the raw question)
  2. **Copy Capsule** (injects the Capsule Copypasta with the capsule’s `statement`, `assumptions`, `pedagogy` split into Socratic/Aphorisms, and a standard checklist/output format)
  3. **Copy Judge** (the rubric prompt above)

* Optional toggle: **“Include Acceptance Checklist”** (on/off).

* Optional toggle: **“Use Problem-Solving 5-Pack”** (prepopulates the 5 canonical Socratic Qs).

This keeps the YAML ↔ prompt path **one-way** (as you wanted) and makes the cognitive upgrade **visually undeniable** in a live screen-share.

---

## Why this convincingly demonstrates the upgrade

* **Same task, same model, only the capsule changes.**
* **Observable deltas**: more structure, explicit assumptions, real citations, reversible plans, and a self-check.
* **Third-party judging**: an impartial rubric scores both outputs-no hand-waving.

If you want, I can generate capsule-specific Copypasta blocks for a few of your existing YAMLs (e.g., `llm.citation_required_v1`, `llm.pr_change_impact_v1`, `pedagogy.problem_solving_v1`) so you can copy them directly into the SPA.
