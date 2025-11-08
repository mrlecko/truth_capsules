#!/usr/bin/env python3
"""
Compose system prompts and manifests from truth capsules.

Combines profiles, bundles, and individual capsules into a deterministic
system prompt suitable for LLM consumption, along with a JSON manifest
for reproducibility and auditing.

Usage:
  python compose_capsules_cli.py \\
    --root truth-capsules-v1 \\
    --profile conversational \\
    --bundle pr_review_minibundle_v1 \\
    --out prompt.txt \\
    --manifest prompt.manifest.json

  # List available profiles and bundles
  python compose_capsules_cli.py --root truth-capsules-v1 --list-profiles
  python compose_capsules_cli.py --root truth-capsules-v1 --list-bundles
"""
import os
import sys
import json
import argparse
import glob
import yaml
import hashlib
import datetime
from typing import Dict, List, Optional

# Profile aliases: short name → full profile ID
# This allows users to type --profile conversational instead of
# --profile profile.conversational_guidance_v1
PROFILE_ALIASES = {
    "conversational": "profile.conversational_guidance_v1",
    "pedagogical": "profile.pedagogical_v1",
    "code_patch": "profile.code_patch_v1",
    "tool_runner": "profile.tool_runner_v1",
    "ci_det": "profile.ci_deterministic_gate_v1",
    "ci_llm": "profile.ci_llm_judge_v1",
    "rules_gen": "profile.rules_generator_v1",
}


