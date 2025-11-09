#!/usr/bin/env python3
import argparse, json, os, sys, glob, yaml, hashlib
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from jinja2 import Template

CDN = {
    # Pin versions for deterministic builds
    "prism_css":  ("prismjs/themes/prism-tomorrow.min.css",               "text/css"),
    "prism_core": ("prismjs@1.29.0/prism.js",                          "application/javascript"),
    "prism_yaml": ("prismjs@1.29.0/components/prism-yaml.min.js",         "application/javascript"),
    "prism_json": ("prismjs@1.29.0/components/prism-json.min.js",         "application/javascript"),
    "split_js":   ("split.js@1.6.5/dist/split.min.js",                     "application/javascript"),
    "sortable_js":("sortablejs@1.15.2/Sortable.min.js",                    "application/javascript"),
}

# --- replace the single-path CDN map with multi-candidate lists ---
UNPKG = "https://unpkg.com/"

CDN_ALTS = {
    # CSS (pin first, then unpinned fallback)
    "prism_css": [
        "prismjs@1.29.0/themes/prism-tomorrow.min.css",
        "prismjs/themes/prism-tomorrow.min.css",
    ],
    # Prism core (try minified, then non-minified, then components core, then unpinned)
    "prism_core": [
        "prismjs@1.29.0/prism.min.js",
        "prismjs@1.29.0/prism.js",
        "prismjs@1.29.0/components/prism-core.min.js",
        "prismjs/prism.js",
    ],
    # Plugins remain the same, but add unpinned fallbacks
    "prism_yaml": [
        "prismjs@1.29.0/components/prism-yaml.min.js",
        "prismjs/components/prism-yaml.min.js",
    ],
    "prism_json": [
        "prismjs@1.29.0/components/prism-json.min.js",
        "prismjs/components/prism-json.min.js",
    ],
    "split_js": [
        "split.js@1.6.5/dist/split.min.js",
    ],
    "sortable_js": [
        "sortablejs@1.15.2/Sortable.min.js",
    ],
}

def _guess_ext(key: str) -> str:
    return ".css" if "css" in key else ".js"

def fetch(url: str) -> bytes:
    from urllib.request import urlopen, Request
    req = Request(url, headers={"User-Agent": "truth-capsules-spa/1.0"})
    with urlopen(req, timeout=20) as r:
        return r.read()

def load_or_fetch_any(key: str, vendor_dir: str, offline: bool) -> bytes:
    """
    Try each candidate path until one succeeds. Cache to vendor_dir.
    """
    ensure_dir(vendor_dir)
    ext = _guess_ext(key)
    local_path = os.path.join(vendor_dir, f"{key}{ext}")

    # Use cached blob if present
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


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def read_yaml(filepath):
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

def index_llm_templates(root_dir):
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

def collect_data(root_dir):
    capsules, bundles, profiles, schemas = {}, {}, {}, {}
    yaml_files = glob.glob(os.path.join(root_dir, "**", "*.yml"), recursive=True) + \
                 glob.glob(os.path.join(root_dir, "**", "*.yaml"), recursive=True)
    for filepath in yaml_files:
        data = read_yaml(filepath)
        if not isinstance(data, dict): continue
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
            }; continue
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
                "_file": filepath
            }; continue
        if data.get("id") and data.get("version") and data.get("domain"):
            capsules[data["id"]] = data; continue
        if data.get("kind") == "schema" and data.get("id"):
            schemas[data["id"]] = data; continue
    llm_templates = index_llm_templates(root_dir)
    return {"capsules": capsules, "bundles": bundles, "profiles": profiles,
            "schemas": schemas, "llm_templates": llm_templates}

def ensure_dir(p): os.makedirs(p, exist_ok=True)

def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "truth-capsules-spa/1.0"})
    with urlopen(req, timeout=20) as r:
        return r.read()

