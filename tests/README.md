# Tests

Basic test suite for Truth Capsules validation.

## Running Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/test_capsules_validate.py
```

## Test Structure

```
tests/
├── test_capsules_validate.py  # Schema validation tests
├── fixtures/                   # Test data
│   └── capsules/              # Sample capsules for testing
└── README.md                   # This file
```

## What's Tested

- **Required fields:** All capsules have `id`, `version`, `domain`, `statement`
- **Witness structure:** Witnesses have `language` and `code` or `code_ref`
- **ID conventions:** Capsule IDs match filename patterns
- **Unicode handling:** No escape sequences (use UTF-8 characters)

## Adding Tests

When adding new tests:

1. Create test functions prefixed with `test_`
2. Use descriptive assertion messages
3. Add fixtures to `fixtures/` directory as needed
4. Update this README with test descriptions

## Future Tests

Planned for v1.1+:

- SHACL validation integration tests
- Composition workflow tests
- Witness execution sandbox tests
- Signature verification tests
- CI workflow smoke tests
