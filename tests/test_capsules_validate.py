"""
Basic capsule validation tests.

Run with: pytest tests/
"""
import pathlib
import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
CAPSULES = ROOT / "capsules"


def test_all_capsules_have_required_fields():
    """Verify all capsules have id, version, domain, and statement."""
    capsule_files = list(CAPSULES.glob("*.yaml"))
    assert len(capsule_files) > 0, "No capsule files found"

    for path in capsule_files:
        with open(path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)

        # Required fields
        assert "id" in doc, f"{path.name}: missing 'id' field"
        assert "version" in doc, f"{path.name}: missing 'version' field"
        assert "domain" in doc, f"{path.name}: missing 'domain' field"
        assert "statement" in doc, f"{path.name}: missing 'statement' field"


def test_witnesses_have_valid_structure():
    """Verify witnesses have language and either code or code_ref."""
    for path in CAPSULES.glob("*.yaml"):
        with open(path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)

        if "witnesses" not in doc:
            continue

        for i, witness in enumerate(doc["witnesses"]):
            # Must have language
            assert "language" in witness, \
                f"{path.name}: witness {i} missing 'language'"

            # Must have code XOR code_ref
            has_code = "code" in witness
            has_code_ref = "code_ref" in witness or "codeRef" in witness
            assert has_code or has_code_ref, \
                f"{path.name}: witness {i} missing code or code_ref"


def test_capsule_ids_match_filename():
    """Verify capsule IDs follow naming convention."""
    for path in CAPSULES.glob("*.yaml"):
        with open(path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)

        capsule_id = doc.get("id", "")
        expected_prefix = path.stem  # filename without .yaml

        # ID should match filename (with optional suffix after _vN)
        assert capsule_id.startswith(expected_prefix) or expected_prefix.startswith(capsule_id.rsplit("_", 1)[0]), \
            f"{path.name}: ID '{capsule_id}' doesn't match filename pattern"


def test_no_unicode_escapes():
    """Verify capsules use UTF-8 characters, not escape sequences."""
    for path in CAPSULES.glob("*.yaml"):
        content = path.read_text(encoding="utf-8")

        # Check for common unicode escapes that should be actual characters
        assert "\\u2265" not in content, f"{path.name}: contains \\u2265 instead of ≥"
        assert "\\u2264" not in content, f"{path.name}: contains \\u2264 instead of ≤"
        assert "\\u2192" not in content, f"{path.name}: contains \\u2192 instead of →"
