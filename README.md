<!-- AI-AGENT-SUMMARY
name: langchain-opendataloader-pdf
category: LangChain document loader, PDF extraction for RAG
license: MIT
solves: [Load PDFs as LangChain Document objects for RAG pipelines, structured PDF extraction with correct reading order and table preservation]
input: PDF files (digital, tagged)
output: LangChain Document objects (text, Markdown, JSON with bounding boxes, HTML)
sdk: Python
requirements: Python 3.10+, Java 11+
key-differentiators: [LangChain-native BaseLoader, per-page Document splitting, all opendataloader-pdf extraction features, batch file/directory input]
-->

# langchain-opendataloader-pdf

LangChain document loader for [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) — parse PDFs into structured `Document` objects for RAG pipelines.

For the full feature set of the core engine (hybrid AI mode, OCR, formula extraction, benchmarks, accessibility), see the [OpenDataLoader PDF documentation](https://opendataloader.org/docs).

[![PyPI version](https://img.shields.io/pypi/v/langchain-opendataloader-pdf.svg)](https://pypi.org/project/langchain-opendataloader-pdf/)
[![License](https://img.shields.io/pypi/l/langchain-opendataloader-pdf.svg)](https://github.com/opendataloader-project/langchain-opendataloader-pdf/blob/main/LICENSE)

## Features

- **Accurate reading order** — XY-Cut++ algorithm handles multi-column layouts correctly
- **Table extraction** — Preserves table structure in output
- **Multiple formats** — Text, Markdown, JSON (with bounding boxes), HTML
- **Per-page splitting** — Each page becomes a separate `Document` with page number metadata
- **AI safety** — Built-in prompt injection filtering (hidden text, off-page content, invisible layers)
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

loader = OpenDataLoaderPDFLoader(
    file_path="document.pdf",
    format="text"
)
documents = loader.load()

print(documents[0].page_content)
print(documents[0].metadata)
# {'source': 'document.pdf', 'format': 'text', 'page': 1}
```

## Usage Examples

### Batch Processing

```python
from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

# Single file, multiple files, or directories — all in one call
loader = OpenDataLoaderPDFLoader(
    file_path=["report1.pdf", "report2.pdf", "documents/"]
)
docs = loader.load()
```

### Output Formats

```python
# Plain text (default) — best for simple RAG
loader = OpenDataLoaderPDFLoader(file_path="doc.pdf", format="text")

# Markdown — preserves headings, lists, tables
loader = OpenDataLoaderPDFLoader(file_path="doc.pdf", format="markdown")

# JSON — structured data with bounding boxes for source citations
loader = OpenDataLoaderPDFLoader(file_path="doc.pdf", format="json")

# HTML — styled output
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

### Table Detection

```python
loader = OpenDataLoaderPDFLoader(
    file_path="financial_report.pdf",
    format="markdown",
    table_method="cluster"  # Better for borderless tables
)
```

### Sensitive Data Sanitization

```python
# Replace emails, phone numbers, IPs, credit cards, URLs with placeholders
loader = OpenDataLoaderPDFLoader(
    file_path="document.pdf",
    sanitize=True
)
```

### Extract Specific Pages

```python
loader = OpenDataLoaderPDFLoader(
    file_path="document.pdf",
    pages="1,3,5-10"
)
```

### Include Headers and Footers

```python
# By default, headers and footers are excluded for cleaner RAG output
loader = OpenDataLoaderPDFLoader(
    file_path="document.pdf",
    include_header_footer=True
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
# Images are excluded by default (image_output="off")
# This is optimal for text-based RAG pipelines

# Embed images as Base64 (for multimodal RAG)
loader = OpenDataLoaderPDFLoader(
    file_path="doc.pdf",
    format="markdown",
    image_output="embedded",
    image_format="jpeg"  # or "png"
)

# Save images as files to a local directory
loader = OpenDataLoaderPDFLoader(
    file_path="doc.pdf",
    format="markdown",
    image_output="external",
    image_dir="./images",   # images saved here; defaults to temp dir if not set
    image_format="png"
)
```

### Hybrid AI Mode

For complex documents (tables, charts, scanned content), hybrid mode routes pages to an AI backend for better accuracy while keeping simple pages on the fast local engine:

```python
# Requires a running docling-fast server (default: localhost:5002)
loader = OpenDataLoaderPDFLoader(
    file_path="complex_report.pdf",
    format="markdown",
    hybrid="docling-fast",          # Enable hybrid extraction
    hybrid_mode="auto",             # Auto-triage: only complex pages go to backend
    hybrid_url="http://localhost:5002",
)
documents = loader.load()

# Document metadata shows which backend was used
print(documents[0].metadata)
# {'source': 'complex_report.pdf', 'format': 'markdown', 'page': 1, 'hybrid': 'docling-fast'}
```

### Suppress Logging

```python
loader = OpenDataLoaderPDFLoader(
    file_path="doc.pdf",
    quiet=True
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
| `split_pages` | `bool` | `True` | Split into separate Documents per page |
| `quiet` | `bool` | `False` | Suppress console logging |
| `password` | `str` | `None` | Password for encrypted PDFs |
| `use_struct_tree` | `bool` | `False` | Use PDF structure tree (tagged PDFs) |
| `table_method` | `str` | `"default"` | `"default"` (border-based) or `"cluster"` (border + clustering) |
| `reading_order` | `str` | `"xycut"` | `"xycut"` or `"off"` |
| `keep_line_breaks` | `bool` | `False` | Preserve original line breaks |
| `image_output` | `str` | `"off"` | `"off"`, `"embedded"` (Base64), or `"external"` |
| `image_format` | `str` | `"png"` | `"png"` or `"jpeg"` |
| `image_dir` | `str` | `None` | Directory for extracted images when using `image_output="external"` |
| `sanitize` | `bool` | `False` | Sanitize sensitive data (emails, phone numbers, IPs, credit cards, URLs) |
| `pages` | `str` | `None` | Pages to extract (e.g., `"1,3,5-7"`). Default: all pages |
| `include_header_footer` | `bool` | `False` | Include page headers and footers in output |
| `content_safety_off` | `List[str]` | `None` | Disable safety filters: `"hidden-text"`, `"off-page"`, `"tiny"`, `"hidden-ocg"`, `"all"` |
| `replace_invalid_chars` | `str` | `None` | Replacement for invalid characters |
| `hybrid` | `str` | `None` | Hybrid AI backend: `"docling-fast"`. Requires running backend server |
| `hybrid_mode` | `str` | `None` | `"auto"` (route complex pages) or `"full"` (route all pages) |
| `hybrid_url` | `str` | `None` | Backend server URL. Default: `http://localhost:5002` |
| `hybrid_timeout` | `str` | `None` | Backend timeout in ms. Default: `"30000"` |
| `hybrid_fallback` | `bool` | `False` | Fall back to Java extraction on backend failure |

## Document Metadata

Each returned `Document` includes metadata:

```python
doc.metadata
# {'source': 'document.pdf', 'format': 'text', 'page': 1}

# When hybrid mode is active:
# {'source': 'document.pdf', 'format': 'text', 'page': 1, 'hybrid': 'docling-fast'}
```

When `split_pages=False`, the `page` key is omitted.

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://opendataloader.org/docs) — Full documentation (hybrid mode, benchmarks, accessibility)
- [GitHub](https://github.com/opendataloader-project/opendataloader-pdf) — Core engine source code
- [LangChain Docs](https://docs.langchain.com/oss/python/integrations/document_loaders/opendataloader_pdf) — LangChain integration reference
- [PyPI Package](https://pypi.org/project/langchain-opendataloader-pdf/)
