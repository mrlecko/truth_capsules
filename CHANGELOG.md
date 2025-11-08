# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-07

### Added

- **Core Features**
  - 24 high-quality capsules (LLM behavior, PR review, safety, business rules)
  - 6 pre-composed bundles for common workflows
  - 7 context profiles (conversational, CI, code assistant, pedagogical, etc.)
  - Deterministic composition with manifest lockfiles
  - Provenance and Ed25519 signing support

- **CLI Tools**
  - `capsule_linter.py` - Schema validation with strict mode
  - `compose_capsules_cli.py` - System prompt composition
  - `run_witnesses.py` - Executable witness validation
  - `capsule_sign.py` / `capsule_verify.py` - Cryptographic signing
  - `export_kg.py` - Knowledge graph export (RDF/NDJSON-LD)

- **Knowledge Graph Support**
  - RDF/Turtle export for SPARQL queries
  - NDJSON-LD for Neo4j/Memgraph property graphs
  - SHACL validation for schema compliance
  - Sample SPARQL queries included
  - Ontology and JSON-LD context definitions

- **CI/CD Integration**
  - GitHub Actions workflows for lint, compose, and LLM-judge
  - Policy enforcement (review status gates)
  - KG smoke tests with SHACL validation

- **Documentation**
  - Comprehensive README with quick start
  - Capsule schema specification v1
  - Profiles reference guide
  - Witnesses security guide
  - Knowledge graph integration guide
  - CI/CD setup guide

- **Web Tools**
  - Interactive SPA for visual composition
  - Snapshot-based web viewer with drag-and-drop

### Fixed

- Unicode character handling in capsules (replaced escape sequences)
- Profile naming consistency with alias system
- SHACL validation to match optional title field

### Security

- Removed demo private key from repository
- Added comprehensive .gitignore for secrets
- Created SECURITY.md policy
- Documented witness execution sandbox

## [Unreleased]

### Planned

- Automated test suite with pytest
- Pre-commit hooks for code quality
- Dependency pinning with pip-tools
- Enhanced SPA with live mode
- Community capsule gallery
- VSCode extension
- Additional language bindings (Node.js, Rust)
