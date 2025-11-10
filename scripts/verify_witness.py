#!/usr/bin/env python3
import os, sys, json, tempfile, subprocess, hashlib

def canonical_json(obj)->bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def main():
    if len(sys.argv) < 3:
        print("usage: verify_witness.py SIGNED_JSON PUBLIC_KEY_PEM", file=sys.stderr)
        sys.exit(2)
    signed_path, pubkey = sys.argv[1], sys.argv[2]
    with open(signed_path, "r", encoding="utf-8") as f:
        signed = json.load(f)
    results = signed["results"]
    proof = signed["proof"]
    canon = canonical_json(results)
    want = proof["canonical"]["digest"]
    have = hashlib.sha256(canon).hexdigest()
    if have != want:
        print("[verify] FAIL: digest mismatch", file=sys.stderr)
        sys.exit(1)

    sig_b64 = proof["signature"]
    with tempfile.NamedTemporaryFile(delete=False) as msg, tempfile.NamedTemporaryFile(delete=False) as sig:
        msg.write(canon); msg.flush()
        import base64; sig.write(base64.b64decode(sig_b64)); sig.flush()
        # Ed25519 raw verify on canonical bytes
        cmd = ["openssl","pkeyutl","-verify","-pubin","-inkey",pubkey,"-rawin","-in",msg.name,"-sigfile",sig.name]
        ok = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    print( "OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
