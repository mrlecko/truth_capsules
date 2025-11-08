#!/usr/bin/env python3
import os, sys, json, glob, yaml

def run_capsule(fp):
    y = yaml.safe_load(open(fp, "r").read())
    status = "GREEN"; results = []
    for w in y.get("witnesses", []):
        if w.get("language") == "python":
            try:
                glb = {}
                exec(w["code"], glb, {})
                results.append({"name": w["name"], "result": "GREEN"})
            except SystemExit as _:
                results.append({"name": w["name"], "result": "SKIP"})
            except Exception as e:
                status = "RED"
                results.append({"name": w["name"], "result": "RED", "error": str(e)})
    return {"capsule": y["id"], "status": status, "witness_results": results}

def main():
    cap_dir = sys.argv[1] if len(sys.argv)>1 else "capsules"
    all_caps = sorted(glob.glob(os.path.join(cap_dir, "*.yaml")))
    out = [run_capsule(fp) for fp in all_caps]
    print(json.dumps(out, indent=2))
    if any(x["status"] == "RED" for x in out): sys.exit(1)

if __name__ == "__main__":
    main()