def load_yaml(filepath: str) -> dict:
    """Load a YAML file and return parsed dict with metadata."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    data = yaml.safe_load(raw) or {}
    data["__file__"] = filepath
    data["__raw__"] = raw
    return data


def index_capsules(root: str) -> Dict[str, dict]:
    """Build an ID→capsule dict from the capsules directory.

    Supports recursive directory structure (e.g., capsules/llm/*.yaml).
    Capsules are indexed by their 'id' field, not by file path.
    """
    caps = {}
    pattern = os.path.join(root, "capsules", "**", "*.yaml")
    for filepath in sorted(glob.glob(pattern, recursive=True)):
        capsule = load_yaml(filepath)
        capsule_id = capsule.get("id") or os.path.splitext(os.path.basename(filepath))[0]
        capsule["id"] = capsule_id
        caps[capsule_id] = capsule
    return caps


def index_bundles(root: str) -> Dict[str, dict]:
    """Build a name→bundle dict from the bundles directory."""
    bundles = {}
    pattern = os.path.join(root, "bundles", "*.yaml")
    for filepath in sorted(glob.glob(pattern)):
        bundle = load_yaml(filepath)
        name = bundle.get("name") or os.path.splitext(os.path.basename(filepath))[0]
        bundle["name"] = name
        bundles[name] = bundle
    return bundles


def index_profiles(root: str) -> Dict[str, dict]:
    """Build an ID→profile dict from the profiles directory."""
    profiles = {}
    pattern = os.path.join(root, "profiles", "*.yaml")
    for filepath in sorted(glob.glob(pattern)):
        profile = load_yaml(filepath)
        profile_id = profile.get("id") or os.path.splitext(os.path.basename(filepath))[0]
        profile["id"] = profile_id
        profiles[profile_id] = profile
    return profiles


def resolve_profile(name: str, profiles: Dict[str, dict]) -> Optional[dict]:
    """Resolve profile by exact ID or alias."""
    # Try exact match first
    if name in profiles:
        return profiles[name]
    # Try alias
    full_id = PROFILE_ALIASES.get(name)
    if full_id and full_id in profiles:
        return profiles[full_id]
    return None


def parse_field_spec(spec: str) -> tuple[str, Optional[int]]:
    """Parse field specification with optional slice.

    Examples:
        "title" → ("title", None)
        "assumptions[:5]" → ("assumptions", 5)
        "pedagogy.socratic[:3]" → ("pedagogy.socratic", 3)

    Args:
        spec: Field specification string

    Returns:
        Tuple of (field_path, limit) where limit is None if no slice
    """
    import re
    match = re.match(r'^([a-z_.]+)(?:\[:(\d+)\])?$', spec)
    if not match:
        return spec, None
    field_path, limit = match.groups()
    return field_path, int(limit) if limit else None


def apply_projection(capsule: dict, projection: dict) -> dict:
    """Apply projection rules to a capsule.

    Args:
        capsule: Source capsule dict
        projection: Projection spec with 'include' list

    Returns:
        Filtered capsule dict containing only projected fields
    """
    include_specs = projection.get("include", [])
    if not include_specs:
        # No projection, return full capsule
        return capsule

    projected = {
        "id": capsule.get("id"),
        "version": capsule.get("version"),
        "domain": capsule.get("domain")
    }

    for spec in include_specs:
        field_path, limit = parse_field_spec(spec)

        # Handle nested pedagogy fields
        if field_path.startswith("pedagogy."):
            pedagogy_type = field_path.split(".", 1)[1]  # e.g., "socratic" or "aphorisms"
            pedagogy = capsule.get("pedagogy", [])
            if not isinstance(pedagogy, list):
                continue

            # Filter by kind
            if pedagogy_type == "socratic":
                items = [p.get("text", "") for p in pedagogy if p.get("kind", "").lower() == "socratic"]
            elif pedagogy_type == "aphorisms":
                items = [p.get("text", "") for p in pedagogy if p.get("kind", "").lower() == "aphorism"]
            else:
                continue

            # Apply limit if specified
            if limit is not None:
                items = items[:limit]

            # Store in projected capsule
            if pedagogy_type not in projected:
                projected[pedagogy_type] = []
            projected[pedagogy_type] = items

        else:
            # Simple field (title, statement, assumptions, etc.)
            value = capsule.get(field_path)
            if value is None:
                continue

            # Apply limit if it's a list
            if isinstance(value, list) and limit is not None:
                value = value[:limit]

            projected[field_path] = value

    return projected


def build_control_table(capsules: List[dict], priority_overrides: dict = None) -> str:
    """Build a compact control table showing capsule priorities and directives.

    Args:
        capsules: List of capsules to include in the table
        priority_overrides: Optional dict mapping capsule IDs to priority values

    Returns:
        Formatted control table as a string
    """
    if not capsules:
        return ""

    # Default priorities for known capsules (lower = higher priority)
    DEFAULT_PRIORITIES = {
        "llm.safety_refusal_guard_v1": 1,
        "llm.pii_redaction_guard_v1": 2,
        "llm.citation_required_v1": 3,
        "llm.plan_verify_answer_v1": 4,
    }

    # Directive templates for known capsules
    DIRECTIVE_TEMPLATES = {
        "llm.safety_refusal_guard_v1": "FORBID unsafe outputs",
        "llm.pii_redaction_guard_v1": "FORBID raw PII",
        "llm.citation_required_v1": "MUST cite or abstain",
        "llm.plan_verify_answer_v1": "MUST Plan→Verify→Answer",
    }

    # Build rows
    rows = []
    for capsule in capsules:
        cap_id = capsule.get("id", "?")

        # Determine priority
        priority = DEFAULT_PRIORITIES.get(cap_id, 5)
        if priority_overrides and cap_id in priority_overrides:
            priority = priority_overrides[cap_id]

        # Determine directive
        directive = DIRECTIVE_TEMPLATES.get(cap_id, "SEE capsule statement")

        rows.append((priority, cap_id, directive))

    # Sort by priority (lower first), then by ID
    rows.sort(key=lambda x: (x[0], x[1]))

    # Format table
    lines = []
    lines.append("SYSTEM: Capsule Control Table (compiled)")
    lines.append("| Pri | Capsule ID                           | Directive                  |")
    lines.append("|-----|--------------------------------------|----------------------------|")

    for priority, cap_id, directive in rows:
        # Pad to fixed widths for readability
        lines.append(f"| {priority:3d} | {cap_id:36s} | {directive:26s} |")

    return "\n".join(lines)


def compose_text(
    profile: dict,
    capsules: List[dict],
    projection: dict = None,
    include_pedagogy: bool = True,
    control_table_enabled: bool = False,
    priority_overrides: dict = None
) -> str:
    """Compose the final system prompt text.

    Args:
        profile: Profile dict with response block
        capsules: List of capsule dicts to include
        projection: Optional projection spec (if None, uses profile's projection)
        include_pedagogy: Whether to include Socratic/Aphorism sections
        control_table_enabled: Whether to include control table
        priority_overrides: Optional priority overrides for control table

    Returns:
        Formatted system prompt as string
    """
    lines = []
    response = profile.get("response", {})

    # Determine effective projection
    if projection is None:
        projection = response.get("projection", {})

    # Get render templates from projection or use defaults
    render_templates = projection.get("render", {}) if projection else {}

    # Profile header: use system_block if present
    system_block = response.get("system_block")
    if system_block:
        lines.append(system_block.strip())
    else:
        # Construct from individual fields
        lines.append(
            f"SYSTEM: Profile={profile.get('title', '?')} "
            f"(id={profile.get('id', '?')}, v={profile.get('version', '?')})"
        )
        if response.get("policy"):
            lines.append(f"POLICY: {response['policy'].strip()}")
        if response.get("format"):
            lines.append(f"FORMAT: {response['format']}")

    # Schema reference hint
    if response.get("schema_ref"):
        lines.append("")
        lines.append(f"SYSTEM: SCHEMA_REF {response['schema_ref']}")

    # Control table (if enabled)
    if control_table_enabled:
        lines.append("")
        lines.append(build_control_table(capsules, priority_overrides))

    # Capsule rules section
    lines.append("")
    lines.append("SYSTEM: Capsule Rules (Selected)")

    for capsule in capsules:
        # Apply projection if available
        if projection and projection.get("include"):
            projected_capsule = apply_projection(capsule, projection)
        else:
            projected_capsule = capsule

        # Render capsule header
        header_template = render_templates.get(
            "capsule_header",
            "BEGIN CAPSULE id={id} version={version} domain={domain}"
        )
        header = header_template.format(
            id=projected_capsule.get("id", "?"),
            version=projected_capsule.get("version", "?"),
            domain=projected_capsule.get("domain", "?")
        )
        lines.append(header)

        # Title
        if projected_capsule.get("title"):
            lines.append(f"TITLE: {projected_capsule['title']}")

        # Statement
        if projected_capsule.get("statement"):
            lines.append(f"STATEMENT: {projected_capsule['statement']}")

        # Assumptions
        assumptions = projected_capsule.get("assumptions")
        if assumptions:
            if not isinstance(assumptions, list):
                assumptions = [assumptions]
            lines.append("ASSUMPTIONS:")
            assumption_template = render_templates.get("assumption_bullet", "  - {text}")
            for a in assumptions:
                lines.append(assumption_template.format(text=str(a)))

        # Pedagogy sections (if not filtered by compact mode)
        if include_pedagogy:
            # Socratic prompts
            socratic = projected_capsule.get("socratic", [])
            if socratic:
                lines.append("SOCRATIC:")
                socratic_template = render_templates.get("socratic_bullet", "  - {text}")
                for text in socratic:
                    lines.append(socratic_template.format(text=text.strip()))

            # Aphorisms
            aphorisms = projected_capsule.get("aphorisms", [])
            if aphorisms:
                lines.append("APHORISMS:")
                aphorism_template = render_templates.get("aphorism_bullet", "  - {text}")
                for text in aphorisms:
                    lines.append(aphorism_template.format(text=text.strip()))

        # Enforcement footer
        enforcement_template = render_templates.get(
            "enforcement_footer",
            "ENFORCEMENT: Ensure outputs satisfy this capsule; otherwise abstain and request the minimal missing info."
        )
        lines.append(enforcement_template)
        lines.append("END CAPSULE")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def list_profiles(profiles: Dict[str, dict]) -> None:
    """Print available profiles with aliases."""
    print("Available Profiles:\n")

    # Build reverse alias map
    alias_to_ids = {}
    for alias, profile_id in PROFILE_ALIASES.items():
        if profile_id not in alias_to_ids:
            alias_to_ids[profile_id] = []
        alias_to_ids[profile_id].append(alias)

    for profile_id in sorted(profiles.keys()):
        profile = profiles[profile_id]
        title = profile.get("title", "?")
        aliases = alias_to_ids.get(profile_id, [])

        print(f"  {profile_id}")
        print(f"    Title: {title}")
        if aliases:
            print(f"    Aliases: {', '.join(aliases)}")
        print()


def list_bundles(bundles: Dict[str, dict]) -> None:
    """Print available bundles."""
    print("Available Bundles:\n")
    for name in sorted(bundles.keys()):
        bundle = bundles[name]
        capsule_ids = bundle.get("capsules", [])
        applies_to = bundle.get("applies_to", [])

        print(f"  {name}")
        print(f"    Capsules: {len(capsule_ids)}")
        if applies_to:
            print(f"    Applies to: {', '.join(applies_to)}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--root",
        required=True,
        help="Path to truth-capsules root directory"
    )
    ap.add_argument(
        "--profile",
        help="Profile ID or alias (e.g., 'conversational' or 'profile.conversational_guidance_v1')"
    )
    ap.add_argument(
        "--bundle",
        action="append",
        default=[],
        help="Bundle name(s) to include (can be specified multiple times)"
    )
    ap.add_argument(
        "--capsule",
        action="append",
        default=[],
        help="Additional capsule IDs to include (can be specified multiple times)"
    )
    ap.add_argument(
        "--out",
        help="Output prompt file path"
    )
    ap.add_argument(
        "--manifest",
        help="Output manifest JSON file path (optional)"
    )
    ap.add_argument(
        "--projection",
        help="Override profile's default projection (e.g., 'ci', 'compact', 'full')"
    )
    ap.add_argument(
        "--compact",
        action="store_true",
        help="Compact mode: exclude pedagogy fields regardless of projection"
    )
    ap.add_argument(
        "--control-table",
        action="store_true",
        default=False,
        help="Include capsule control table (priority + directive summary)"
    )
    ap.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit"
    )
    ap.add_argument(
        "--list-bundles",
        action="store_true",
        help="List available bundles and exit"
    )
    args = ap.parse_args()

    # Load indices
    profiles = index_profiles(args.root)
    bundles = index_bundles(args.root)
    capsules_index = index_capsules(args.root)

    # Handle list commands
    if args.list_profiles:
        list_profiles(profiles)
        return 0

    if args.list_bundles:
        list_bundles(bundles)
        return 0

    # Validate compose requirements
    if not args.profile or not args.out:
        print("ERROR: --profile and --out are required for composition", file=sys.stderr)
        print("Use --list-profiles or --list-bundles to see available options", file=sys.stderr)
        return 2

    # Resolve profile
    profile = resolve_profile(args.profile, profiles)
    if not profile:
        print(f"ERROR: Profile not found: {args.profile}", file=sys.stderr)
        print("\nAvailable profiles:", file=sys.stderr)
        for pid in sorted(profiles.keys()):
            print(f"  - {pid}", file=sys.stderr)
        print("\nAvailable aliases:", file=sys.stderr)
        for alias in sorted(PROFILE_ALIASES.keys()):
            print(f"  - {alias}", file=sys.stderr)
        return 2

    # Resolve capsules from bundles and explicit capsule args
    # Bundle v1.1 support: collect excludes, order, priority_overrides from all bundles
    all_excludes = set()
    explicit_order = []
    all_priority_overrides = {}

    selected_capsules = []
    seen_ids = set()

    # Add capsules from bundles (with v1.1 features)
    for bundle_name in args.bundle:
        bundle = bundles.get(bundle_name)
        if not bundle:
            print(f"WARNING: Bundle not found: {bundle_name}", file=sys.stderr)
            continue

        # Collect bundle v1.1 metadata
        excludes = bundle.get("excludes", [])
        all_excludes.update(excludes)

        order = bundle.get("order", [])
        if order:
            explicit_order.extend(order)

        priority_overrides = bundle.get("priority_overrides", {})
        if priority_overrides:
            all_priority_overrides.update(priority_overrides)

        # Add capsules from bundle
        for capsule_id in bundle.get("capsules", []):
            if capsule_id in capsules_index and capsule_id not in seen_ids:
                selected_capsules.append(capsules_index[capsule_id])
                seen_ids.add(capsule_id)

    # Add explicit capsules (accept IDs or file paths)
    for ref in args.capsule:
        chosen = None

        # 1) Exact ID match
        if ref in capsules_index:
            chosen = capsules_index[ref]

        # 2) Basename-as-ID (e.g., capsules/foo.bar_v1.yaml -> foo.bar_v1)
        if chosen is None:
            base_id = os.path.splitext(os.path.basename(ref))[0]
            if base_id in capsules_index:
                chosen = capsules_index[base_id]

        # 3) Treat as file path anywhere on disk
        if chosen is None and os.path.isfile(ref):
            try:
                cap = load_yaml(ref)
                cap_id = cap.get("id") or os.path.splitext(os.path.basename(ref))[0]
                cap["id"] = cap_id
                chosen = cap
            except Exception as e:
                print(f"WARNING: Failed to load capsule file: {ref} ({e})", file=sys.stderr)

        if chosen:
            if chosen["id"] not in seen_ids:
                selected_capsules.append(chosen)
                seen_ids.add(chosen["id"])
        else:
            print(f"WARNING: Capsule not found: {ref}", file=sys.stderr)

    # Apply excludes (bundle v1.1 feature)
    if all_excludes:
        selected_capsules = [c for c in selected_capsules if c["id"] not in all_excludes]

    # Apply explicit ordering (bundle v1.1 feature)
    if explicit_order:
        # Build a map of capsule ID → capsule
        capsule_map = {c["id"]: c for c in selected_capsules}

        # Reorder according to explicit_order, then append remaining in original order
        reordered = []
        for cap_id in explicit_order:
            if cap_id in capsule_map:
                reordered.append(capsule_map[cap_id])
                del capsule_map[cap_id]  # Remove from map so we don't add it twice

        # Append remaining capsules (not in explicit order) in their original order
        for capsule in selected_capsules:
            if capsule["id"] in capsule_map:
                reordered.append(capsule)

        selected_capsules = reordered

    if not selected_capsules:
        print("ERROR: No capsules selected. Specify at least one --bundle or --capsule", file=sys.stderr)
        return 3

    # Compose prompt with new parameters (bundle v1.1 support)
    prompt_text = compose_text(
        profile=profile,
        capsules=selected_capsules,
        projection=None,  # Uses profile's projection by default
        include_pedagogy=not args.compact,
        control_table_enabled=args.control_table,
        priority_overrides=all_priority_overrides if all_priority_overrides else None
    )

    # Write output
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(prompt_text)

    print(f"✓ Wrote {args.out} ({len(selected_capsules)} capsules)")

    # Write manifest if requested
    if args.manifest:
        # Build bundle info (with versions if available)
        bundle_info = []
        for bundle_name in args.bundle:
            bundle = bundles.get(bundle_name, {})
            bundle_info.append({
                "name": bundle_name,
                "version": bundle.get("version", "1.0.0")  # Default to 1.0.0 if not specified
            })

        # Build capsule info with file paths and SHA256 hashes
        capsule_info = []
        for capsule in selected_capsules:
            filepath = capsule.get("__file__", "")
            # Calculate SHA256 hash if file exists
            sha256_hash = None
            if filepath and os.path.exists(filepath):
                try:
                    with open(filepath, "rb") as f:
                        sha256_hash = hashlib.sha256(f.read()).hexdigest()
                except Exception:
                    pass

            capsule_info.append({
                "id": capsule["id"],
                "file": filepath,
                "sha256": sha256_hash
            })

        manifest = {
            "profile": profile.get("id"),
            "profile_version": profile.get("version", "1.0.0"),
            "projection": "default",  # Will be updated in Phase 2 when projection logic is added
            "bundles": bundle_info,
            "capsules": capsule_info,
            "composer_version": "1.1.0",
            "abstain_policy": "ask-one-then-abstain",
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        with open(args.manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"✓ Wrote {args.manifest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
