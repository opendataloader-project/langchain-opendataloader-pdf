# langchain-opendataloader-pdf

This package integrates the [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) engine with LangChain by providing a document loader which parses PDFs into structured `Document` objects.

## Requirements
- Python >= 3.10
- Java 11 or newer available on the system `PATH`
- opendataloader-pdf >= 1.3.0

## Installation
```bash
pip install -U langchain-opendataloader-pdf
```

## Quick start
```python
from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

loader = OpenDataLoaderPDFLoader(
    file_path=["path/to/document.pdf", "path/to/folder"], 
    format="text"
)
documents = loader.load()

for doc in documents:
    print(doc.metadata, doc.page_content[:80])
```

## Parameters

| Parameter                | Type                  | Required   | Default      | Description                                                                                                        |
|--------------------------|-----------------------| ---------- |--------------|--------------------------------------------------------------------------------------------------------------------|
| `file_path`              | `List[str]`           | ✅ Yes     | —            | One or more PDF file paths or directories to process.                                                              |
| `format`                 | `str`                 | No         | `None`       | Output formats (e.g. `"json"`, `"html"`, `"markdown"`, `"text"`).                                                  |
| `quiet`                  | `bool`                | No         | `False`      | Suppresses CLI logging output when `True`.                                                                         |
| `content_safety_off`     | `Optional[List[str]]` | No         | `None`       | List of content safety filters to disable (e.g. `"all"`, `"hidden-text"`, `"off-page"`, `"tiny"`, `"hidden-ocg"`). |

## Development workflow
This repository uses [Poetry](https://python-poetry.org/) for dependency management. If you don't have Poetry installed, please follow the [official installation guide](https://python-poetry.org/#installation).

Once Poetry is installed, you can install the project dependencies:
```bash
poetry install
```

Common tasks are mirrored in the `Makefile` so you can run them with or without Poetry.



## Publishing notes
Run `poetry check` and `poetry build` to verify the package metadata before uploading to PyPI. Confirm that `langchain_opendataloader_pdf/py.typed` is present in the wheel so consumers benefit from typing information.

## License
Distributed under the MIT License. See `LICENSE` for full text.
