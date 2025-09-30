import logging
import tempfile
from pathlib import Path
from typing import Any, Iterator, List, Union, Optional
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
        **kwargs: Any,
    ):
        """Initialize the loader.

        Args:
            file_path: A path or list of paths to the PDF file(s).
            format: The output format. Default: "text" (Valid options are: "json", "text", "html", "markdown")
            quiet: Suppress CLI logging output. Default: False
            content_safety_off: List of content safety filters to disable. Default: None
            **kwargs: Additional keyword arguments to pass to the opendataloader_pdf.
        """
        if isinstance(file_path, (str, Path)):
            self.file_paths = [str(file_path)]
        else:
            self.file_paths = [str(p) for p in file_path]
        self.format = format.lower()
        self.quiet = quiet
        self.content_safety_off = content_safety_off
        self.extra_args = kwargs

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
                **self.extra_args,
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
