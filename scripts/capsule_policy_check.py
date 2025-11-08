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

def norm_capsule_for_digest(c):
    core = {
        "id": c.get("id"),
        "version": c.get("version"),
        "domain": c.get("domain"),
        "title": c.get("title"),
        "statement": c.get("statement"),
        "assumptions": c.get("assumptions") or [],
        "pedagogy": [{"kind": p.get("kind"), "text": p.get("text")} for p in (c.get("pedagogy") or [])],
    }
    s = json.dumps(core, sort_keys=True, ensure_ascii=False)
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

        if args.require-signature-on-approved and status == "approved":
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
