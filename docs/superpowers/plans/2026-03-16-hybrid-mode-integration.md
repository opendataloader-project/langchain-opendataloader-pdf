# Hybrid Mode Integration — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose opendataloader-pdf's hybrid extraction parameters in the LangChain wrapper so users can leverage AI-backend-assisted PDF extraction.

**Architecture:** Add 5 flat parameters (`hybrid`, `hybrid_mode`, `hybrid_url`, `hybrid_timeout`, `hybrid_fallback`) to `OpenDataLoaderPDFLoader.__init__()`, forward them to `opendataloader_pdf.convert()`, extend Document metadata when hybrid is active, and re-raise exceptions when hybrid mode fails instead of silently swallowing them.

**Tech Stack:** Python, LangChain Core, opendataloader-pdf >= 2.0.0, pytest

**Spec:** `docs/superpowers/specs/2026-03-16-hybrid-mode-integration-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `langchain_opendataloader_pdf/document_loaders.py` | Add 5 hybrid params to `__init__`, forward in `convert()`, extend metadata, change error handling for hybrid |
| `tests/test_document_loaders.py` | 13 new unit tests (mock-based) |
| `tests/test_integration.py` | 2 new integration tests (Java-only, fallback scenarios) |
| `tests/test_e2e_hybrid.py` | New file, 8 E2E tests (requires hybrid server) |
| `README.md` | Add hybrid section to usage examples and parameters table |

---

## Chunk 1: Unit Tests + Implementation

### Task 1: Add hybrid parameter init tests

**Files:**
- Test: `tests/test_document_loaders.py`

- [ ] **Step 1: Write failing test — hybrid defaults**

Add to `TestOpenDataLoaderPDFLoaderInit` class:

```python
def test_init_hybrid_defaults(self):
    loader = OpenDataLoaderPDFLoader(file_path="test.pdf")
    assert loader.hybrid is None
    assert loader.hybrid_mode is None
    assert loader.hybrid_url is None
    assert loader.hybrid_timeout is None
    assert loader.hybrid_fallback is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderInit::test_init_hybrid_defaults -v`
Expected: FAIL — `AttributeError: 'OpenDataLoaderPDFLoader' object has no attribute 'hybrid'`

- [ ] **Step 3: Write failing test — hybrid custom values**

```python
def test_init_hybrid_custom_values(self):
    loader = OpenDataLoaderPDFLoader(
        file_path="test.pdf",
        hybrid="docling-fast",
        hybrid_mode="full",
        hybrid_url="http://my-server:5002",
        hybrid_timeout="60000",
        hybrid_fallback=True,
    )
    assert loader.hybrid == "docling-fast"
    assert loader.hybrid_mode == "full"
    assert loader.hybrid_url == "http://my-server:5002"
    assert loader.hybrid_timeout == "60000"
    assert loader.hybrid_fallback is True
