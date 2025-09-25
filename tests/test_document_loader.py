import json
from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from langchain_opendataloader_pdf.document_loaders import OpenDataLoaderPDFLoader

# Mock JSON output simulating a result from the opendataloader-pdf tool.
# This includes nested structures to test recursive parsing.
MOCK_JSON_OUTPUT = json.dumps(
    {
        "kids": [
            {"type": "Title", "content": "Document Title", "page number": 1, "kids": []},
            {
                "type": "Para",
                "content": "This is the first paragraph.",
                "page number": 1,
            },
            {
                "type": "Section",
                "content": "Section 1",
                "page number": 2,
                "kids": [
                    {
                        "type": "Para",
                        "content": "Paragraph within Section 1.",
                        "page number": 2,
                    }
                ],
            },
            {"type": "Para", "content": "Final paragraph.", "page number": 3},
        ]
    }
)

MOCK_TEXT_OUTPUT = "This is a plain text output from the PDF."

MOCK_INVALID_JSON_OUTPUT = '''{"key": "value", "unterminated... '''


@pytest.fixture
def mock_run(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Fixture to mock the opendataloader_pdf.run function."""
    mock = MagicMock()
    # The loader imports `opendataloader_pdf` and calls `run` on it.
    # So we need to patch it in the loader's module namespace.
    monkeypatch.setattr(
        "langchain_opendataloader_pdf.document_loaders.opendataloader_pdf.run", mock
    )
    return mock


def test_load_with_json_parsing(mock_run: MagicMock) -> None:
    """
    Tests that the loader correctly parses a valid JSON output and creates
    multiple documents recursively.
    """
    mock_run.return_value = MOCK_JSON_OUTPUT
    file_path = "dummy.pdf"

    loader = OpenDataLoaderPDFLoader(file_path=file_path)
    docs = list(loader.lazy_load())

    # We expect 5 documents from the MOCK_JSON_OUTPUT based on the "content" fields
    assert len(docs) == 5

    expected_docs = [
        Document(
            page_content="Document Title",
            metadata={"page": 1, "type": "Title", "source": file_path},
        ),
        Document(
            page_content="This is the first paragraph.",
            metadata={"page": 1, "type": "Para", "source": file_path},
        ),
        Document(
            page_content="Section 1",
            metadata={"page": 2, "type": "Section", "source": file_path},
        ),
        Document(
            page_content="Paragraph within Section 1.",
            metadata={"page": 2, "type": "Para", "source": file_path},
        ),
        Document(
            page_content="Final paragraph.",
            metadata={"page": 3, "type": "Para", "source": file_path},
        ),
    ]

    # Compare the list of Document objects
    assert docs == expected_docs

    # Verify that the mock was called correctly
    mock_run.assert_called_once_with(input_path=file_path, no_json=False)


def test_load_with_no_json(mock_run: MagicMock) -> None:
    """
    Tests that the loader returns the entire output as a single document
    when no_json=True.
    """
    mock_run.return_value = MOCK_TEXT_OUTPUT
    file_path = "dummy.pdf"

    loader = OpenDataLoaderPDFLoader(file_path=file_path, no_json=True)
    docs = list(loader.lazy_load())

    assert len(docs) == 1
    assert docs[0].page_content == MOCK_TEXT_OUTPUT
    assert docs[0].metadata == {"source": file_path}

    # Verify that the mock was called correctly
    mock_run.assert_called_once_with(input_path=file_path, no_json=True)


def test_load_with_invalid_json(mock_run: MagicMock) -> None:
    """
    Tests that the loader gracefully handles a JSONDecodeError and returns
    the raw output as a single document.
    """
    mock_run.return_value = MOCK_INVALID_JSON_OUTPUT
    file_path = "dummy.pdf"

    loader = OpenDataLoaderPDFLoader(file_path=file_path)
    docs = list(loader.lazy_load())

    # Should fall back to treating the output as a single text block
    assert len(docs) == 1
    assert docs[0].page_content == MOCK_INVALID_JSON_OUTPUT
    assert docs[0].metadata == {"source": file_path}

    mock_run.assert_called_once_with(input_path=file_path, no_json=False)


def test_loader_passes_extra_args(mock_run: MagicMock) -> None:
    """
    Tests that extra arguments passed to the loader are correctly
    forwarded to the opendataloader_pdf.run function.
    """
    mock_run.return_value = MOCK_TEXT_OUTPUT
    file_path = "dummy.pdf"

    # This test uses the **kwargs feature
    loader = OpenDataLoaderPDFLoader(
        file_path=file_path,
        no_json=True,
        password="test_password",
        generate_markdown=True,
    )
    list(loader.lazy_load())

    # Verify that the mock was called with the extra arguments.
    # Note: This test works because MagicMock accepts any arguments.
    # It correctly tests that the loader passes the arguments on.
    mock_run.assert_called_once_with(
        input_path=file_path,
        no_json=True,
        password="test_password",
        generate_markdown=True,
    )