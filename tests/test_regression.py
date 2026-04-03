"""Regression tests: verify output consistency across versions.

These tests ensure the same PDF always produces the same output.
If output changes intentionally (e.g., better extraction), update the snapshots
by running: UPDATE_SNAPSHOTS=1 pytest tests/test_regression.py

Requires Java 11+ and sample PDFs.
"""

import json
import os
from pathlib import Path

import pytest

from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader
from tests.conftest import java_available

UPDATE_SNAPSHOTS = os.environ.get("UPDATE_SNAPSHOTS") == "1"


SAMPLES_DIR = Path(__file__).parent.parent / "samples" / "pdf"
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"
LOREM_PDF = SAMPLES_DIR / "lorem.pdf"

pytestmark = [
    pytest.mark.skipif(not java_available(), reason="Java 11+ required"),
    pytest.mark.skipif(not LOREM_PDF.exists(), reason=f"Sample PDF not found: {LOREM_PDF}"),
]


@pytest.fixture(autouse=True)
def ensure_snapshots_dir():
    SNAPSHOTS_DIR.mkdir(exist_ok=True)


class TestRegressionText:
    """Verify text output hasn't changed unexpectedly."""

    SNAPSHOT_FILE = SNAPSHOTS_DIR / "lorem_text.txt"

    def test_text_output_matches_snapshot(self):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(LOREM_PDF), format="text", quiet=True, split_pages=False
        )
        docs = loader.load()
        assert len(docs) == 1
        actual = docs[0].page_content.strip()

        if not self.SNAPSHOT_FILE.exists():
            if UPDATE_SNAPSHOTS:
                self.SNAPSHOT_FILE.write_text(actual, encoding="utf-8")
                pytest.skip("Snapshot created, run again to verify")
            else:
                pytest.fail(f"Snapshot missing: {self.SNAPSHOT_FILE}. Run with UPDATE_SNAPSHOTS=1 to create.")

        expected = self.SNAPSHOT_FILE.read_text(encoding="utf-8").strip()
        assert actual == expected, (
            f"Text output changed! If intentional, delete {self.SNAPSHOT_FILE} and re-run.\n"
            f"Expected length: {len(expected)}, Actual length: {len(actual)}"
        )


class TestRegressionMarkdown:
    """Verify markdown output hasn't changed unexpectedly."""

    SNAPSHOT_FILE = SNAPSHOTS_DIR / "lorem_markdown.md"

    def test_markdown_output_matches_snapshot(self):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(LOREM_PDF), format="markdown", quiet=True, split_pages=False
        )
        docs = loader.load()
        assert len(docs) == 1
        actual = docs[0].page_content.strip()

        if not self.SNAPSHOT_FILE.exists():
            if UPDATE_SNAPSHOTS:
                self.SNAPSHOT_FILE.write_text(actual, encoding="utf-8")
                pytest.skip("Snapshot created, run again to verify")
            else:
                pytest.fail(f"Snapshot missing: {self.SNAPSHOT_FILE}. Run with UPDATE_SNAPSHOTS=1 to create.")

        expected = self.SNAPSHOT_FILE.read_text(encoding="utf-8").strip()
        assert actual == expected, (
            f"Markdown output changed! If intentional, delete {self.SNAPSHOT_FILE} and re-run."
        )


class TestRegressionJson:
    """Verify JSON structure hasn't changed unexpectedly."""

    SNAPSHOT_FILE = SNAPSHOTS_DIR / "lorem_json.json"

    def test_json_structure_matches_snapshot(self):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(LOREM_PDF), format="json", quiet=True, split_pages=False
        )
        docs = loader.load()
        assert len(docs) == 1
        actual_data = json.loads(docs[0].page_content)

        if not self.SNAPSHOT_FILE.exists():
            if UPDATE_SNAPSHOTS:
                self.SNAPSHOT_FILE.write_text(
                    json.dumps(actual_data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                pytest.skip("Snapshot created, run again to verify")
            else:
                pytest.fail(f"Snapshot missing: {self.SNAPSHOT_FILE}. Run with UPDATE_SNAPSHOTS=1 to create.")

        expected_data = json.loads(self.SNAPSHOT_FILE.read_text(encoding="utf-8"))

        # Compare structure: same keys and types, not exact values
        # (minor text extraction improvements shouldn't break this)
        assert set(actual_data.keys()) == set(expected_data.keys()), "Top-level keys changed"
        if "kids" in actual_data:
            assert len(actual_data["kids"]) == len(expected_data["kids"]), (
                f"Number of elements changed: {len(actual_data['kids'])} vs {len(expected_data['kids'])}"
            )


class TestRegressionMetadata:
    """Verify metadata structure is consistent."""

    def test_metadata_keys_consistent(self):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(LOREM_PDF), format="text", quiet=True, split_pages=True
        )
        docs = loader.load()
        assert len(docs) > 0, "Expected at least one document from lorem.pdf"
        for doc in docs:
            assert set(doc.metadata.keys()) == {"source", "format", "page"}
            assert isinstance(doc.metadata["page"], int)
            assert doc.metadata["format"] == "text"
            assert Path(doc.metadata["source"]).name == "lorem.pdf"

    def test_metadata_no_page_when_no_split(self):
        loader = OpenDataLoaderPDFLoader(
            file_path=str(LOREM_PDF), format="text", quiet=True, split_pages=False
        )
        docs = loader.load()
        assert set(docs[0].metadata.keys()) == {"source", "format"}


class TestConcurrency:
    """Verify multiple loader instances don't interfere."""

    def test_sequential_loaders_no_conflict(self):
        """Two loaders running sequentially should not interfere with each other."""
        loader1 = OpenDataLoaderPDFLoader(
            file_path=str(LOREM_PDF), format="text", quiet=True
        )
        loader2 = OpenDataLoaderPDFLoader(
            file_path=str(LOREM_PDF), format="markdown", quiet=True
        )

        docs1 = loader1.load()
        docs2 = loader2.load()

        assert len(docs1) >= 1
        assert len(docs2) >= 1
        assert docs1[0].metadata["format"] == "text"
        assert docs2[0].metadata["format"] == "markdown"
        # Content should differ (different formats)
        assert docs1[0].page_content != docs2[0].page_content
