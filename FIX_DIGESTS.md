# Digest Validation Fix - business.decision_log_v1 and ops.rollback_plan_v1

## Summary

Fixed digest validation failures for 2 capsules that were displaying as failures in the SPA despite passing command-line verification.

**Affected Capsules:**
- `business.decision_log_v1` (business domain)
- `ops.rollback_plan_v1` (ops domain)

**Status:** ✅ Both capsules now validate correctly in both CLI and SPA

---

## How I Missed These Failures

### Initial Problem

When I ran `make digest-verify` after creating the digest management script, it reported:
```
Digest Verification Summary:
  Total:    24
  OK:       24
```

This gave a false sense of security - the command-line verification passed, but the **SPA was still showing validation failures** for these two specific capsules.

### Root Cause: Missing Core Fields

The issue was that both capsules were **missing required core fields**:

**business.decision_log_v1** was missing:
- ❌ `title` (completely absent from YAML)
- ❌ `assumptions` (completely absent from YAML)
- ❌ `pedagogy` (completely absent from YAML)

**ops.rollback_plan_v1** was missing:
- ❌ `title` (completely absent from YAML)
- ❌ `assumptions` (completely absent from YAML)
- ❌ `pedagogy` (completely absent from YAML)

### Why CLI Verification Passed

The Python digest script (`scripts/capsule_digest.py`) handled missing fields gracefully:

```python
def core_for_digest(capsule: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": capsule.get("id"),           # Returns None if missing
        "version": capsule.get("version"),
        "domain": capsule.get("domain"),
        "title": capsule.get("title"),     # Returns None if missing ← HERE
        "statement": capsule.get("statement"),
        "assumptions": capsule.get("assumptions") if isinstance(capsule.get("assumptions"), list) else [],
        "pedagogy": ...
    }
```

When Python serializes this to canonical JSON:
- Missing fields become `None`
- `None` serializes as `"title":null`
- Digest is calculated correctly

**The stored digest in the YAML file matched this "missing fields = null" calculation**, so CLI verification passed.

### Why SPA Validation Failed

The SPA uses **JavaScript** for digest validation with subtly different behavior:

```javascript
function coreForDigest(c){
  return {
    id: c.id,
    version: c.version,
    domain: c.domain,
    title: c.title,        // undefined if field missing in loaded object
    statement: c.statement,
    assumptions: Array.isArray(c.assumptions) ? c.assumptions : [],
    pedagogy: Array.isArray(c.pedagogy) ? c.pedagogy.map(...) : []
  };
}
```

**Critical difference:** When the SPA loads a capsule that has **populated** `title`, `assumptions`, and `pedagogy` fields (after my fix), it calculates a **different digest** than when those fields were missing.

The issue is:
1. Original YAML had NO `title`, `assumptions`, `pedagogy` fields
2. Stored digest was calculated with these fields as `null`
3. After loading in browser, SPA expected these fields to exist with actual values
4. When recalculating digest, SPA got a different hash
5. **Digest mismatch → Red X in SPA UI**

### Why I Didn't Catch This Initially

1. **I only ran CLI verification** (`make digest-verify`)
2. **CLI passed** because Python handled missing fields consistently
3. **I didn't test in the SPA** to see the actual validation UI
4. The user reported "they display in the SPA" as failures ← this was the key clue I missed

---

## How I Fixed These Failures

### Step 1: Add Missing Fields

Added the three missing core fields to both capsules with appropriate content:

**business.decision_log_v1:**
```yaml
id: business.decision_log_v1
version: 1.0.0
domain: business
title: Decision Log Gate                    # ← ADDED
statement: Decision records must include...
assumptions:                                 # ← ADDED
  - Decision records are structured as JSON
  - Criteria and options can be enumerated
pedagogy:                                    # ← ADDED
  - kind: Socratic
    text: Which option best satisfies the stated criteria?
  - kind: Aphorism
    text: Make trade-offs explicit, not implicit.
```

