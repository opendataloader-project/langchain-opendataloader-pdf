"""Integration tests for OpenDataLoaderPDFLoader.

These tests require Java 11+ and actual PDF files to run.
They are skipped if the required resources are not available.
"""

import subprocess
from pathlib import Path

import pytest

from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader


def java_available() -> bool:
    """Check if Java is available on the system."""
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


SAMPLES_DIR = Path(__file__).parent.parent / "samples" / "pdf"
SAMPLE_PDF = SAMPLES_DIR / "lorem.pdf"  # 1 page
MULTI_PAGE_PDF = SAMPLES_DIR / "2408.02509v1.pdf"  # Multi-page PDF


# Skip all tests in this module if Java is not available or sample PDF is missing
pytestmark = [
    pytest.mark.skipif(
        not java_available(),
        reason="Java 11+ is required for integration tests",
    ),
    pytest.mark.skipif(
        not SAMPLE_PDF.exists(),
        reason=f"Sample PDF not found: {SAMPLE_PDF}",
    ),
]


@pytest.fixture
def sample_pdf() -> Path:
    """Return the path to the sample PDF file (1 page)."""
    return SAMPLE_PDF


@pytest.fixture
def multi_page_pdf() -> Path:
    """Return the path to a multi-page PDF file."""
    return MULTI_PAGE_PDF


@pytest.fixture
def sample_pdfs() -> list[Path]:
    """Return paths to all sample PDF files."""
    return list(SAMPLES_DIR.glob("*.pdf"))


class TestIntegrationBasic:
    """Basic integration tests."""

    def test_load_pdf_as_text(self, sample_pdf: Path):
        """Test loading a PDF and getting text output."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
        )
        documents = loader.load()

        assert len(documents) >= 1
        assert len(documents[0].page_content) > 0
        assert documents[0].metadata["format"] == "text"

    def test_load_pdf_as_json(self, sample_pdf: Path):
        """Test loading a PDF and getting JSON output (split_pages=False)."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="json",
            quiet=True,
            split_pages=False,
        )
        documents = loader.load()

        assert len(documents) == 1
        assert documents[0].metadata["format"] == "json"
        # JSON output should be parseable
        import json

        data = json.loads(documents[0].page_content)
        assert isinstance(data, (dict, list))

    def test_load_pdf_as_markdown(self, sample_pdf: Path):
        """Test loading a PDF and getting Markdown output."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="markdown",
            quiet=True,
        )
        documents = loader.load()

        assert len(documents) >= 1
        assert documents[0].metadata["format"] == "markdown"

    def test_load_pdf_as_html(self, sample_pdf: Path):
        """Test loading a PDF and getting HTML output."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="html",
            quiet=True,
        )
        documents = loader.load()

        assert len(documents) >= 1
        assert documents[0].metadata["format"] == "html"


class TestIntegrationWithOptions:
    """Integration tests with various options."""

    def test_load_with_keep_line_breaks(self, sample_pdf: Path):
        """Test loading with keep_line_breaks option."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            keep_line_breaks=True,
        )
        documents = loader.load()
        assert len(documents) == 1

    def test_load_with_use_struct_tree(self, sample_pdf: Path):
        """Test loading with use_struct_tree option."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            use_struct_tree=True,
        )
        documents = loader.load()
        assert len(documents) == 1

    def test_load_with_reading_order_off(self, sample_pdf: Path):
        """Test loading with reading_order=off."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            reading_order="off",
        )
        documents = loader.load()
        assert len(documents) == 1

    def test_load_with_page_separator(self, sample_pdf: Path):
        """Test loading with page separator."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            text_page_separator="--- Page %page-number% ---",
            split_pages=False,
        )
        documents = loader.load()
        assert len(documents) == 1

    def test_load_with_image_options(self, sample_pdf: Path):
        """Test loading with image options."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="markdown",
            quiet=True,
            image_output="off",
        )
        documents = loader.load()
        assert len(documents) == 1

    def test_load_with_table_method_cluster(self, sample_pdf: Path):
        """Test loading with table_method=cluster."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="json",
            quiet=True,
            table_method="cluster",
        )
        documents = loader.load()
        assert len(documents) == 1

    def test_load_multiple_files(self, sample_pdfs: list[Path]):
        """Test loading multiple PDF files."""
        if len(sample_pdfs) < 2:
            pytest.skip("Need at least 2 sample PDFs")

        loader = OpenDataLoaderPDFLoader(
            file_path=[str(p) for p in sample_pdfs[:2]],
            format="text",
            quiet=True,
            split_pages=False,
        )
        documents = loader.load()

        assert len(documents) == 2


