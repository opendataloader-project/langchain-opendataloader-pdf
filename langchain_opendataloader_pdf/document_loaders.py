import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union

from langchain_core.document_loaders.base import BaseLoader
from langchain_core.documents import Document

try:
    import opendataloader_pdf
except ImportError:
    raise ImportError(
        "`opendataloader-pdf` package not found. "
        "Please install it with `pip install opendataloader-pdf`"
    )

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

            # Load a single file
            loader = OpenDataLoaderPDFLoader("example.pdf")
            docs = loader.load()

            # Load multiple files
            loader = OpenDataLoaderPDFLoader(["doc1.pdf", "doc2.pdf"])
            docs = loader.load()
    """

    def __init__(
        self,
        file_path: Union[str, Path, List[Union[str, Path]]],
        no_json: bool = False,
        **kwargs: Any,
    ):
        """Initialize the loader.

        Args:
            file_path: A path or list of paths to the PDF file(s).
            no_json: If True, skips JSON parsing and returns the entire text
                     content as a single Document.
            **kwargs: Additional keyword arguments to pass to the
                      `opendataloader_pdf.run` function.
        """
        if isinstance(file_path, (str, Path)):
            self.file_paths = [Path(file_path)]
        else:
            self.file_paths = [Path(p) for p in file_path]

        self.no_json = no_json
        self.extra_args = kwargs

    def _parse_node_recursively(
        self, node: Dict[str, Any], source: str
    ) -> Iterator[Document]:
        """Recursively parse a JSON node and its children."""
        # 1. If the current node has text content, create a Document.
        content = node.get("content", "")
        if content:
            yield Document(
                page_content=content,
                metadata={
                    "page": node.get("page number", None),
                    "type": node.get("type", None),
                    "source": source,
                },
            )

                # 2. Recursively call this function for each child in 'kids'.
        if "kids" in node and isinstance(node["kids"], list):
            for child_node in node["kids"]:
                yield from self._parse_node_recursively(child_node, source)

    def lazy_load(self) -> Iterator[Document]:
        """Sequentially process each PDF file and yield Documents."""
        for path in self.file_paths:
            try:
                output = opendataloader_pdf.run(
                    input_path=str(path),
                    no_json=self.no_json,
                    **self.extra_args,
                )

                if not self.no_json:
                    try:
                        data = json.loads(output)
                        # Start the recursive parsing from the top-level 'kids' array.
                        for top_level_node in data.get("kids", []):
                            yield from self._parse_node_recursively(
                                top_level_node, str(path)
                            )

                    except json.JSONDecodeError:
                        logger.debug(
                            f"Could not parse JSON for {path}. "
                            "Returning entire output as a single document."
                        )
                        yield Document(
                            page_content=output, metadata={"source": str(path)}
                        )
                else:
                    yield Document(page_content=output, metadata={"source": str(path)})

            except Exception as e:
                logger.error(f"Error processing file {path}: {e}")
                continue
