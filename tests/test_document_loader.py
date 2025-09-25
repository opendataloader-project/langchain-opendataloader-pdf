import json
from pathlib import Path

import pytest
from langchain_core.documents import Document

# Import the loader class to be tested.
# This path might need to be adjusted based on your actual project structure.
from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader


# --- Snapshot Management ---
# Set to True to generate/update snapshot files.
# Set to False to compare results against existing snapshots.
GEN_SNAPSHOTS = True
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _load_or_generate_snapshot(snapshot_file: Path, actual_data: dict):
    """Load a snapshot or generate a new one if GEN_SNAPSHOTS is True."""
    if GEN_SNAPSHOTS:
        snapshot_file.parent.mkdir(exist_ok=True)
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(actual_data, f, indent=4)
        return actual_data  # In generation mode, the test always passes.
    else:
        if not snapshot_file.exists():
            pytest.fail(
                f"Snapshot file not found: {snapshot_file}. "
                "Run with GEN_SNAPSHOTS=True to create it."
            )
        with open(snapshot_file, "r", encoding="utf-8") as f:
            return json.load(f)


def test_load_as_json_chunks(monkeypatch: pytest.MonkeyPatch):
    """
    Test the loader in its default JSON parsing mode.
    Mocks the opendataloader_pdf.run call and compares the output to a snapshot.
    """
    # 1. Setup Mock: Define the mock JSON data to be returned by opendataloader_pdf.run.
    mock_json_output = json.dumps(
        {
            "kids": [
                {
                    "content": "Top-level paragraph.",
                    "page number": 1,
                    "type": "paragraph",
                },
                {
                    "type": "text block",
                    "page number": 1,
                    "kids": [
                        {
                            "content": "Nested paragraph.",
                            "page number": 1,
                            "type": "paragraph",
                        }
                    ],
                },
            ]
        }
    )

    # Use monkeypatch to intercept the opendataloader_pdf.run function.
    # The string path must match where the 'run' function is imported in your loader file.
    monkeypatch.setattr(
        "langchain_opendataloader_pdf.document_loaders.opendataloader_pdf.run",
        lambda *args, **kwargs: mock_json_output,
    )

    # 2. Execute the loader.
    loader = OpenDataLoaderPDFLoader("dummy.pdf", no_json=False)
    actual_docs = list(loader.lazy_load())

    # 3. Verify the results.
    # Convert the list of Document objects into a serializable dictionary.
    actual_data = {"documents": [doc.model_dump() for doc in actual_docs]}

    # Compare the actual data against the snapshot.
    snapshot_file = SNAPSHOT_DIR / "test_load_as_json_chunks.json"
    expected_data = _load_or_generate_snapshot(snapshot_file, actual_data)

    assert actual_data == expected_data
    # Add a basic assertion for extra validation.
    assert len(actual_docs) == 2


def test_load_as_raw_text(monkeypatch: pytest.MonkeyPatch):
    """
    Test the raw text mode (no_json=True).
    Mocks the opendataloader_pdf.run call and compares the output to a snapshot.
    """
    # 1. Setup Mock
    mock_raw_output = "This is the raw text output from the PDF."
    monkeypatch.setattr(
        "langchain_opendataloader_pdf.document_loaders.opendataloader_pdf.run",
        lambda *args, **kwargs: mock_raw_output,
    )

    # 2. Execute the loader.
    loader = OpenDataLoaderPDFLoader("dummy.pdf", no_json=True)
    actual_docs = list(loader.lazy_load())

    # 3. Verify the results.
    actual_data = {"documents": [doc.model_dump() for doc in actual_docs]}

    snapshot_file = SNAPSHOT_DIR / "test_load_as_raw_text.json"
    expected_data = _load_or_generate_snapshot(snapshot_file, actual_data)

    assert actual_data == expected_data
    assert len(actual_docs) == 1
    assert actual_docs[0].page_content == mock_raw_output
