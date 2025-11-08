#!/usr/bin/env python3
import sys, yaml, json, os

bundle_path = sys.argv[1]
out_path = sys.argv[2]

b = yaml.safe_load(open(bundle_path))
env = b.get("env", {})
modes = b.get("modes", ["static"])

gha = {
  "name": f"Capsule Gates - {b.get('name','bundle')}",
  "on": ["pull_request"],
  "jobs": {
    "gates": {
      "runs-on": "ubuntu-latest",
      "strategy": {"matrix": {"mode": modes}},
      "steps": [
        {"uses":"actions/checkout@v4"},
        {"uses":"actions/setup-python@v5","with":{"python-version":"3.11"}},
        {"run":"pip install pyyaml"},
        {"name":"Prepare fixtures","if":"matrix.mode == 'static'","run":"mkdir -p artifacts/out && cp -r artifacts/examples/. artifacts/out/ || true"},
        {"name":"Smoke prompts","if":"matrix.mode == 'smoke'","run":"python scripts/smoke_llm.py --out artifacts/out","env":{"OPENAI_API_KEY":"${{ secrets.OPENAI_API_KEY }}"} },
        {"name":"Run truth capsules","run":"python scripts/run_capsules.py capsules","env": env},
        {"name":"Upload receipts","if":"always()","uses":"actions/upload-artifact@v4","with":{"name":"receipts","path":"receipts/"}}
      ]
    }
  }
}

os.makedirs(os.path.dirname(out_path), exist_ok=True)
open(out_path,"w").write(yaml.safe_dump(gha, sort_keys=False))
print(f"Wrote {out_path}")