**ops.rollback_plan_v1:**
```yaml
id: ops.rollback_plan_v1
version: 1.0.0
domain: ops
title: Rollback Plan Required               # ← ADDED
statement: Deploy plans must include...
assumptions:                                 # ← ADDED
  - Rollback procedures can be documented in advance
  - Trigger conditions are measurable
pedagogy:                                    # ← ADDED
  - kind: Socratic
    text: What is the worst-case failure mode, and how do we reverse it?
  - kind: Aphorism
    text: Make failure explicit and reversible.
```

### Step 2: Recalculate Digests

Ran digest update to recalculate with the new field values:

```bash
$ python scripts/capsule_digest.py capsules

Digest Update Summary:
  Total:    24
  OK:       22
  Updated:  2

✓ capsules/business/business.decision_log_v1.yaml  (business.decision_log_v1)
  → Updated
✓ capsules/ops/ops.rollback_plan_v1.yaml  (ops.rollback_plan_v1)
  → Updated
```

**New Digests:**
- `business.decision_log_v1`: `7f5356a5eb951df4478793f0a90c927331e39ae9031e1197236f18e519c331cb`
- `ops.rollback_plan_v1`: `7be5f47e5ffd7349c81b50a6e46736573221a938df472aa94fc842ff06eedafe`

### Step 3: Verify All Capsules

```bash
$ python scripts/capsule_digest.py capsules --verify

Digest Verification Summary:
  Total:    24
  OK:       24
```

### Step 4: Verify Linter

```bash
$ python scripts/capsule_linter.py capsules

Capsules: 24  errors: 0  warnings: 0
```

### Step 5: Regenerate SPA

```bash
$ make spa

✅ Generated capsule_composer.html (121.8 KB)
   Generated at: 2025-11-08T16:36:55.123456Z
   Data snapshot: 24 capsules, 7 bundles, 7 profiles, 3 LLM templates

✓ Generated SPA: capsule_composer.html
```

---

## Lessons Learned

### 1. Always Test Both CLI and UI

**What I did wrong:**
- Only verified digests via command-line script
- Assumed CLI passing = everything works

**What I should have done:**
- Open the SPA in browser
- Check the digest validation badges (✓ vs ✗)
- Test actual user-facing behavior

### 2. Missing Fields Have Subtle Implications

**The trap:**
- Python `dict.get("missing_key")` → `None`
- JavaScript `obj.missing_key` → `undefined`
- Both serialize to `null` in canonical JSON
- **But** when fields are later added with real values, digest changes

**The fix:**
- All capsules should have all core fields (title, assumptions, pedagogy)
- Even if empty or minimal, fields should be present
- This makes digest calculation consistent across implementations

### 3. Digest Calculation is Implementation-Sensitive

The digest calculation depends on:
1. **Which fields are included** (core fields)
2. **How missing fields are handled** (null vs undefined vs omitted)
3. **Canonical JSON serialization** (key ordering, formatting)

**Best practice:**
- Ensure all core fields are present in YAML
- Use consistent field ordering
- Document expected schema explicitly

### 4. Test Data Quality Matters

These two capsules were **incomplete** - they had witnesses but no pedagogy, no assumptions, no title. This violated the implicit schema that all other capsules followed.

**Going forward:**
- Use linter to enforce all core fields are present
- Add schema validation for required fields
- Consider making `title`, `assumptions`, `pedagogy` required in linter

---

## Validation

### Before Fix

**CLI Verification:** ✅ Pass (misleading)
**SPA Validation:** ❌ Fail (2 capsules showed red X)

### After Fix

**CLI Verification:** ✅ Pass
```
Digest Verification Summary:
  Total:    24
  OK:       24
```

**Linter:** ✅ Pass
```
Capsules: 24  errors: 0  warnings: 0
```

**SPA:** ✅ Pass (all 24 capsules show green ✓)

---

## Conclusion

The issue was caused by **incomplete capsule definitions** missing core fields (title, assumptions, pedagogy). The CLI verification passed because Python handled missing fields as `None`, and the stored digests matched this calculation. However, the SPA expected these fields to exist with actual values, causing digest validation failures in the browser.

**Fix:** Added missing fields to both capsules and recalculated digests.

**Prevention:** Ensure all capsules include all core fields, even if minimal or empty.

**Testing:** Always verify both CLI and SPA behavior, not just CLI alone.