```

- [ ] **Step 4: Implement hybrid parameters in `__init__`**

Modify: `langchain_opendataloader_pdf/document_loaders.py:46-118`

Add after `split_pages: bool = True,` (line 64):

```python
hybrid: Optional[str] = None,
hybrid_mode: Optional[str] = None,
hybrid_url: Optional[str] = None,
hybrid_timeout: Optional[str] = None,
hybrid_fallback: bool = False,
```

Add docstring entries before the closing `"""` on line 98, after the `split_pages` docstring entry:

```python
hybrid: Backend for hybrid AI extraction. None = Java-only (default).
    Values: "docling-fast". Requires a running hybrid backend server.
hybrid_mode: Triage mode when hybrid is enabled.
    "auto" (default): route only complex pages to backend.
    "full": route all pages to backend.
hybrid_url: Custom backend server URL. Default: http://localhost:5002
hybrid_timeout: Backend request timeout in milliseconds (as string).
    Default: "30000" (30 seconds).
hybrid_fallback: Opt-in to Java fallback on backend failure.
    Default: False.
```

Add assignments after `self.split_pages = split_pages` (line 118):

```python
self.hybrid = hybrid
self.hybrid_mode = hybrid_mode
self.hybrid_url = hybrid_url
self.hybrid_timeout = hybrid_timeout
self.hybrid_fallback = hybrid_fallback
```

- [ ] **Step 5: Run both init tests to verify they pass**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderInit::test_init_hybrid_defaults tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderInit::test_init_hybrid_custom_values -v`
Expected: 2 PASSED

- [ ] **Step 6: Commit**

```bash
cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf
git add langchain_opendataloader_pdf/document_loaders.py tests/test_document_loaders.py
git commit -m "feat: add hybrid parameters to OpenDataLoaderPDFLoader init"
```

---

### Task 2: Forward hybrid params to convert()

**Files:**
- Test: `tests/test_document_loaders.py`
- Modify: `langchain_opendataloader_pdf/document_loaders.py:223-244`

- [ ] **Step 1: Write failing test — convert receives hybrid params**

Add to `TestOpenDataLoaderPDFLoaderConvertCall` class:

```python
@patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
@patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
def test_convert_passes_hybrid_params(self, mock_mkdtemp, mock_odl):
    mock_mkdtemp.return_value = "/tmp/test"
    mock_odl.convert = MagicMock()

    loader = OpenDataLoaderPDFLoader(
        file_path="test.pdf",
        hybrid="docling-fast",
        hybrid_mode="auto",
        hybrid_url="http://localhost:5002",
        hybrid_timeout="60000",
        hybrid_fallback=True,
    )
    list(loader.lazy_load())

    call_kwargs = mock_odl.convert.call_args[1]
    assert call_kwargs["hybrid"] == "docling-fast"
    assert call_kwargs["hybrid_mode"] == "auto"
    assert call_kwargs["hybrid_url"] == "http://localhost:5002"
    assert call_kwargs["hybrid_timeout"] == "60000"
    assert call_kwargs["hybrid_fallback"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderConvertCall::test_convert_passes_hybrid_params -v`
Expected: FAIL — `KeyError: 'hybrid'`

- [ ] **Step 3: Write failing test — hybrid none passthrough**

```python
@patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
@patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
def test_convert_hybrid_none_passthrough(self, mock_mkdtemp, mock_odl):
    mock_mkdtemp.return_value = "/tmp/test"
    mock_odl.convert = MagicMock()

    loader = OpenDataLoaderPDFLoader(file_path="test.pdf")
    list(loader.lazy_load())

    call_kwargs = mock_odl.convert.call_args[1]
    assert call_kwargs["hybrid"] is None
    assert call_kwargs["hybrid_mode"] is None
    assert call_kwargs["hybrid_url"] is None
    assert call_kwargs["hybrid_timeout"] is None
    assert call_kwargs["hybrid_fallback"] is False
```

- [ ] **Step 4: Write failing test — all params together including hybrid**

```python
@patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
@patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
def test_convert_passes_all_options_with_hybrid(self, mock_mkdtemp, mock_odl):
    mock_mkdtemp.return_value = "/tmp/test"
    mock_odl.convert = MagicMock()

    loader = OpenDataLoaderPDFLoader(
        file_path=["a.pdf", "b.pdf"],
        format="markdown",
        quiet=True,
        password="secret",
        content_safety_off=["hidden-text"],
        keep_line_breaks=True,
        replace_invalid_chars="?",
        use_struct_tree=True,
        table_method="cluster",
        reading_order="xycut",
        image_output="external",
        image_format="jpeg",
        image_dir="./images",
        sanitize=True,
        pages="1,3,5-7",
        include_header_footer=True,
        split_pages=False,
        hybrid="docling-fast",
        hybrid_mode="full",
        hybrid_url="http://my-server:5002",
        hybrid_timeout="60000",
        hybrid_fallback=True,
    )
    list(loader.lazy_load())

    call_kwargs = mock_odl.convert.call_args[1]
    # Existing params still work
    assert call_kwargs["input_path"] == ["a.pdf", "b.pdf"]
    assert call_kwargs["format"] == ["markdown"]
    assert call_kwargs["quiet"] is True
    assert call_kwargs["sanitize"] is True
    # Hybrid params
    assert call_kwargs["hybrid"] == "docling-fast"
    assert call_kwargs["hybrid_mode"] == "full"
    assert call_kwargs["hybrid_url"] == "http://my-server:5002"
    assert call_kwargs["hybrid_timeout"] == "60000"
    assert call_kwargs["hybrid_fallback"] is True
```

- [ ] **Step 5: Implement — add hybrid params to convert() call**

In `langchain_opendataloader_pdf/document_loaders.py`, add after `include_header_footer=self.include_header_footer,` (line 243):

```python
hybrid=self.hybrid,
hybrid_mode=self.hybrid_mode,
hybrid_url=self.hybrid_url,
hybrid_timeout=self.hybrid_timeout,
hybrid_fallback=self.hybrid_fallback,
```

- [ ] **Step 6: Run all 3 new convert tests to verify they pass**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderConvertCall::test_convert_passes_hybrid_params tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderConvertCall::test_convert_hybrid_none_passthrough tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderConvertCall::test_convert_passes_all_options_with_hybrid -v`
Expected: 3 PASSED

- [ ] **Step 7: Commit**

```bash
cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf
git add langchain_opendataloader_pdf/document_loaders.py tests/test_document_loaders.py
git commit -m "feat: forward hybrid params to opendataloader_pdf.convert()"
```

---

### Task 3: Hybrid metadata in Documents

**Files:**
- Test: `tests/test_document_loaders.py`
- Modify: `langchain_opendataloader_pdf/document_loaders.py`

- [ ] **Step 1: Write failing test — metadata includes hybrid when set**

Add new test class:

```python
class TestOpenDataLoaderPDFLoaderHybridMetadata:
    """Test hybrid metadata in Document objects."""

    def test_metadata_includes_hybrid(self):
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", hybrid="docling-fast", split_pages=True
        )
        content = (
            "\n<<<ODL_PAGE_BREAK_1>>>\n"
            "Page 1 content"
        )
        docs = list(loader._split_into_pages(content, "test.pdf"))
        assert docs[0].metadata["hybrid"] == "docling-fast"

    def test_metadata_no_hybrid_when_off(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", split_pages=True)
        content = (
            "\n<<<ODL_PAGE_BREAK_1>>>\n"
            "Page 1 content"
        )
        docs = list(loader._split_into_pages(content, "test.pdf"))
        assert "hybrid" not in docs[0].metadata

    def test_split_pages_metadata_includes_hybrid(self):
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", hybrid="docling-fast", split_pages=True
        )
        content = (
            "\n<<<ODL_PAGE_BREAK_1>>>\n"
            "Page 1"
            "\n<<<ODL_PAGE_BREAK_2>>>\n"
            "Page 2"
        )
        docs = list(loader._split_into_pages(content, "test.pdf"))
        assert all(d.metadata["hybrid"] == "docling-fast" for d in docs)

    def test_split_json_pages_metadata_includes_hybrid(self):
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", format="json", hybrid="docling-fast", split_pages=True
        )
        json_data = {
            "kids": [
                {"type": "paragraph", "page number": 1, "content": "Text"},
            ]
        }
        docs = list(loader._split_json_into_pages(json_data, "test.pdf"))
        assert docs[0].metadata["hybrid"] == "docling-fast"

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    @patch("builtins.open", create=True)
    @patch("langchain_opendataloader_pdf.document_loaders.Path")
    def test_metadata_includes_hybrid_no_split(
        self, mock_path_class, mock_open, mock_mkdtemp, mock_odl
    ):
        """Test hybrid metadata when split_pages=False (direct yield path)."""
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        mock_file_content = "Full document content"
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.read.return_value = mock_file_content
        mock_open.return_value = mock_file

        mock_path_instance = MagicMock()
        mock_file_path = MagicMock()
        mock_file_path.with_suffix.return_value.name = "document.pdf"
        mock_file_path.unlink = MagicMock()
        mock_path_instance.glob.return_value = [mock_file_path]
        mock_path_class.return_value = mock_path_instance

        loader = OpenDataLoaderPDFLoader(
            file_path="document.pdf",
            format="text",
            hybrid="docling-fast",
            split_pages=False,
        )
        docs = list(loader.lazy_load())

        assert len(docs) == 1
        assert docs[0].metadata["hybrid"] == "docling-fast"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderHybridMetadata -v`
Expected: FAIL — `KeyError: 'hybrid'` for the include tests

- [ ] **Step 3: Implement metadata extension**

In `_split_into_pages()`, modify the metadata dict in both yield points. Find each `metadata={...}` block and add the hybrid spread after the last existing key:

```python
**({"hybrid": self.hybrid} if self.hybrid else {}),
```

Apply to all three methods that yield Documents:

1. **`_split_into_pages()`** — both yield points (the "before first separator" case and the page-number-matched case)
2. **`_split_json_into_pages()`** — the single yield point
3. **`lazy_load()` direct yield** — the `split_pages=False` branch (NOT the file cleanup except block)

Each metadata dict becomes like:

```python
metadata={
    "source": source_name,
    "format": self.format,
    "page": page_num,  # omitted in split_pages=False path
    **({"hybrid": self.hybrid} if self.hybrid else {}),
},
```

- [ ] **Step 4: Run metadata tests to verify they pass**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderHybridMetadata -v`
Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf
git add langchain_opendataloader_pdf/document_loaders.py tests/test_document_loaders.py
git commit -m "feat: include hybrid backend info in Document metadata"
```

---

### Task 4: Hybrid error re-raise behavior

**Files:**
- Test: `tests/test_document_loaders.py`
- Modify: `langchain_opendataloader_pdf/document_loaders.py` — the **outer** `except Exception` block at the end of `lazy_load()` (NOT the inner file cleanup except at `file.unlink()`)

**Dependency:** This task must complete before Task 5 integration tests will work (they depend on error re-raise behavior).

- [ ] **Step 1: Write failing test — hybrid error re-raise**

```python
class TestOpenDataLoaderPDFLoaderHybridErrors:
    """Test error behavior when hybrid mode is active."""

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_hybrid_error_reraise(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock(
            side_effect=RuntimeError("Hybrid backend unreachable")
        )

        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", hybrid="docling-fast"
        )
        with pytest.raises(RuntimeError, match="Hybrid backend unreachable"):
            list(loader.lazy_load())

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_non_hybrid_error_swallowed(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock(
            side_effect=RuntimeError("Some error")
        )

        loader = OpenDataLoaderPDFLoader(file_path="test.pdf")
        # Should NOT raise — existing silent behavior
        docs = list(loader.lazy_load())
        assert docs == []
```

- [ ] **Step 2: Run tests to verify the re-raise test fails**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderHybridErrors -v`
Expected: `test_hybrid_error_reraise` FAIL (error swallowed), `test_non_hybrid_error_swallowed` PASS

- [ ] **Step 3: Implement error re-raise for hybrid mode**

In `langchain_opendataloader_pdf/document_loaders.py`, change the except block (lines 284-285):

From:
```python
except Exception as e:
    logger.error(f"Error: {e}")
```

To:
```python
except Exception as e:
    if self.hybrid:
        raise
    logger.error(f"Error: {e}")
```

- [ ] **Step 4: Run both error tests to verify they pass**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py::TestOpenDataLoaderPDFLoaderHybridErrors -v`
Expected: 2 PASSED

- [ ] **Step 5: Run ALL unit tests to verify no regressions**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py -v`
Expected: All PASSED (original 45 + 13 new = 58)

- [ ] **Step 6: Commit**

```bash
cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf
git add langchain_opendataloader_pdf/document_loaders.py tests/test_document_loaders.py
git commit -m "feat: re-raise exceptions when hybrid mode fails"
```

---

## Chunk 2: Integration Tests + E2E Tests

### Task 5: Integration tests (Java-only, no hybrid server)

**Files:**
- Modify: `tests/test_integration.py`

- [ ] **Step 1: Write integration tests for fallback scenarios**

Add to `tests/test_integration.py`:

```python
class TestIntegrationHybridFallback:
    """Test hybrid fallback behavior with real Java engine (no hybrid server needed)."""

    def test_hybrid_fallback_on_bad_url(self, sample_pdf: Path):
        """fallback=True with unreachable URL should fall back to Java extraction."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            hybrid="docling-fast",
            hybrid_url="http://127.0.0.1:59999",  # unreachable port
            hybrid_fallback=True,
        )
        documents = loader.load()
        assert len(documents) >= 1
        assert len(documents[0].page_content) > 0

    def test_hybrid_no_fallback_on_bad_url(self, sample_pdf: Path):
        """fallback=False with unreachable URL should raise an exception."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            hybrid="docling-fast",
            hybrid_url="http://127.0.0.1:59999",  # unreachable port
            hybrid_fallback=False,
        )
        with pytest.raises(Exception):
            loader.load()
```

- [ ] **Step 2: Run integration tests (skip if no Java)**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_integration.py::TestIntegrationHybridFallback -v`
Expected: 2 PASSED (or SKIPPED if no Java)

- [ ] **Step 3: Commit**

```bash
cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf
git add tests/test_integration.py
git commit -m "test: add hybrid fallback integration tests"
```

---

### Task 6: E2E tests (requires hybrid server)

**Files:**
- Create: `tests/test_e2e_hybrid.py`

- [ ] **Step 1: Create E2E test file with fixtures and skip conditions**

```python
"""End-to-end tests for hybrid mode.

