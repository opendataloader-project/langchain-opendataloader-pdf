# Hybrid Mode Integration for langchain-opendataloader-pdf

**Date**: 2026-03-16
**Status**: Draft
**Scope**: Passthrough of 5 hybrid parameters from `opendataloader-pdf` core into the LangChain wrapper

---

## Problem

`opendataloader-pdf` core engine fully supports hybrid mode — intelligent routing of PDF pages between fast local Java processing and AI backend (docling-fast, hancom) for superior accuracy. The `opendataloader_pdf.convert()` function exposes 5 hybrid parameters, but `langchain-opendataloader-pdf` does not pass any of them through, leaving LangChain users unable to use hybrid extraction.

## Approach

**Flat parameter passthrough** — add 5 explicit parameters to `OpenDataLoaderPDFLoader.__init__()` following the existing pattern of individually declared, typed parameters forwarded to `convert()`.

Alternatives considered and rejected:
- **Dict-based config** (`hybrid_config: dict`): breaks existing pattern, no IDE autocompletion, weak typing
- **kwargs passthrough**: no type safety, poor discoverability

## Design

### 1. New Parameters

Added to `__init__` after `split_pages`:

```python
hybrid: Optional[str] = None,
    # Backend selection. None = Java-only (default).
    # Values: "docling-fast"
    # Note: "hancom" exists in Java core but is not exposed in
    # convert() Python API yet. Add when core exposes it.

hybrid_mode: Optional[str] = None,
    # Triage mode when hybrid is enabled.
    # "auto" (default): route only complex pages to backend
    # "full": route all pages to backend

hybrid_url: Optional[str] = None,
    # Custom backend server URL.
    # Default: http://localhost:5002 (docling-fast)

hybrid_timeout: Optional[str] = None,
    # Backend request timeout in milliseconds as string.
    # Default: "30000" (30 seconds)
    # Note: str type matches core engine's convert() signature.

hybrid_fallback: bool = False,
    # Opt-in to Java fallback on backend failure.
    # Default: False (matches core engine default).
```

### 2. convert() Call

Add to the existing `opendataloader_pdf.convert()` call in `lazy_load()`:

```python
hybrid=self.hybrid,
hybrid_mode=self.hybrid_mode,
hybrid_url=self.hybrid_url,
hybrid_timeout=self.hybrid_timeout,
hybrid_fallback=self.hybrid_fallback,
```

### 3. Metadata Extension

When `self.hybrid` is set (not None), add `"hybrid": self.hybrid` to Document metadata. Applied in all three yield points:
- `_split_into_pages()`
- `_split_json_into_pages()`
- Direct yield in `lazy_load()` (when `split_pages=False`)

### 4. No Validation Changes

No client-side validation of hybrid values. The core engine already validates and raises errors for invalid combinations. This keeps the wrapper thin.

### 5. Error Behavior — Hybrid Failures Must Be Explicit

The existing `lazy_load()` catches all exceptions with `except Exception` and silently logs them. **This behavior is changed for hybrid mode.** When `self.hybrid` is set, exceptions from `convert()` must re-raise so users get clear feedback about backend failures.

Implementation: in the `except Exception` block, check `if self.hybrid:` and re-raise instead of swallowing.

```python
except Exception as e:
    if self.hybrid:
        raise
    logger.error(f"Error: {e}")
```

This ensures:
- **hybrid enabled + backend unreachable + fallback=False** → exception raised to user with clear error message
- **hybrid enabled + backend unreachable + fallback=True** → core engine handles fallback internally, no exception
- **hybrid disabled (default)** → existing silent behavior preserved (no breaking change)

---

## Test Plan

### Unit Tests (test_document_loaders.py) — mock-based, no external deps

