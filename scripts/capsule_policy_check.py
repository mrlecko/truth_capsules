#!/usr/bin/env python3
"""
Policy gate for Truth Capsules.

Rules:
- Digest must match for ALL capsules.
- If provenance.review.status == "approved": require Ed25519 signature & valid pubkey and verify.
- Optional: branch-based enforcement via --require-signature-on-approved flag.
Exit non-zero on any violation.
"""
import os, sys, json, base64, yaml, hashlib, argparse

def canonical_json(obj):
    """Canonical JSON - deterministic ordering, no whitespace."""
    if isinstance(obj, list):
        return "[" + ",".join(canonical_json(item) for item in obj) + "]"
    elif isinstance(obj, dict):
        keys = sorted(obj.keys())
        pairs = [json.dumps(k) + ":" + canonical_json(obj[k]) for k in keys]
        return "{" + ",".join(pairs) + "}"
    else:
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))

def norm_capsule_for_digest(c):
    pedagogy = c.get("pedagogy") or []
    if isinstance(pedagogy, list):
        pedagogy = [{"kind": p.get("kind"), "text": p.get("text")} for p in pedagogy if isinstance(p, dict)]
    else:
        pedagogy = []

    core = {
        "id": c.get("id"),
        "version": c.get("version"),
        "domain": c.get("domain"),
        "title": c.get("title"),
        "statement": c.get("statement"),
        "assumptions": c.get("assumptions") if isinstance(c.get("assumptions"), list) else [],
        "pedagogy": pedagogy
    }
    s = canonical_json(core)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="path to capsules directory")
    ap.add_argument("--require-signature-on-approved", action="store_true")
    args = ap.parse_args()

    try:
        from nacl.signing import VerifyKey
        HAVE_NACL = True
    except Exception:
        HAVE_NACL = False

    errors = 0
    checked = 0
    for fn in sorted(os.listdir(args.path)):
        if not fn.endswith(".yaml"): continue
        fp = os.path.join(args.path, fn)
        try:
            c = yaml.safe_load(open(fp, "r", encoding="utf-8")) or {}
        except Exception as e:
            print(f"[error] yaml parse failed: {fn}: {e}")
            errors += 1
            continue
        checked += 1
        dig = norm_capsule_for_digest(c)
        ps = (((c.get("provenance") or {}).get("signing")) or {})
        status = ((c.get("provenance") or {}).get("review") or {}).get("status", "draft")

        if ps.get("digest") != dig:
            print(f"[error] digest mismatch: {fn}")
            errors += 1
            continue

        if args.require_signature_on_approved and status == "approved":
            if not HAVE_NACL:
                print(f"[error] approved requires signature verification but pynacl not available: {fn}")
                errors += 1
                continue
            sig = ps.get("signature"); pub = ps.get("pubkey")
            if not sig or not pub:
                print(f"[error] approved requires signature+pubkey: {fn}")
                errors += 1
                continue
            try:
                VerifyKey(base64.b64decode(pub)).verify(dig.encode("utf-8"), base64.b64decode(sig))
            except Exception as e:
                print(f"[error] signature verification failed: {fn}: {e}")
                errors += 1
                continue

    print(f"policy summary: checked={checked} errors={errors}")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
