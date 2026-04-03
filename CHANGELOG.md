# Changelog

All notable changes to langchain-opendataloader-pdf will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- `detect_strikethrough` parameter (from opendataloader-pdf v2.1.0)
- Sync markers for automated option synchronization with opendataloader-pdf
- CI: `test.yml` — unit tests on every PR (Python 3.10, 3.12, 3.13)
- CI: `test-full.yml` — multi-platform full test (manual trigger)
- CI: `sync-upstream.yml` — automated code generation + PR on upstream release
- Regression snapshot tests
- pytest-socket for network isolation in unit tests

### Changed
- `split_pages` parameter moved after synced params block (keyword-only usage unaffected)
- `hybrid_timeout` default documented as `"0"` (no timeout), was `"30000"`
- README AI-AGENT-SUMMARY license: MIT → Apache-2.0
- README Parameters Reference table now auto-generated from options.json

### Fixed
- Parameters Reference table missing `detect_strikethrough`

## [2.0.0] - 2026-03-26

### Added
- Hybrid AI extraction mode (`hybrid`, `hybrid_mode`, `hybrid_url`, `hybrid_timeout`, `hybrid_fallback`)
- `sanitize` parameter for sensitive data masking
- `pages` parameter for page selection
- `include_header_footer` parameter
- `split_pages` parameter with per-page Document splitting
- `password` parameter for encrypted PDFs
- `use_struct_tree` parameter for tagged PDFs
- `table_method` parameter (default, cluster)
- `reading_order` parameter (xycut, off)
- `image_output`, `image_format`, `image_dir` parameters
- `keep_line_breaks` parameter
- `replace_invalid_chars` parameter
- JSON page splitting by `page number` field
- Comprehensive unit tests (59 tests)
- Integration tests with real PDF files (24 tests)
- Sample PDFs for testing

### Changed
- License changed from MIT to Apache-2.0
- Build system changed from poetry to hatchling
- Dependency: `opendataloader-pdf>=2.0.0` (was `>=1.3.0`)

## [1.2.0] - 2025-12-15

### Changed
- Updated for opendataloader-pdf v1.3.0 compatibility

## [1.1.0] - 2025-11-20

### Changed
- Migrated from `run()` to `convert()` API
- File-based output processing instead of in-memory

## [1.0.0] - 2025-10-01

### Added
- Initial release
- `OpenDataLoaderPDFLoader` class with `BaseLoader` interface
- Text and JSON output format support
- `lazy_load()` iterator support
