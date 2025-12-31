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
