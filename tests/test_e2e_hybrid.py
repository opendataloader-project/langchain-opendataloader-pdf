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
