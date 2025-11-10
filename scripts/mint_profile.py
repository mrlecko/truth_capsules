#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mint a blank Truth Capsules profile YAML with the requested schema.

Usage:
  python3 scripts/mint_profile.py --name macgyver_v2 --title "Macgyverisms" --dir profiles
  python3 scripts/mint_profile.py --name conversational_guidance_v2
"""
import argparse, re
from pathlib import Path
from datetime import datetime, timezone

TEMPLATE = """kind: profile
id: profile.{id_name}
title: {title}
version: 1.0.0
description: {description}
response:
  format: natural
  policy: |
    Cite or abstain; follow Plan→Verify→Answer; ask ONE crisp follow-up if required.
  system_block: |
    SYSTEM: Profile={title}

    FORMAT: Natural language.
  projection:
    include:
    - title
    - statement
    - assumptions[:5]
    - pedagogy.socratic[:3]
    - pedagogy.aphorisms[:3]
    render:
      capsule_header: BEGIN CAPSULE id={{id}} version={{version}} domain={{domain}}
      assumption_bullet: '  - {{text}}'
      socratic_bullet: '  - {{text}}'
      aphorism_bullet: '  - {{text}}'
      enforcement_footer: 'ENFORCEMENT: Ensure outputs satisfy this capsule; otherwise
        abstain and request the minimal missing info.'
download:
  suggested_ext: txt
"""

def slug(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^\w.-]+", "_", s)
    return s

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True, help="Profile short name, e.g. macgyver_v1")
    p.add_argument("--title", default=None, help='Human title (default: TitleCase of name with separators -> spaces)')
    p.add_argument("--description", default=None, help="Description line for the profile")
    p.add_argument("--dir", default="profiles", help="Output directory (default: profiles)")
    p.add_argument("--force", action="store_true", help="Overwrite if the file exists")
    args = p.parse_args()

    id_name = slug(args.name)
    # Title default: turn underscores/dashes/dots into spaces and Title Case
    default_title = re.sub(r"[_\-.]+", " ", id_name).strip().title()
    title = args.title if args.title else default_title
    description = args.description if args.description else f"Bootstrap yourself or an LLM to solve problems like {title}."

    out_dir = Path(args.dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"profile.{id_name}.yaml"

    if out_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {out_path} (use --force to override)")

    content = TEMPLATE.format(
        id_name=id_name,
        title=title,
        description=description
    )

    # Normalize newlines and write
    out_path.write_text(content, encoding="utf-8")
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[mint_profile] wrote {out_path} at {ts}")

if __name__ == "__main__":
    main()
