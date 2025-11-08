
#!/usr/bin/env python3
# See README: requires pynacl for real signing; otherwise warns.
import os, sys, argparse, base64, yaml
try:
    from nacl.signing import SigningKey
    HAVE_NACL = True
except Exception:
    HAVE_NACL = False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="dir of capsules")
    ap.add_argument("--key", help="ed25519 private key (base64)")
    ap.add_argument("--key-id", default="demo")
    ap.add_argument("--pub", help="ed25519 public key (base64)")
    args = ap.parse_args()
    if not os.path.isdir(args.path): 
        print("path must be a directory"); sys.exit(2)
    for fn in os.listdir(args.path):
        if not fn.endswith(".yaml"): continue
        fp = os.path.join(args.path, fn)
        data = yaml.safe_load(open(fp,"r",encoding="utf-8"))
        s = (data.get("provenance") or {}).get("signing") or {}
        digest = (s.get("digest") or "").encode("utf-8")
        if not digest:
            print("[skip] no digest", fn); continue
        if not HAVE_NACL:
            print("[warn] pynacl not installed; cannot sign", fn); continue
        sk = SigningKey(base64.b64decode(args.key))
        sig = sk.sign(digest).signature
        s["signature"] = base64.b64encode(sig).decode("ascii")
        s["method"] = "ed25519"
        s["key_id"] = args.key_id if hasattr(args,"key_id") else "demo"
        if args.pub: s["pubkey"] = args.pub
        data.setdefault("provenance", {})["signing"] = s
        yaml.safe_dump(data, open(fp,"w",encoding="utf-8"), sort_keys=False, allow_unicode=True)
        print("[ok] signed", fn)

if __name__ == "__main__":
    main()
