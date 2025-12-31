# langchain-opendataloader-pdf

LangChain document loader for [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) — parse PDFs into structured `Document` objects for RAG pipelines.

[![PyPI version](https://img.shields.io/pypi/v/langchain-opendataloader-pdf.svg)](https://pypi.org/project/langchain-opendataloader-pdf/)
[![License](https://img.shields.io/pypi/l/langchain-opendataloader-pdf.svg)](https://github.com/opendataloader-project/langchain-opendataloader-pdf/blob/main/LICENSE)

## Features

- **Accurate reading order** — XY-Cut++ algorithm handles multi-column layouts correctly
- **Table extraction** — Preserves table structure in output
- **Multiple formats** — Text, Markdown, JSON, HTML
- **100% local** — No cloud APIs, your documents never leave your machine
- **Fast** — Rule-based extraction, no GPU required

## Requirements

- Python >= 3.10
- Java 11+ available on system `PATH`

## Installation

```bash
pip install -U langchain-opendataloader-pdf
```

## Quick Start

```python
from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

# Load a PDF as text
loader = OpenDataLoaderPDFLoader(
    file_path="document.pdf",
    format="text"
)
documents = loader.load()

print(documents[0].page_content)
```

## Usage Examples

### Basic Usage

```python
from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

# Single file
loader = OpenDataLoaderPDFLoader(file_path="report.pdf")
docs = loader.load()

# Multiple files
loader = OpenDataLoaderPDFLoader(
    file_path=["report1.pdf", "report2.pdf", "documents/"]
)
docs = loader.load()
```

### Output Formats

```python
# Plain text (default) - best for simple RAG
loader = OpenDataLoaderPDFLoader(file_path="doc.pdf", format="text")

# Markdown - preserves headings, lists, tables
loader = OpenDataLoaderPDFLoader(file_path="doc.pdf", format="markdown")

# JSON - structured data with bounding boxes
loader = OpenDataLoaderPDFLoader(file_path="doc.pdf", format="json")

# HTML - styled output
loader = OpenDataLoaderPDFLoader(file_path="doc.pdf", format="html")
```

### Tagged PDF Support

For accessible PDFs with structure tags (common in government/legal documents):

```python
loader = OpenDataLoaderPDFLoader(
    file_path="accessible_document.pdf",
    use_struct_tree=True  # Use native PDF structure
)
```

### Page Separators

Add separators between pages for chunking:

```python
loader = OpenDataLoaderPDFLoader(
    file_path="multipage.pdf",
    format="text",
    text_page_separator="\n\n--- Page %page-number% ---\n\n"
)
```

### Table Detection

For documents with complex tables:

```python
loader = OpenDataLoaderPDFLoader(
    file_path="financial_report.pdf",
    format="markdown",
    table_method="cluster"  # Better for borderless tables
)
```

### Password-Protected PDFs

```python
loader = OpenDataLoaderPDFLoader(
    file_path="encrypted.pdf",
    password="secret123"
)
```

### Image Handling

```python
# Exclude images (faster, smaller output)
loader = OpenDataLoaderPDFLoader(
    file_path="doc.pdf",
    format="markdown",
    image_output="off"
)

# Embed images as Base64 (self-contained output)
loader = OpenDataLoaderPDFLoader(
    file_path="doc.pdf",
    format="markdown",
    image_output="embedded",
    image_format="jpeg"  # or "png"
)
```

### Suppress Logging

```python
loader = OpenDataLoaderPDFLoader(
    file_path="doc.pdf",
    quiet=True  # No console output
)
```

## RAG Pipeline Example

```python
from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Load PDF
loader = OpenDataLoaderPDFLoader(
    file_path="knowledge_base.pdf",
    format="markdown",
    quiet=True
)
documents = loader.load()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(documents)

# Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embeddings)

# Query
results = vectorstore.similarity_search("What is the main topic?")
```

## Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | `str \| List[str]` | — | **(Required)** PDF file path(s) or directories |
| `format` | `str` | `"text"` | Output format: `"text"`, `"markdown"`, `"json"`, `"html"` |
| `quiet` | `bool` | `False` | Suppress console logging |
| `password` | `str` | `None` | Password for encrypted PDFs |
| `use_struct_tree` | `bool` | `False` | Use PDF structure tree (tagged PDFs) |
| `table_method` | `str` | `None` | `"default"` (border-based) or `"cluster"` (border + clustering) |
| `reading_order` | `str` | `"xycut"` | Reading order: `"xycut"` or `"off"` |
| `keep_line_breaks` | `bool` | `False` | Preserve original line breaks |
| `text_page_separator` | `str` | `None` | Separator between pages (text format) |
| `markdown_page_separator` | `str` | `None` | Separator between pages (markdown format) |
| `html_page_separator` | `str` | `None` | Separator between pages (html format) |
| `image_output` | `str` | `None` | `"off"`, `"embedded"` (Base64), or `"external"` |
| `image_format` | `str` | `None` | `"png"` or `"jpeg"` |
| `content_safety_off` | `List[str]` | `None` | Disable safety filters: `"hidden-text"`, `"off-page"`, `"tiny"`, `"hidden-ocg"`, `"all"` |
| `replace_invalid_chars` | `str` | `None` | Replacement for invalid characters |

## Document Metadata

Each returned `Document` includes metadata:

```python
doc.metadata
# {'source': 'document.pdf', 'format': 'text'}
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Links

- [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) — Core PDF parsing engine
- [LangChain Documentation](https://python.langchain.com/docs/integrations/document_loaders/opendataloader_pdf/) — Official integration docs
- [PyPI Package](https://pypi.org/project/langchain-opendataloader-pdf/)
