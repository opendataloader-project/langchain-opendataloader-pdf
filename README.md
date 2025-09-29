# langchain-opendataloader-pdf

A lightweight adapter that plugs the [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) engine into the LangChain document loader API. The loader calls the Java-based extractor, parses the structured JSON output, and yields ready-to-use LangChain `Document` objects.

## Features
- Stream over one or many PDF files while keeping metadata such as page numbers and node types
- Recursively traverse the OpenDataLoader `kids` hierarchy to capture every text fragment
- Toggle JSON parsing off with `no_json=True` when you prefer the raw text payload
- Ships with `py.typed` so static type checkers (mypy, pyright, etc.) understand the package

## Requirements
- Python >= 3.9, < 4.0
- Java 11 or newer available on the system `PATH`
- The `opendataloader-pdf` Python package (installed automatically when you install this project)

## Installation
```bash
pip install -U langchain-opendataloader-pdf
```
> The dependency on `opendataloader-pdf` is declared in `pyproject.toml`, so the package is installed together with this integration. Ensure Java is discoverable on your machine before importing the loader.

## Quick start
```python
from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

loader = OpenDataLoaderPDFLoader("sample.pdf")
documents = loader.load()
for doc in documents:
    print(doc.metadata["page"], doc.page_content[:80])
```

### Multiple files and extra options
You can pass a list of files and forward any supported keyword arguments to `opendataloader_pdf.run`.

```python
loader = OpenDataLoaderPDFLoader([
    "report.pdf",
    "appendix.pdf",
], output_format="JSON", preserve_line_breaks=True)

for document in loader.lazy_load():
    # process each chunk as it streams in
    ...
```

### Processing a Directory
You can also provide a path to a directory. The loader will find and process all PDF files within it.

```python
# Load all PDFs from a directory
loader = OpenDataLoaderPDFLoader("path/to/my/pdf_folder/")
docs = loader.load()
```

### Raw text mode
If the downstream pipeline does not need the JSON tree, set `no_json=True` to receive one `Document` per file containing the full text.

```python
loader = OpenDataLoaderPDFLoader("scanned.pdf", no_json=True)
```

## Development workflow
This repository uses [Poetry](https://python-poetry.org/) for dependency management. If you don't have Poetry installed, please follow the [official installation guide](https://python-poetry.org/docs/#installation).

Once Poetry is installed, you can install the project dependencies:
```bash
poetry install --with dev
```

Common tasks are mirrored in the `Makefile` so you can run them with or without Poetry.

## Quality checks
```bash
make lint      # ruff + mypy
make test      # unit test suite (network disabled)
make integration_tests  # runs tests that may touch the network
```
You can also call the underlying Poetry commands directly (e.g., `poetry run pytest`).

## Publishing notes
Run `poetry check` and `poetry build` to verify the package metadata before uploading to PyPI. Confirm that `langchain_opendataloader_pdf/py.typed` is present in the wheel so consumers benefit from typing information.

## License
Distributed under the MIT License. See `LICENSE` for full text.