def load_or_fetch(name: str, vendor_dir: str, offline: bool) -> bytes:
    """Load a vendor blob from disk, or fetch from unpkg and cache it."""
    # choose filename by type
    ext = ".js" if "js" in name and "css" not in name else ".css"
    local_path = os.path.join(vendor_dir, f"{name}{ext}")
    if os.path.isfile(local_path):
        with open(local_path, "rb") as f:
            return f.read()
    if offline:
        raise FileNotFoundError(f"offline mode and missing {local_path}")
    # fetch & cache
    path, _mime = CDN[name]
    url = UNPKG + path
    blob = fetch(url)
    ensure_dir(vendor_dir)
    with open(local_path, "wb") as f:
        f.write(blob)
    return blob

def embed_libs(vendor_dir: str, offline: bool):
    """Return dict of inline CSS/JS strings + digest comments."""
    libs = {}
    digests = {}
    for key in CDN.keys():
        try:
            blob = load_or_fetch(key, vendor_dir, offline)
            digests[key] = sha256_bytes(blob)
            # For CSS wrap in <style>…</style>, for JS in <script>…</script>
            if key.endswith("_css"):
                libs[key] = blob.decode("utf-8", errors="replace")
            else:
                libs[key] = blob.decode("utf-8", errors="replace")
        except (HTTPError, URLError, FileNotFoundError) as e:
            # Leave empty on failure; template will fall back to CDN tags
            libs[key] = ""
            digests[key] = f"missing ({e})"
    return libs, digests

def generate_spa(root_dir, template_path, output_path, vendor_dir, inline_cdn, offline):
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
    data_json = json.dumps(data, indent=2, ensure_ascii=False)

    libs = {k: "" for k in CDN}
    digests = {k: "" for k in CDN}
    if inline_cdn:
        print("  ⇢ Embedding vendor libs inline…")
        libs, digests = embed_libs(vendor_dir, offline)
        for k, h in digests.items():
            print(f"    - {k}: sha256={h}")

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
        inline_cdn=inline_cdn
    )


    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html.encode("utf-8")) / 1024
    print(f"\n✅ Generated {output_path} ({size_kb:.1f} KB)")
    print(f"   Generated at: {generated_at}")

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

    # verify cdn files embedded ok
    try:
        if args.embed_cdn:
            libs, digests = embed_libs(args.vendor_dir, args.offline)

            # STRICT mode: fail if any missing
            if args.strict_embed:
                missing = [k for k, v in digests.items() if str(v).startswith("missing")]
                if missing:
                    print(
                        f"❌ ERROR: --strict-embed: missing embeds: {', '.join(missing)}",
                        file=sys.stderr
                    )
                    sys.exit(2)
        else:
            libs, digests = ({k: "" for k in CDN_ALTS}, {k: "skipped" for k in CDN_ALTS})

        # Prepare render vars
        data = collect_data(args.root)
        data_json = json.dumps(data, indent=2, ensure_ascii=False)
        generated_at = datetime.utcnow().isoformat() + "Z"

        with open(args.template, "r", encoding="utf-8") as f:
            template_content = f.read()
        template = Template(template_content)

        html = template.render(
            data_json=data_json,
            generated_at=generated_at,
            prism_css_inline=libs["prism_css"],
            prism_core_inline=libs["prism_core"],
            prism_yaml_inline=libs["prism_yaml"],
            prism_json_inline=libs["prism_json"],
            split_js_inline=libs["split_js"],
            sortable_js_inline=libs["sortable_js"],
            cdn_urls={k: (UNPKG + CDN_ALTS[k][0]) for k in CDN_ALTS},
            digests=digests,
            inline_cdn=args.embed_cdn
        )

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"\n✅ Generated {args.output}")
        if args.embed_cdn:
            for k, d in digests.items():
                print(f"  • {k}: sha256={d}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


    if not os.path.isdir(args.root):
        print(f"❌ ERROR: {args.root} is not a directory", file=sys.stderr); sys.exit(1)
    if not os.path.isfile(args.template):
        print(f"❌ ERROR: Template not found: {args.template}", file=sys.stderr); sys.exit(1)
    try:
        generate_spa(args.root, args.template, args.output, args.vendor_dir, args.embed_cdn, args.offline)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
