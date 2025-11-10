#!/usr/bin/env python3
"""
Reads witness JSON (array) from stdin or from a file path argument.

Writes:
  artifacts/out/witness_<ts>.json          (verbatim input)
  artifacts/out/witness_<ts>.signed.json   (with proof block)
  artifacts/out/witness_<ts>.sig           (detached base64)

Env:
  OUT_DIR      (default: artifacts/out)
  SIGNING_KEY  (PEM private key, Ed25519; default: keys/dev_ed25519_sk.pem)
  KEY_ID       (default: dev)
"""
import sys, os, json, base64, tempfile, subprocess, hashlib, time

def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def read_input() -> tuple[str, list]:
    # Prefer argv[1] file path if provided; else stdin
    raw = ""
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        path = sys.argv[1]
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception as e:
            print(f"[sign_witness] failed to read '{path}': {e}", file=sys.stderr)
            sys.exit(2)
    else:
        try:
            raw = sys.stdin.read()
        except Exception as e:
            print(f"[sign_witness] failed to read stdin: {e}", file=sys.stderr)
            sys.exit(2)

    if not raw or not raw.strip():
        print("[sign_witness] invalid JSON: empty input", file=sys.stderr)
        sys.exit(2)

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[sign_witness] invalid JSON: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, list):
        print("[sign_witness] expected a JSON array from witness runner", file=sys.stderr)
        sys.exit(2)

    return raw, data

import subprocess
def git_sha():
    try: return subprocess.check_output(["git","rev-parse","--short","HEAD"], text=True).strip()
    except: return None

def main():
    raw, data = read_input()

    out_dir = os.environ.get("OUT_DIR", "artifacts/out")
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    base = os.path.join(out_dir, f"witness_{ts}")

    # Save raw input
    raw_path = base + ".json"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw)

    # Canonical bytes + digest
    canon = canonical_json(data)
    digest = hashlib.sha256(canon).hexdigest()

    # Sign with OpenSSL Ed25519 (raw message)
    key = os.environ.get("SIGNING_KEY", "keys/dev_ed25519_sk.pem")
    key_id = os.environ.get("KEY_ID", "dev")
    if not os.path.exists(key):
        print(f"[sign_witness] SIGNING_KEY not found: {key}", file=sys.stderr)
        sys.exit(2)

    with tempfile.NamedTemporaryFile(delete=False) as tmp_in:
        tmp_in.write(canon)
        tmp_in.flush()
        sig_bin = base + ".sig.bin"
        cmd = ["openssl", "pkeyutl", "-sign", "-inkey", key, "-rawin", "-in", tmp_in.name, "-out", sig_bin]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"[sign_witness] openssl sign failed: {e.stderr.decode('utf-8', 'ignore')}", file=sys.stderr)
            sys.exit(2)

    with open(sig_bin, "rb") as f:
        sig_b64 = base64.b64encode(f.read()).decode("ascii")
    os.replace(sig_bin, base + ".sig")

    signed_doc = {
        "results": data,
        "proof": {
            "type": "Ed25519",
            "created": ts,
            "keyId": key_id,
            "canonical": {"algo": "json-c14n-v1", "hash": "sha256", "digest": digest},
            "signature": sig_b64,
            "meta": {
                "engine": "sandbox",
                "image": os.environ.get("SANDBOX_IMAGE","truthcapsules/runner:0.1"),
                "git": git_sha(),
            }
        }
    }
    signed_path = base + ".signed.json"
    with open(signed_path, "w", encoding="utf-8") as f:
        json.dump(signed_doc, f, ensure_ascii=False, indent=2)

    print(f"[sign_witness] wrote:\n  {raw_path}\n  {signed_path}\n  {base+'.sig'}", file=sys.stderr)

if __name__ == "__main__":
    main()
