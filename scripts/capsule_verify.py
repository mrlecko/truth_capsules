
#!/usr/bin/env python3
import os, sys, json, base64, yaml, hashlib
try:
    from nacl.signing import VerifyKey
    HAVE_NACL = True
except Exception:
    HAVE_NACL = False

def norm(c):
    core = {"id":c.get("id"),"version":c.get("version"),"domain":c.get("domain"),
            "title":c.get("title"),"statement":c.get("statement"),
            "assumptions":c.get("assumptions") or [],
            "pedagogy":[{"kind":p.get("kind"),"text":p.get("text")} for p in (c.get("pedagogy") or [])]}
    import json; s=json.dumps(core, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def main():
    path = sys.argv[1] if len(sys.argv)>1 else "./truth-capsules-v1/capsules"
    ok=0; bad=0
    for fn in os.listdir(path):
        if not fn.endswith(".yaml"): continue
        fp = os.path.join(path, fn)
        c = yaml.safe_load(open(fp,"r",encoding="utf-8")) or {}
        dig = norm(c)
        s = ((c.get("provenance") or {}).get("signing") or {})
        if s.get("digest") != dig:
            print("[digest-mismatch]", fn); bad+=1; continue
        if HAVE_NACL and s.get("signature") and s.get("pubkey"):
            try:
                VerifyKey(base64.b64decode(s["pubkey"])).verify(dig.encode("utf-8"), base64.b64decode(s["signature"]))
                print("[ok] sig", fn); ok+=1
            except Exception as e:
                print("[bad-signature]", fn, e); bad+=1
        else:
            print("[ok] digest-only", fn); ok+=1
    print("summary ok=", ok, "bad=", bad)
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
