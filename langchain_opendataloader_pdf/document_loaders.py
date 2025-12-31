import json
import logging
import re
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union, Optional
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
        image_output: Optional[str] = None,
        image_format: Optional[str] = None,
        split_pages: bool = True,
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
            image_output: Image output mode.
                (Values: "off", "embedded" (Base64), "external" (file references))
            image_format: Output format for extracted images.
                (Values: "png", "jpeg". Default: "png")
            split_pages: If True, split output into separate Documents per page.
                Automatically sets the appropriate page separator for the format.
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
        self.image_output = image_output
        self.image_format = image_format
        self.split_pages = split_pages

    # Internal separator used for page splitting (unique enough to avoid collisions)
    _PAGE_SPLIT_SEPARATOR = "\n<<<ODL_PAGE_BREAK_%page-number%>>>\n"

    def _get_page_separator(self) -> Optional[str]:
        """Get the page separator for split_pages mode."""
        if self.split_pages:
            return self._PAGE_SPLIT_SEPARATOR
        return None

    def _split_into_pages(self, content: str, source_name: str) -> Iterator[Document]:
        """Split content by page separator and yield Documents for each page."""
        # Build regex pattern to match separator with page number
        # The separator appears BEFORE each page's content with that page's number
        # e.g., "\n<<<ODL_PAGE_BREAK_1>>>\nPage 1 content\n<<<ODL_PAGE_BREAK_2>>>\nPage 2 content"
        separator_pattern = re.escape(self._PAGE_SPLIT_SEPARATOR).replace(
            re.escape("%page-number%"), r"(\d+)"
        )

        # Split content using the separator pattern
        parts = re.split(separator_pattern, content)

        # parts: [before_first_sep, page_num_1, content_1, page_num_2, content_2, ...]
        # First part (index 0) is content before first separator (usually empty)
        # Then alternating: page_num (odd indices), content (even indices > 0)

        # Handle content before first separator (if any, treat as page 1)
        if parts[0].strip():
            yield Document(
                page_content=parts[0].strip(),
                metadata={
                    "source": source_name,
                    "format": self.format,
                    "page": 1,
                },
            )

        # Process remaining parts: (page_num, content) pairs
        for i in range(1, len(parts), 2):
            page_num = int(parts[i])
            if i + 1 < len(parts):
                page_content = parts[i + 1].strip()
                if page_content:  # Skip empty pages
                    yield Document(
                        page_content=page_content,
                        metadata={
                            "source": source_name,
                            "format": self.format,
                            "page": page_num,
                        },
                    )

    def _extract_text_from_element(self, element: Dict[str, Any]) -> str:
        """Recursively extract text content from a JSON element."""
        texts = []

        # Get direct content
        if "content" in element:
            texts.append(element["content"])

        # Process nested elements
        for key in ["kids", "rows", "cells", "list items"]:
            if key in element:
                for child in element[key]:
                    texts.append(self._extract_text_from_element(child))

        return "\n".join(filter(None, texts))

    def _split_json_into_pages(
        self, data: Dict[str, Any], source_name: str
    ) -> Iterator[Document]:
        """Split JSON content by page number and yield Documents for each page."""
        # Group elements by page number
        pages: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

        for element in data.get("kids", []):
            page_num = element.get("page number", 1)
            pages[page_num].append(element)

        # Yield a Document for each page
        for page_num in sorted(pages.keys()):
            page_elements = pages[page_num]
            # Extract text from all elements on this page
            page_texts = [self._extract_text_from_element(el) for el in page_elements]
            page_content = "\n".join(filter(None, page_texts))

            if page_content.strip():
                yield Document(
                    page_content=page_content,
                    metadata={
                        "source": source_name,
                        "format": self.format,
                        "page": page_num,
                    },
                )

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

            # Get page separator for split_pages mode
            page_sep = self._get_page_separator()

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
                markdown_page_separator=page_sep,
                text_page_separator=page_sep,
                html_page_separator=page_sep,
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

                source_name = file.with_suffix(".pdf").name

                if self.split_pages:
                    if self.format == "json":
                        # Parse JSON and split by page number
                        data = json.loads(content)
                        yield from self._split_json_into_pages(data, source_name)
                    else:
                        # Split by page separator pattern and yield each page
                        yield from self._split_into_pages(content, source_name)
                else:
                    yield Document(
                        page_content=content,
                        metadata={
                            "source": source_name,
                            "format": self.format,
                        },
                    )
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting temp file '{file}': {e}")

        except Exception as e:
            logger.error(f"Error: {e}")
