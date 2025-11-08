#!/usr/bin/env python3
"""
Fix unicode escape sequences in YAML capsules.

This script converts escaped unicode sequences (e.g., \\u2265) to their
actual UTF-8 characters (e.g., ≥) for improved readability and proper YAML handling.
"""
import os
import re
import sys

# Mapping of common unicode escapes to their actual characters
UNICODE_MAP = {
    r'\u2264': '≤',  # less than or equal
    r'\u2265': '≥',  # greater than or equal
    r'\u2011': '‑',  # non-breaking hyphen
    r'\u2013': '–',  # en dash
    r'\u2014': '-',  # em dash
    r'\u2192': '→',  # rightwards arrow
    r'\u2019': '\u2019',  # right single quotation mark (curly apostrophe)
}

def fix_unicode_escapes(content: str) -> tuple[str, int]:
    """Replace unicode escape sequences with actual UTF-8 characters.

    Returns:
        tuple: (fixed_content, num_replacements)
    """
    fixed = content
    count = 0

    for escape, char in UNICODE_MAP.items():
        matches = fixed.count(escape)
        if matches > 0:
            fixed = fixed.replace(escape, char)
            count += matches

    return fixed, count

def process_file(filepath: str, dry_run: bool = False) -> tuple[bool, int]:
    """Process a single YAML file.

    Returns:
        tuple: (was_modified, num_replacements)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()

        fixed, count = fix_unicode_escapes(original)

        if count > 0:
            if not dry_run:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed)
            return True, count

        return False, 0

    except Exception as e:
        print(f"ERROR processing {filepath}: {e}", file=sys.stderr)
        return False, 0

def main():
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('path', help='Directory containing YAML capsules')
    ap.add_argument('--dry-run', action='store_true',
                    help='Show what would be fixed without modifying files')
    args = ap.parse_args()

    if not os.path.isdir(args.path):
        print(f"ERROR: {args.path} is not a directory", file=sys.stderr)
        sys.exit(1)

    total_files = 0
    modified_files = 0
    total_replacements = 0

    for root, dirs, files in os.walk(args.path):
        for filename in sorted(files):
            if filename.endswith(('.yaml', '.yml')):
                filepath = os.path.join(root, filename)
                total_files += 1

                was_modified, count = process_file(filepath, args.dry_run)

                if was_modified:
                    modified_files += 1
                    total_replacements += count
                    status = "WOULD FIX" if args.dry_run else "FIXED"
                    print(f"{status}: {filepath} ({count} replacements)")

    print(f"\nSummary: {modified_files}/{total_files} files modified, "
          f"{total_replacements} total replacements")

    if args.dry_run:
        print("(Dry run - no files were actually modified)")

if __name__ == '__main__':
    main()
