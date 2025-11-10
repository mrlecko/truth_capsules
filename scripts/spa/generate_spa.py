#!/usr/bin/env python3
"""
Truth Capsules — Single-file SPA generator (golden)

• Deterministic vendor assets via unpkg (with pinned + fallback candidates)
• Optional inline embedding (with cache + strict mode)
• Robust YAML → JSON: ISO-stringify datetime/date and any oddballs
• Single render path (no duplicate logic)
"""

import argparse, json, os, sys, glob, yaml, hashlib
from datetime import datetime, date
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from jinja2 import Template

# -------------------------------
# CDN inventory (first is preferred)
# -------------------------------
UNPKG = "https://unpkg.com/"

CDN_ALTS = {
    # CSS
    "prism_css": [
        "prismjs@1.29.0/themes/prism-tomorrow.min.css",
        "prismjs/themes/prism-tomorrow.min.css",
    ],
    # JS: Prism core
    "prism_core": [
        "prismjs@1.29.0/prism.min.js",
        "prismjs@1.29.0/prism.js",
        "prismjs@1.29.0/components/prism-core.min.js",
        "prismjs/prism.js",
    ],
    # JS: Prism plugins
    "prism_yaml": [
        "prismjs@1.29.0/components/prism-yaml.min.js",
        "prismjs/components/prism-yaml.min.js",
    ],
    "prism_json": [
        "prismjs@1.29.0/components/prism-json.min.js",
        "prismjs/components/prism-json.min.js",
    ],
    # JS: Utilities
    "split_js": [
        "split.js@1.6.5/dist/split.min.js",
    ],
    "sortable_js": [
        "sortablejs@1.15.2/Sortable.min.js",
    ],
}

# -------------------------------
# Helpers
# -------------------------------

def _json_default(o):
    """Make YAML timestamps and other oddballs JSON-serializable."""
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)

def _guess_ext(key: str) -> str:
    return ".css" if "css" in key else ".js"

def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "truth-capsules-spa/1.0"})
    with urlopen(req, timeout=20) as r:
        return r.read()

def load_or_fetch_any(key: str, vendor_dir: str, offline: bool) -> bytes:
    """
    Try each CDN candidate for 'key' until one succeeds; cache to vendor_dir.
    Respects offline mode (requires cache to exist).
    """
    ensure_dir(vendor_dir)
    ext = _guess_ext(key)
    local_path = os.path.join(vendor_dir, f"{key}{ext}")

    # Cached blob wins
    if os.path.isfile(local_path):
        with open(local_path, "rb") as f:
            return f.read()

    if offline:
        raise FileNotFoundError(f"offline mode and missing {local_path}")

    last_err = None
    for path in CDN_ALTS[key]:
        url = UNPKG + path
        try:
            blob = fetch(url)
            with open(local_path, "wb") as f:
                f.write(blob)
            return blob
        except Exception as e:
            last_err = e
            continue
    raise FileNotFoundError(f"All candidates failed for {key}: {last_err}")

def embed_libs(vendor_dir: str, offline: bool):
    """
    Return (libs, digests):
      libs[key]   = inline text ('' if missing)
      digests[key]= sha256 hex or 'missing (...)'
    """
    libs, digests = {}, {}
    for key in CDN_ALTS.keys():
        try:
            blob = load_or_fetch_any(key, vendor_dir, offline)
            digests[key] = sha256_bytes(blob)
            libs[key] = blob.decode("utf-8", errors="replace")
        except Exception as e:
            libs[key] = ""
            digests[key] = f"missing ({e})"
    return libs, digests