class TestIntegrationLazyLoad:
    """Test lazy loading functionality."""

    def test_lazy_load_yields_documents(self, sample_pdf: Path):
        """Test that lazy_load yields documents one at a time."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
        )

        docs = list(loader.lazy_load())
        assert len(docs) == 1
        assert docs[0].page_content  # Not empty


class TestIntegrationContent:
    """Test content extraction quality."""

    def test_lorem_ipsum_content(self, sample_pdf: Path):
        """Test that lorem ipsum PDF contains expected text."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            split_pages=False,
        )
        documents = loader.load()

        assert len(documents) == 1
        content = documents[0].page_content.lower()
        # Lorem ipsum should contain these words
        assert "lorem" in content or "ipsum" in content or len(content) > 100


class TestIntegrationSplitPages:
    """Test split_pages functionality with real PDFs."""

    def test_split_pages_text_format(self, multi_page_pdf: Path):
        """Test split_pages with text format on multi-page PDF."""
        if not multi_page_pdf.exists():
            pytest.skip(f"Multi-page PDF not found: {multi_page_pdf}")

        loader = OpenDataLoaderPDFLoader(
            file_path=str(multi_page_pdf),
            format="text",
            quiet=True,
            split_pages=True,
        )
        documents = loader.load()

        # Multi-page PDF should produce multiple documents
        assert len(documents) > 1
        # Each document should have page metadata
        for doc in documents:
            assert "page" in doc.metadata
            assert doc.metadata["format"] == "text"
            assert len(doc.page_content) > 0

    def test_split_pages_markdown_format(self, multi_page_pdf: Path):
        """Test split_pages with markdown format on multi-page PDF."""
        if not multi_page_pdf.exists():
            pytest.skip(f"Multi-page PDF not found: {multi_page_pdf}")

        loader = OpenDataLoaderPDFLoader(
            file_path=str(multi_page_pdf),
            format="markdown",
            quiet=True,
            split_pages=True,
        )
        documents = loader.load()

        assert len(documents) > 1
        for doc in documents:
            assert "page" in doc.metadata
            assert doc.metadata["format"] == "markdown"

    def test_split_pages_json_format(self, multi_page_pdf: Path):
        """Test split_pages with JSON format extracts text per page."""
        if not multi_page_pdf.exists():
            pytest.skip(f"Multi-page PDF not found: {multi_page_pdf}")

        loader = OpenDataLoaderPDFLoader(
            file_path=str(multi_page_pdf),
            format="json",
            quiet=True,
            split_pages=True,
        )
        documents = loader.load()

        assert len(documents) > 1
        for doc in documents:
            assert "page" in doc.metadata
            assert doc.metadata["format"] == "json"
            # Content should be extracted text, not raw JSON
            assert len(doc.page_content) > 0

    def test_split_pages_html_format(self, multi_page_pdf: Path):
        """Test split_pages with HTML format on multi-page PDF."""
        if not multi_page_pdf.exists():
            pytest.skip(f"Multi-page PDF not found: {multi_page_pdf}")

        loader = OpenDataLoaderPDFLoader(
            file_path=str(multi_page_pdf),
            format="html",
            quiet=True,
            split_pages=True,
        )
        documents = loader.load()

        assert len(documents) > 1
        for doc in documents:
            assert "page" in doc.metadata
            assert doc.metadata["format"] == "html"

    def test_split_pages_page_numbers_sequential(self, multi_page_pdf: Path):
        """Test that page numbers are sequential on multi-page PDF."""
        if not multi_page_pdf.exists():
            pytest.skip(f"Multi-page PDF not found: {multi_page_pdf}")

        loader = OpenDataLoaderPDFLoader(
            file_path=str(multi_page_pdf),
            format="text",
            quiet=True,
            split_pages=True,
        )
        documents = loader.load()

        assert len(documents) > 1
        page_numbers = [doc.metadata["page"] for doc in documents]
        # Page numbers should be sequential (may have gaps for empty pages)
        assert page_numbers == sorted(page_numbers)
        assert page_numbers[0] == 1

    def test_split_pages_false_returns_single_document(self, multi_page_pdf: Path):
        """Test that split_pages=False returns a single document per file."""
        if not multi_page_pdf.exists():
            pytest.skip(f"Multi-page PDF not found: {multi_page_pdf}")

        loader = OpenDataLoaderPDFLoader(
            file_path=str(multi_page_pdf),
            format="text",
            quiet=True,
            split_pages=False,
        )
        documents = loader.load()

        assert len(documents) == 1
        assert "page" not in documents[0].metadata

    def test_single_page_pdf_returns_one_document(self, sample_pdf: Path):
        """Test that a single-page PDF returns exactly one document."""
        loader = OpenDataLoaderPDFLoader(
            file_path=str(sample_pdf),
            format="text",
            quiet=True,
            split_pages=True,
        )
        documents = loader.load()

        assert len(documents) == 1
        assert documents[0].metadata["page"] == 1
