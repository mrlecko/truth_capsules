#!/usr/bin/env python3
"""
Generate Truth Capsules SPA with embedded data.

This script loads capsules, bundles, and profiles from YAML files and
embeds them into a static HTML file for easy distribution and hosting.

Usage:
    python generate_spa.py --root ../truth-capsules-v1 --output capsule_composer.html

The generated HTML is a self-contained snapshot viewer with data frozen
at generation time. To refresh with latest capsules, regenerate this file.
"""
import argparse
import json
import os
import sys
import glob
import yaml
from datetime import datetime
from jinja2 import Template


def read_yaml(filepath):
    """Load and parse a YAML file with error handling."""
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
    """
    Load LLM command templates from llm_templates/ directory.

    Args:
        root_dir: Path to project root directory

    Returns:
        list of template dicts with id, label, model, etc.
    """
    templates = []
    templates_dir = os.path.join(root_dir, "llm_templates")

    if not os.path.isdir(templates_dir):
        return templates

    yaml_files = sorted(glob.glob(os.path.join(templates_dir, "*.yaml")))

    for filepath in yaml_files:
        try:
            data = read_yaml(filepath)
            if not isinstance(data, dict):
                continue

            # Validate required fields
            required = ["id", "label", "model", "input_mode", "cmd_template"]
            if not all(field in data for field in required):
                print(f"  ⚠ Skipping {os.path.basename(filepath)}: missing required fields")
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
        except Exception as e:
            print(f"  ⚠ Error loading {os.path.basename(filepath)}: {e}")
            continue

    return templates


def collect_data(root_dir):
    """
    Collect all capsules, bundles, and profiles from the root directory.

    Args:
        root_dir: Path to truth-capsules-v1 directory

    Returns:
        dict with keys: capsules, bundles, profiles, schemas, llm_templates
    """
    capsules = {}
    bundles = {}
    profiles = {}
    schemas = {}

    # Find all YAML files recursively
    yaml_files = (
        glob.glob(os.path.join(root_dir, "**", "*.yml"), recursive=True) +
        glob.glob(os.path.join(root_dir, "**", "*.yaml"), recursive=True)
    )

    for filepath in yaml_files:
        data = read_yaml(filepath)
        if not isinstance(data, dict):
            continue

        # Identify profiles by 'kind: profile'
        if data.get("kind") == "profile" and data.get("id"):
            profile_id = data["id"]
            profiles[profile_id] = {
                "id": profile_id,
                "title": data.get("title", profile_id),
                "version": data.get("version", "0.0.0"),
                "description": data.get("description", ""),
                "response": data.get("response", {}),
                "download": data.get("download", {"suggested_ext": "txt"}),
                "_file": filepath,
                "_raw": data.get("_raw", "")
            }
            continue

        # Identify bundles by presence of 'capsules' list
        # (but not if it's a capsule itself with witnesses)
        if (
            "capsules" in data and
            isinstance(data.get("capsules"), list) and
            ("id" not in data or "witnesses" not in data)
        ):
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
            }
            continue

        # Identify capsules by presence of 'id', 'version', 'domain'
        if data.get("id") and data.get("version") and data.get("domain"):
            capsule_id = data["id"]
            capsules[capsule_id] = data
            continue

        # Identify schemas by 'kind: schema'
        if data.get("kind") == "schema" and data.get("id"):
            schema_id = data["id"]
            schemas[schema_id] = data
            continue

    # Load LLM templates
    llm_templates = index_llm_templates(root_dir)

    return {
        "capsules": capsules,
        "bundles": bundles,
        "profiles": profiles,
        "schemas": schemas,
        "llm_templates": llm_templates
    }


def generate_spa(root_dir, template_path, output_path):
    """
    Generate the SPA HTML file with embedded data.

    Args:
        root_dir: Path to truth-capsules-v1 directory
        template_path: Path to template.html
        output_path: Path for generated HTML output
    """
    print(f"📦 Collecting data from {root_dir}...")
    data = collect_data(root_dir)

    print(f"  ✓ {len(data['capsules'])} capsules")
    print(f"  ✓ {len(data['bundles'])} bundles")
    print(f"  ✓ {len(data['profiles'])} profiles")
    print(f"  ✓ {len(data['llm_templates'])} LLM templates")

    # Load template
    print(f"\n📄 Loading template from {template_path}...")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    template = Template(template_content)

    # Render with data
    print(f"\n🔧 Rendering SPA...")
    generated_at = datetime.utcnow().isoformat() + "Z"

    # Convert data to JSON string for embedding
    data_json = json.dumps(data, indent=2, ensure_ascii=False)

    html = template.render(
        data_json=data_json,
        generated_at=generated_at
    )

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    file_size_kb = len(html.encode('utf-8')) / 1024
    print(f"\n✅ Generated {output_path} ({file_size_kb:.1f} KB)")
    print(f"   Generated at: {generated_at}")
    print(f"   Data snapshot: {len(data['capsules'])} capsules, {len(data['bundles'])} bundles, {len(data['profiles'])} profiles, {len(data['llm_templates'])} LLM templates")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Path to truth-capsules-v1 root directory"
    )
    parser.add_argument(
        "--template",
        default="scripts/spa/template.html",
        help="Path to template.html (default: spa/template.html)"
    )
    parser.add_argument(
        "--output",
        default="capsule_composer.html",
        help="Output HTML file path (default: capsule_composer.html)"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.root):
        print(f"❌ ERROR: {args.root} is not a directory", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.template):
        print(f"❌ ERROR: Template not found: {args.template}", file=sys.stderr)
        sys.exit(1)

    try:
        generate_spa(args.root, args.template, args.output)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