| Test | Description |
|------|-------------|
| `test_init_hybrid_defaults` | All 5 hybrid params default correctly (None/False) |
| `test_init_hybrid_custom_values` | Custom values stored correctly |
| `test_convert_called_with_hybrid_params` | `convert()` receives all 5 hybrid params individually |
| `test_convert_called_with_all_params_together` | `convert()` receives hybrid params combined with existing params |
| `test_convert_hybrid_none_passthrough` | `convert()` receives None/False when hybrid not set |
| `test_metadata_includes_hybrid` | Document metadata contains `hybrid` key when set |
| `test_metadata_no_hybrid_when_off` | Document metadata has no `hybrid` key when None |
| `test_split_pages_metadata_includes_hybrid` | Per-page Documents include hybrid in metadata |
| `test_split_json_pages_metadata_includes_hybrid` | JSON split Documents include hybrid in metadata |
| `test_hybrid_error_reraise` | When hybrid set and convert() raises, exception propagates to caller |
| `test_non_hybrid_error_swallowed` | When hybrid not set and convert() raises, error logged silently (existing behavior) |

### Integration Tests (test_integration.py) — requires Java 11+ only (NO hybrid server)

These tests validate hybrid parameter passthrough and fallback behavior using only local Java. They do NOT require a running hybrid backend server.

| Test | Description | Skip Condition |
|------|-------------|----------------|
| `test_hybrid_fallback_on_bad_url` | fallback=True with unreachable URL → Java result (documents returned) | No Java |
| `test_hybrid_no_fallback_on_bad_url` | fallback=False with unreachable URL → exception raised with clear error message | No Java |

### E2E Tests (test_e2e_hybrid.py) — requires Java 11+ AND running hybrid server

These tests validate actual hybrid extraction end-to-end with a real backend server. They cover format correctness, triage behavior, and timeout handling that cannot be tested without a live server.

**Skip condition**: `@pytest.mark.skipif` — Java unavailable OR hybrid server not reachable.

**Server URL**: `os.environ.get("ODL_HYBRID_URL", "http://localhost:5002")`

| # | Test | Input | Verification |
|---|------|-------|--------------|
| 1 | `test_text_pdf_auto_mode` | Simple text PDF | Documents created, hybrid metadata present |
| 2 | `test_table_pdf_auto_mode` | Table-heavy PDF | Markdown output contains pipe characters for tables |
| 3 | `test_full_mode` | Any PDF | All pages processed by backend (compare with auto result) |
| 4 | `test_split_pages_hybrid` | Multi-page PDF | Per-page Documents, correct page metadata |
| 5 | `test_all_formats` | Same PDF → text, markdown, json, html | All 4 formats produce valid output |
| 6 | `test_fallback_bad_url` | Invalid URL + fallback=True | Java fallback returns valid Documents |
| 7 | `test_no_fallback_bad_url` | Invalid URL + fallback=False | Exception raised with clear error message |
| 8 | `test_timeout_short` | timeout=1ms | Timeout behavior confirmed |

**Fixtures**:
```python
@pytest.fixture
def hybrid_url():
    return os.environ.get("ODL_HYBRID_URL", "http://localhost:5002")

@pytest.fixture
def is_hybrid_available(hybrid_url):
    """Check server availability, skip all if unreachable."""

@pytest.fixture
def sample_pdf():
    """Simple 1-page text PDF."""

@pytest.fixture
def table_pdf():
    """PDF with complex tables."""

@pytest.fixture
def multi_page_pdf():
    """Multi-page PDF for split_pages tests."""
```

---

## Files Changed

| File | Change |
|------|--------|
| `langchain_opendataloader_pdf/document_loaders.py` | Add 5 params to `__init__`, forward in `convert()`, extend metadata |
| `tests/test_document_loaders.py` | Add 11 unit tests |
| `tests/test_integration.py` | Add 2 integration tests (fallback scenarios, Java-only) |
| `tests/test_e2e_hybrid.py` | New file, 8 E2E tests |
| `README.md` | Add hybrid usage example (see below) |

## README Example

```python
# Hybrid mode: route complex pages to AI backend for better accuracy
loader = OpenDataLoaderPDFLoader(
    file_path="document.pdf",
    format="markdown",
    hybrid="docling-fast",          # Enable hybrid with docling-fast backend
    hybrid_mode="auto",             # Auto-triage: only complex pages go to backend
    hybrid_url="http://localhost:5002",  # Backend server URL
)
documents = loader.load()
```

---

## Out of Scope

- OCR, formula enrichment, picture description (hybrid_server.py features) — future iteration
- New backend types (azure, google) — not yet implemented in core
- Client-side parameter validation — delegated to core engine