These tests require:
- Java 11+ available on PATH
- A running hybrid backend server (docling-fast)
- Sample PDF files in samples/pdf/

Set ODL_HYBRID_URL environment variable to override the default server URL.
"""

import os
import subprocess
import urllib.request
from pathlib import Path

import pytest

from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader


def java_available() -> bool:
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


HYBRID_URL = os.environ.get("ODL_HYBRID_URL", "http://localhost:5002")


def hybrid_server_available() -> bool:
    try:
        urllib.request.urlopen(HYBRID_URL, timeout=3)
        return True
    except Exception:
        return False


SAMPLES_DIR = Path(__file__).parent.parent / "samples" / "pdf"
SAMPLE_PDF = SAMPLES_DIR / "lorem.pdf"
MULTI_PAGE_PDF = SAMPLES_DIR / "2408.02509v1.pdf"

pytestmark = [
    pytest.mark.skipif(not java_available(), reason="Java 11+ required"),
    pytest.mark.skipif(
        not SAMPLE_PDF.exists(), reason=f"Sample PDF not found: {SAMPLE_PDF}"
    ),
    pytest.mark.skipif(
        not hybrid_server_available(),
        reason=f"Hybrid server not available at {HYBRID_URL}",
    ),
]


@pytest.fixture
def sample_pdf() -> Path:
    return SAMPLE_PDF


@pytest.fixture
def multi_page_pdf() -> Path:
    if not MULTI_PAGE_PDF.exists():
        pytest.skip(f"Multi-page PDF not found: {MULTI_PAGE_PDF}")
    return MULTI_PAGE_PDF


class TestE2EHybrid:
    """End-to-end tests with a real hybrid backend server."""

    def test_text_pdf_auto_mode(self, sample_pdf: Path):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            hybrid="docling-fast",
            hybrid_mode="auto",
            hybrid_url=HYBRID_URL,
        )
        docs = loader.load()
        assert len(docs) >= 1
        assert len(docs[0].page_content) > 0
        assert docs[0].metadata["hybrid"] == "docling-fast"

    def test_markdown_auto_mode(self, sample_pdf: Path):
        """Verify hybrid auto mode produces valid markdown output."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="markdown",
            quiet=True,
            hybrid="docling-fast",
            hybrid_mode="auto",
            hybrid_url=HYBRID_URL,
        )
        docs = loader.load()
        assert len(docs) >= 1
        assert len(docs[0].page_content) > 0
        assert docs[0].metadata["hybrid"] == "docling-fast"

    def test_full_mode(self, sample_pdf: Path):
        """Verify full mode routes all pages to backend and produces output."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            hybrid="docling-fast",
            hybrid_mode="full",
            hybrid_url=HYBRID_URL,
        )
        docs = loader.load()
        assert len(docs) >= 1
        assert len(docs[0].page_content) > 0
        assert docs[0].metadata["hybrid"] == "docling-fast"

    def test_split_pages_hybrid(self, multi_page_pdf: Path):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(multi_page_pdf),
            format="text",
            quiet=True,
            hybrid="docling-fast",
            hybrid_url=HYBRID_URL,
            split_pages=True,
        )
        docs = loader.load()
        assert len(docs) > 1
        for doc in docs:
            assert "page" in doc.metadata
            assert doc.metadata["hybrid"] == "docling-fast"

    def test_all_formats(self, sample_pdf: Path):
        for fmt in ["text", "markdown", "json", "html"]:
            loader = OpenDataLoaderPDFLoader(
                file_path=str(sample_pdf),
                format=fmt,
                quiet=True,
                hybrid="docling-fast",
                hybrid_url=HYBRID_URL,
                split_pages=False,
            )
            docs = loader.load()
            assert len(docs) >= 1, f"No documents for format={fmt}"
            assert len(docs[0].page_content) > 0, f"Empty content for format={fmt}"

    def test_fallback_bad_url(self, sample_pdf: Path):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            hybrid="docling-fast",
            hybrid_url="http://127.0.0.1:59999",
            hybrid_fallback=True,
        )
        docs = loader.load()
        assert len(docs) >= 1

    def test_no_fallback_bad_url(self, sample_pdf: Path):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            hybrid="docling-fast",
            hybrid_url="http://127.0.0.1:59999",
            hybrid_fallback=False,
        )
        with pytest.raises(Exception):
            loader.load()

    def test_timeout_short(self, sample_pdf: Path):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            hybrid="docling-fast",
            hybrid_url=HYBRID_URL,
            hybrid_timeout="1",  # 1ms — should timeout
            hybrid_fallback=False,
        )
        with pytest.raises(Exception):
            loader.load()
```

- [ ] **Step 2: Run E2E tests (will skip if no server)**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_e2e_hybrid.py -v`
Expected: 8 PASSED or SKIPPED

- [ ] **Step 3: Commit**

```bash
cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf
git add tests/test_e2e_hybrid.py
git commit -m "test: add hybrid E2E tests (requires running hybrid server)"
```

---

## Chunk 3: README Update

### Task 7: Update README with hybrid documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add hybrid usage example section**

After the "### Image Handling" section (line 170), add:

```markdown
### Hybrid AI Mode

For complex documents (tables, charts, scanned content), hybrid mode routes pages to an AI backend for better accuracy while keeping simple pages on the fast local engine:

```python
# Requires a running docling-fast server (default: localhost:5002)
loader = OpenDataLoaderPDFLoader(
    file_path="complex_report.pdf",
    format="markdown",
    hybrid="docling-fast",          # Enable hybrid extraction
    hybrid_mode="auto",             # Auto-triage: only complex pages go to backend
    hybrid_url="http://localhost:5002",
)
documents = loader.load()

# Document metadata shows which backend was used
print(documents[0].metadata)
# {'source': 'complex_report.pdf', 'format': 'markdown', 'page': 1, 'hybrid': 'docling-fast'}
```
```

- [ ] **Step 2: Add hybrid params to parameters reference table**

After the `replace_invalid_chars` row (line 232), add:

```markdown
| `hybrid` | `str` | `None` | Hybrid AI backend: `"docling-fast"`. Requires running backend server |
| `hybrid_mode` | `str` | `None` | `"auto"` (route complex pages) or `"full"` (route all pages) |
| `hybrid_url` | `str` | `None` | Backend server URL. Default: `http://localhost:5002` |
| `hybrid_timeout` | `str` | `None` | Backend timeout in ms. Default: `"30000"` |
| `hybrid_fallback` | `bool` | `False` | Fall back to Java extraction on backend failure |
```

- [ ] **Step 3: Update metadata docs to mention hybrid**

After line 241 (`# {'source': 'document.pdf', 'format': 'text', 'page': 1}`), add:

```markdown
# When hybrid mode is active:
# {'source': 'document.pdf', 'format': 'text', 'page': 1, 'hybrid': 'docling-fast'}
```

- [ ] **Step 4: Commit**

```bash
cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf
git add README.md
git commit -m "docs: add hybrid mode usage examples and parameter reference"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run all unit tests**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_document_loaders.py -v`
Expected: All 58 tests PASSED

- [ ] **Step 2: Run all integration tests (if Java available)**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_integration.py -v`
Expected: All PASSED or SKIPPED

- [ ] **Step 3: Run E2E tests (if hybrid server available)**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/test_e2e_hybrid.py -v`
Expected: All PASSED or SKIPPED

- [ ] **Step 4: Run full test suite**

Run: `cd /Users/benedict/Workspace/opendataloader-project/langchain-opendataloader-pdf && python -m pytest tests/ -v`
Expected: All PASSED or SKIPPED, 0 FAILED
