"""Unit tests for OpenDataLoaderPDFLoader."""

from unittest.mock import patch, MagicMock
import pytest

from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader


class TestOpenDataLoaderPDFLoaderInit:
    """Test initialization and parameter handling."""

    def test_init_with_single_file_path(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf")
        assert loader.file_paths == ["test.pdf"]

    def test_init_with_multiple_file_paths(self):
        loader = OpenDataLoaderPDFLoader(file_path=["a.pdf", "b.pdf"])
        assert loader.file_paths == ["a.pdf", "b.pdf"]

    def test_init_default_format(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf")
        assert loader.format == "text"

    def test_init_with_format(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", format="json")
        assert loader.format == "json"

    def test_init_format_case_insensitive(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", format="JSON")
        assert loader.format == "json"

    def test_init_with_quiet(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", quiet=True)
        assert loader.quiet is True

    def test_init_with_content_safety_off(self):
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", content_safety_off=["hidden-text", "off-page"]
        )
        assert loader.content_safety_off == ["hidden-text", "off-page"]

    # New options tests
    def test_init_with_password(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", password="secret123")
        assert loader.password == "secret123"

    def test_init_with_keep_line_breaks(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", keep_line_breaks=True)
        assert loader.keep_line_breaks is True

    def test_init_with_replace_invalid_chars(self):
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", replace_invalid_chars="?"
        )
        assert loader.replace_invalid_chars == "?"

    def test_init_with_use_struct_tree(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", use_struct_tree=True)
        assert loader.use_struct_tree is True

    def test_init_with_table_method(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", table_method="cluster")
        assert loader.table_method == "cluster"

    def test_init_with_reading_order(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", reading_order="off")
        assert loader.reading_order == "off"

    def test_init_with_page_separators(self):
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf",
            markdown_page_separator="---",
            text_page_separator="\n\n",
            html_page_separator="<hr/>",
        )
        assert loader.markdown_page_separator == "---"
        assert loader.text_page_separator == "\n\n"
        assert loader.html_page_separator == "<hr/>"

    def test_init_with_image_options(self):
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", image_output="embedded", image_format="jpeg"
        )
        assert loader.image_output == "embedded"
        assert loader.image_format == "jpeg"

    def test_init_defaults_for_new_options(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf")
        assert loader.password is None
        assert loader.keep_line_breaks is False
        assert loader.replace_invalid_chars is None
        assert loader.use_struct_tree is False
        assert loader.table_method is None
        assert loader.reading_order is None
        assert loader.markdown_page_separator is None
        assert loader.text_page_separator is None
        assert loader.html_page_separator is None
        assert loader.image_output is None
        assert loader.image_format is None


class TestOpenDataLoaderPDFLoaderConvertCall:
    """Test that convert() is called with correct arguments."""

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_basic_options(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", format="text", quiet=True
        )
        list(loader.lazy_load())

        mock_odl.convert.assert_called_once()
        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["input_path"] == ["test.pdf"]
        assert call_kwargs["format"] == ["text"]
        assert call_kwargs["quiet"] is True

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_password(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", password="secret")
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["password"] == "secret"

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_keep_line_breaks(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", keep_line_breaks=True)
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["keep_line_breaks"] is True

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_use_struct_tree(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", use_struct_tree=True)
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["use_struct_tree"] is True

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_table_method(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", table_method="cluster")
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["table_method"] == "cluster"

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_reading_order(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", reading_order="off")
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["reading_order"] == "off"

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_page_separators(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf",
            markdown_page_separator="---",
            text_page_separator="\n\n",
            html_page_separator="<hr/>",
            split_pages=False,
        )
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["markdown_page_separator"] == "---"
        assert call_kwargs["text_page_separator"] == "\n\n"
        assert call_kwargs["html_page_separator"] == "<hr/>"

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_image_options(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", image_output="embedded", image_format="jpeg"
        )
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["image_output"] == "embedded"
        assert call_kwargs["image_format"] == "jpeg"

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_replace_invalid_chars(self, mock_mkdtemp, mock_odl):
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", replace_invalid_chars="?"
        )
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["replace_invalid_chars"] == "?"

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_convert_passes_all_options_together(self, mock_mkdtemp, mock_odl):
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
            markdown_page_separator="---",
            image_output="embedded",
            image_format="jpeg",
            split_pages=False,
        )
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["input_path"] == ["a.pdf", "b.pdf"]
        assert call_kwargs["format"] == ["markdown"]
        assert call_kwargs["quiet"] is True
        assert call_kwargs["password"] == "secret"
        assert call_kwargs["content_safety_off"] == ["hidden-text"]
        assert call_kwargs["keep_line_breaks"] is True
        assert call_kwargs["replace_invalid_chars"] == "?"
        assert call_kwargs["use_struct_tree"] is True
        assert call_kwargs["table_method"] == "cluster"
        assert call_kwargs["reading_order"] == "xycut"
        assert call_kwargs["markdown_page_separator"] == "---"
        assert call_kwargs["image_output"] == "embedded"
        assert call_kwargs["image_format"] == "jpeg"


class TestOpenDataLoaderPDFLoaderValidation:
    """Test format validation."""

    def test_invalid_format_raises_error(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", format="invalid")
        with pytest.raises(ValueError, match="Invalid format"):
            list(loader.lazy_load())

    def test_valid_formats_accepted(self):
        for fmt in ["json", "text", "html", "markdown"]:
            loader = OpenDataLoaderPDFLoader(file_path="test.pdf", format=fmt)
            assert loader.format == fmt



class TestOpenDataLoaderPDFLoaderSplitPages:
    """Test split_pages functionality."""

    def test_init_with_split_pages(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", split_pages=True)
        assert loader.split_pages is True

    def test_init_default_split_pages(self):
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf")
        assert loader.split_pages is True

    def test_split_into_pages_basic(self):
        """Test that _split_into_pages correctly splits content."""
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", split_pages=True)

        content = (
            "Page 1 content"
            "\n<<<ODL_PAGE_BREAK_2>>>\n"
            "Page 2 content"
            "\n<<<ODL_PAGE_BREAK_3>>>\n"
            "Page 3 content"
        )

        docs = list(loader._split_into_pages(content, "test.pdf"))

        assert len(docs) == 3
        assert docs[0].page_content == "Page 1 content"
        assert docs[0].metadata["page"] == 1
        assert docs[0].metadata["source"] == "test.pdf"
        assert docs[1].page_content == "Page 2 content"
        assert docs[1].metadata["page"] == 2
        assert docs[2].page_content == "Page 3 content"
        assert docs[2].metadata["page"] == 3

    def test_split_into_pages_single_page(self):
        """Test that single page content returns one document."""
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", split_pages=True)

        content = "Single page content only"

        docs = list(loader._split_into_pages(content, "test.pdf"))

        assert len(docs) == 1
        assert docs[0].page_content == "Single page content only"
        assert docs[0].metadata["page"] == 1

    def test_split_into_pages_skips_empty(self):
        """Test that empty pages are skipped."""
        loader = OpenDataLoaderPDFLoader(file_path="test.pdf", split_pages=True)

        content = (
            "Page 1 content"
            "\n<<<ODL_PAGE_BREAK_2>>>\n"
            "   "  # Empty/whitespace page
            "\n<<<ODL_PAGE_BREAK_3>>>\n"
            "Page 3 content"
        )

        docs = list(loader._split_into_pages(content, "test.pdf"))

        assert len(docs) == 2
        assert docs[0].metadata["page"] == 1
        assert docs[1].metadata["page"] == 3

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_split_pages_sets_page_separator(self, mock_mkdtemp, mock_odl):
        """Test that split_pages=True sets the internal page separator."""
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", format="text", split_pages=True
        )
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["text_page_separator"] == loader._PAGE_SPLIT_SEPARATOR

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    def test_split_pages_markdown_sets_separator(self, mock_mkdtemp, mock_odl):
        """Test that split_pages=True with markdown format sets markdown separator."""
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", format="markdown", split_pages=True
        )
        list(loader.lazy_load())

        call_kwargs = mock_odl.convert.call_args[1]
        assert call_kwargs["markdown_page_separator"] == loader._PAGE_SPLIT_SEPARATOR

    @patch("langchain_opendataloader_pdf.document_loaders.opendataloader_pdf")
    @patch("langchain_opendataloader_pdf.document_loaders.tempfile.mkdtemp")
    @patch("builtins.open", create=True)
    @patch("langchain_opendataloader_pdf.document_loaders.Path")
    def test_split_pages_yields_multiple_documents(
        self, mock_path_class, mock_open, mock_mkdtemp, mock_odl
    ):
        """Test that split_pages=True yields multiple documents from one file."""
        mock_mkdtemp.return_value = "/tmp/test"
        mock_odl.convert = MagicMock()

        # Mock file content with page separators
        mock_file_content = (
            "First page content"
            "\n<<<ODL_PAGE_BREAK_2>>>\n"
            "Second page content"
            "\n<<<ODL_PAGE_BREAK_3>>>\n"
            "Third page content"
        )

        # Create mock file object
        mock_file = MagicMock()
        mock_file.name = "document.txt"
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.read.return_value = mock_file_content

        mock_open.return_value = mock_file

        # Create mock Path
        mock_path_instance = MagicMock()
        mock_file_path = MagicMock()
        mock_file_path.with_suffix.return_value.name = "document.pdf"
        mock_file_path.unlink = MagicMock()
        mock_path_instance.glob.return_value = [mock_file_path]
        mock_path_class.return_value = mock_path_instance

        loader = OpenDataLoaderPDFLoader(
            file_path="document.pdf", format="text", split_pages=True
        )
        docs = list(loader.lazy_load())

        assert len(docs) == 3
        assert docs[0].page_content == "First page content"
        assert docs[0].metadata["page"] == 1
        assert docs[1].page_content == "Second page content"
        assert docs[1].metadata["page"] == 2
        assert docs[2].page_content == "Third page content"
        assert docs[2].metadata["page"] == 3

    def test_split_json_into_pages_basic(self):
        """Test that _split_json_into_pages correctly splits JSON content by page."""
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", format="json", split_pages=True
        )

        json_data = {
            "file name": "test.pdf",
            "number of pages": 3,
            "kids": [
                {"type": "paragraph", "page number": 1, "content": "Page 1 text"},
                {"type": "heading", "page number": 1, "content": "Page 1 heading"},
                {"type": "paragraph", "page number": 2, "content": "Page 2 text"},
                {"type": "paragraph", "page number": 3, "content": "Page 3 text"},
            ],
        }

        docs = list(loader._split_json_into_pages(json_data, "test.pdf"))

        assert len(docs) == 3
        assert "Page 1 text" in docs[0].page_content
        assert "Page 1 heading" in docs[0].page_content
        assert docs[0].metadata["page"] == 1
        assert docs[1].page_content == "Page 2 text"
        assert docs[1].metadata["page"] == 2
        assert docs[2].page_content == "Page 3 text"
        assert docs[2].metadata["page"] == 3

    def test_split_json_into_pages_with_nested_content(self):
        """Test that _split_json_into_pages handles nested elements like tables."""
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", format="json", split_pages=True
        )

        json_data = {
            "file name": "test.pdf",
            "number of pages": 2,
            "kids": [
                {"type": "paragraph", "page number": 1, "content": "Intro text"},
                {
                    "type": "table",
                    "page number": 1,
                    "rows": [
                        {
                            "type": "table row",
                            "cells": [
                                {"kids": [{"content": "Cell 1"}]},
                                {"kids": [{"content": "Cell 2"}]},
                            ],
                        }
                    ],
                },
                {"type": "paragraph", "page number": 2, "content": "Page 2 text"},
            ],
        }

        docs = list(loader._split_json_into_pages(json_data, "test.pdf"))

        assert len(docs) == 2
        assert "Intro text" in docs[0].page_content
        assert "Cell 1" in docs[0].page_content
        assert "Cell 2" in docs[0].page_content
        assert docs[0].metadata["page"] == 1
        assert docs[1].page_content == "Page 2 text"
        assert docs[1].metadata["page"] == 2

    def test_split_json_into_pages_with_list_items(self):
        """Test that _split_json_into_pages handles list items."""
        loader = OpenDataLoaderPDFLoader(
            file_path="test.pdf", format="json", split_pages=True
        )

        json_data = {
            "file name": "test.pdf",
            "number of pages": 1,
            "kids": [
                {
                    "type": "list",
                    "page number": 1,
                    "list items": [
                        {"content": "Item 1"},
                        {"content": "Item 2"},
                        {"content": "Item 3"},
                    ],
                },
            ],
        }

        docs = list(loader._split_json_into_pages(json_data, "test.pdf"))

        assert len(docs) == 1
        assert "Item 1" in docs[0].page_content
        assert "Item 2" in docs[0].page_content
        assert "Item 3" in docs[0].page_content