def read_yaml(filepath: str):
    """Read YAML; attach source path and raw for provenance/debug."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()
        data = yaml.safe_load(raw)
        if isinstance(data, dict):
            data["_file"] = filepath
            data["_raw"] = raw
        return data
    except Exception as e:
        return {"__error__": str(e), "_file": filepath}

def index_llm_templates(root_dir: str):
    templates = []
    templates_dir = os.path.join(root_dir, "llm_templates")
    if not os.path.isdir(templates_dir):
        return templates
    for filepath in sorted(glob.glob(os.path.join(templates_dir, "*.yaml"))):
        data = read_yaml(filepath)
        if not isinstance(data, dict):
            continue
        required = ["id", "label", "model", "input_mode", "cmd_template"]
        if not all(f in data for f in required):
            continue
        templates.append({
            "id": data["id"],
            "label": data.get("label", data["id"]),
            "model": data["model"],
            "description": data.get("description", ""),
            "engine": data.get("engine", "llm"),
            "input_mode": data.get("input_mode", "arg"),
            "extra_flags": data.get("extra_flags", []),
            "cmd_template": data["cmd_template"],
        })
    return templates

def collect_data(root_dir: str):
    """
    Walk repo and collect capsules, bundles, profiles, schemas, and llm templates.
    Adds derived capsule['posture'] and _witness_count.
    """
    def _derive_posture(obj: dict) -> str:
        w = obj.get("witnesses")
        nonempty = False
        if isinstance(w, list):
            nonempty = len(w) > 0
        elif isinstance(w, dict):
            nonempty = len(w.keys()) > 0
        return "witnessed" if nonempty else "informational"

    capsules, bundles, profiles, schemas = {}, {}, {}, {}
    yaml_files = glob.glob(os.path.join(root_dir, "**", "*.yml"), recursive=True) + \
                 glob.glob(os.path.join(root_dir, "**", "*.yaml"), recursive=True)

    for filepath in yaml_files:
        data = read_yaml(filepath)
        if not isinstance(data, dict):
            continue

        # Profiles
        if data.get("kind") == "profile" and data.get("id"):
            profiles[data["id"]] = {
                "id": data["id"],
                "title": data.get("title", data["id"]),
                "version": data.get("version", "0.0.0"),
                "description": data.get("description", ""),
                "response": data.get("response", {}),
                "download": data.get("download", {"suggested_ext": "txt"}),
                "_file": filepath,
                "_raw": data.get("_raw", ""),
            }
            continue

        # Bundles (heuristic: has 'capsules' list but isn't a single-capsule doc)
        if ("capsules" in data and isinstance(data["capsules"], list)
            and ("id" not in data or "witnesses" not in data)):
            name = data.get("name") or os.path.splitext(os.path.basename(filepath))[0]
            bundles[name] = {
                "name": name,
                "version": data.get("version", "1.0.0"),
                "description": data.get("description", ""),
                "applies_to": data.get("applies_to", []),
                "capsules": data.get("capsules", []),
                "excludes": data.get("excludes", []),
                "priority_overrides": data.get("priority_overrides", {}),
                "order": data.get("order", []),
                "projection": data.get("projection", ""),
                "tags": data.get("tags", []),
                "notes": data.get("notes", ""),
                "env": data.get("env", {}),
                "secrets": data.get("secrets", []),
                "_file": filepath,
            }
            continue

        # Capsules (single)
        if data.get("id") and data.get("version") and data.get("domain"):
            cap = dict(data)
            cap["_file"] = filepath
            cap["posture"] = _derive_posture(cap)
            w = cap.get("witnesses")
            if isinstance(w, list):
                cap["_witness_count"] = len(w)
            elif isinstance(w, dict):
                cap["_witness_count"] = len(w.keys())
            else:
                cap["_witness_count"] = 0
            capsules[cap["id"]] = cap
            continue

        # Schemas
        if data.get("kind") == "schema" and data.get("id"):
            sch = dict(data)
            sch["_file"] = filepath
            schemas[data["id"]] = sch
            continue

    llm_templates = index_llm_templates(root_dir)
    return {
        "capsules": capsules,
        "bundles": bundles,
        "profiles": profiles,
        "schemas": schemas,
        "llm_templates": llm_templates,
    }

# -------------------------------
# Core
# -------------------------------

def generate_spa(root_dir: str,
                 template_path: str,
                 output_path: str,
                 vendor_dir: str,
                 embed_cdn: bool,
                 offline: bool,
                 strict_embed: bool):
    # Basic inputs sanity
    if not os.path.isdir(root_dir):
        raise FileNotFoundError(f"{root_dir} is not a directory")
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    print(f"📦 Collecting data from {root_dir}...")
    data = collect_data(root_dir)
    print(f"  ✓ {len(data['capsules'])} capsules")
    print(f"  ✓ {len(data['bundles'])} bundles")
    print(f"  ✓ {len(data['profiles'])} profiles")
    print(f"  ✓ {len(data['llm_templates'])} LLM templates")

    print(f"\n📄 Loading template from {template_path}...")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
    template = Template(template_content)

    print(f"\n🔧 Rendering SPA...")
    generated_at = datetime.utcnow().isoformat() + "Z"
    data_json = json.dumps(data, indent=2, ensure_ascii=False, default=_json_default)

    # Decide on asset strategy
    if embed_cdn:
        print("  ⇢ Embedding vendor libs inline…")
        libs, digests = embed_libs(vendor_dir, offline)
        for k, h in digests.items():
            print(f"    - {k}: sha256={h}")
        if strict_embed:
            missing = [k for k, v in digests.items() if str(v).startswith("missing")]
            if missing:
                raise RuntimeError(f"--strict-embed failed: missing embeds: {', '.join(missing)}")
    else:
        libs = {k: "" for k in CDN_ALTS}
        digests = {k: "skipped" for k in CDN_ALTS}

    html = template.render(
        data_json=data_json,
        generated_at=generated_at,
        prism_css_inline=libs["prism_css"],
        prism_core_inline=libs["prism_core"],
        prism_yaml_inline=libs["prism_yaml"],
        prism_json_inline=libs["prism_json"],
        split_js_inline=libs["split_js"],
        sortable_js_inline=libs["sortable_js"],
        cdn_urls={k: (UNPKG + CDN_ALTS[k][0]) for k in CDN_ALTS},  # first candidate
        digests=digests,
        inline_cdn=embed_cdn
    )

    ensure_dir(os.path.dirname(output_path) or ".")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html.encode("utf-8")) / 1024
    print(f"\n✅ Generated {output_path} ({size_kb:.1f} KB)")
    print(f"   Generated at: {generated_at}")

# -------------------------------
# CLI
# -------------------------------

def main():
    p = argparse.ArgumentParser(description="Generate single-file Truth Capsules SPA")
    p.add_argument("--root", required=True, help="Path to truth-capsules root directory")
    p.add_argument("--template", default="scripts/spa/template.html", help="Path to template.html")
    p.add_argument("--output", default="capsule_composer.html", help="Output HTML file")
    p.add_argument("--vendor-dir", default="scripts/spa/vendor", help="Where to cache vendor libs")
    p.add_argument("--embed-cdn", action="store_true", help="Inline CDN JS/CSS into the SPA")
    p.add_argument("--offline", action="store_true", help="Do not fetch; use local vendor cache only")
    p.add_argument("--strict-embed", action="store_true", help="Fail the build if any required CDN asset fails to embed")
    args = p.parse_args()

    try:
        generate_spa(
            root_dir=args.root,
            template_path=args.template,
            output_path=args.output,
            vendor_dir=args.vendor_dir,
            embed_cdn=args.embed_cdn,
            offline=args.offline,
            strict_embed=args.strict_embed,
        )
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
