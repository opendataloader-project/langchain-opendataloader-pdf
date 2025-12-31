import logging
import tempfile
from pathlib import Path
from typing import Iterator, List, Union, Optional
from langchain_core.document_loaders.base import BaseLoader
from langchain_core.documents import Document
import opendataloader_pdf

logger = logging.getLogger(__name__)


class OpenDataLoaderPDFLoader(BaseLoader):
    """Load PDF files using `OpenDataLoaderPDF`.

    This loader internally calls the `opendataloader-pdf` Python wrapper,
    which executes the underlying Java engine to extract structured content
    from PDFs. The results are converted into LangChain `Document` objects.
    This loader recursively parses the JSON output to capture all nested text content.

    Setup:
        Install the `opendataloader-pdf` package and ensure Java 11 or later is
        installed and available in your system's PATH.

        .. code-block:: bash

            pip install -U opendataloader-pdf

    Instantiate:
        .. code-block:: python

            from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

            loader = OpenDataLoaderPDFLoader(
                file_path=["path/to/document.pdf", "path/to/folder"],
                format="text"
            )
            documents = loader.load()

            for doc in documents:
                print(doc.metadata, doc.page_content[:80])
    """

    def __init__(
        self,
        file_path: Union[str, Path, List[Union[str, Path]]],
        format: str = "text",
        quiet: bool = False,
        content_safety_off: Optional[List[str]] = None,
        password: Optional[str] = None,
        keep_line_breaks: bool = False,
        replace_invalid_chars: Optional[str] = None,
        use_struct_tree: bool = False,
        table_method: Optional[str] = None,
        reading_order: Optional[str] = None,
        markdown_page_separator: Optional[str] = None,
        text_page_separator: Optional[str] = None,
        html_page_separator: Optional[str] = None,
        image_output: Optional[str] = None,
        image_format: Optional[str] = None,
    ):
        """Initialize the loader.

        Args:
            file_path: A path or list of paths to the PDF file(s).
            format: The output format. Default: "text"
                (Valid options are: "json", "text", "html", "markdown")
            quiet: Suppress CLI logging output. Default: False
            content_safety_off: List of content safety filters to disable.
                (Values: "all", "hidden-text", "off-page", "tiny", "hidden-ocg")
            password: Password for encrypted PDF files.
            keep_line_breaks: Preserve original line breaks in extracted text.
            replace_invalid_chars: Replacement character for invalid/unrecognized
                characters. Default: space
            use_struct_tree: Use PDF structure tree (tagged PDF) for reading order
                and semantic structure.
            table_method: Table detection method.
                (Values: "default" (border-based), "cluster" (border + cluster))
            reading_order: Reading order algorithm.
                (Values: "off", "xycut". Default: "xycut")
            markdown_page_separator: Separator between pages in Markdown output.
                Use %page-number% for page numbers.
            text_page_separator: Separator between pages in text output.
                Use %page-number% for page numbers.
            html_page_separator: Separator between pages in HTML output.
                Use %page-number% for page numbers.
            image_output: Image output mode.
                (Values: "off", "embedded" (Base64), "external" (file references))
            image_format: Output format for extracted images.
                (Values: "png", "jpeg". Default: "png")
        """
        if isinstance(file_path, (str, Path)):
            self.file_paths = [str(file_path)]
        else:
            self.file_paths = [str(p) for p in file_path]
        self.format = format.lower()
        self.quiet = quiet
        self.content_safety_off = content_safety_off
        self.password = password
        self.keep_line_breaks = keep_line_breaks
        self.replace_invalid_chars = replace_invalid_chars
        self.use_struct_tree = use_struct_tree
        self.table_method = table_method
        self.reading_order = reading_order
        self.markdown_page_separator = markdown_page_separator
        self.text_page_separator = text_page_separator
        self.html_page_separator = html_page_separator
        self.image_output = image_output
        self.image_format = image_format

    def lazy_load(self) -> Iterator[Document]:
        """Sequentially process each PDF file and yield Documents."""

        if self.format not in [
            "json",
            "text",
            "html",
            "markdown",
        ]:
            raise ValueError(
                f"Invalid format '{self.format}'. Valid options are: 'json', 'text', 'html', 'markdown'"
            )

        try:
            output_dir = tempfile.mkdtemp(dir=tempfile.gettempdir())

            opendataloader_pdf.convert(
                input_path=self.file_paths,
                output_dir=output_dir,
                format=[self.format],
                quiet=self.quiet,
                content_safety_off=self.content_safety_off,
                password=self.password,
                keep_line_breaks=self.keep_line_breaks,
                replace_invalid_chars=self.replace_invalid_chars,
                use_struct_tree=self.use_struct_tree,
                table_method=self.table_method,
                reading_order=self.reading_order,
                markdown_page_separator=self.markdown_page_separator,
                text_page_separator=self.text_page_separator,
                html_page_separator=self.html_page_separator,
                image_output=self.image_output,
                image_format=self.image_format,
            )

            if self.format == "json":
                ext = "json"
            elif self.format == "text":
                ext = "txt"
            elif self.format == "html":
                ext = "html"
            elif self.format == "markdown":
                ext = "md"

            output_path = Path(output_dir)
            files = list(output_path.glob(f"*.{ext}"))
            for file in files:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                yield Document(
                    page_content=content,
                    metadata={
                        "source": file.with_suffix(".pdf").name,
                        "format": self.format,
                    },
                )
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting temp file '{file}': {e}")

        except Exception as e:
            logger.error(f"Error: {e}")
