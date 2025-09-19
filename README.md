# opendataloader-pdf-langchain

This package contains the LangChain integration with OpenDataLoaderPDF

## Installation

```bash
pip install -U opendataloader-pdf-langchain
```

And you should configure credentials by setting the following environment variables:

* TODO: fill this out

## Chat Models

`ChatOpenDataLoaderPDF` class exposes chat models from OpenDataLoaderPDF.

```python
from langchain_opendataloader_pdf import ChatOpenDataLoaderPDF

llm = ChatOpenDataLoaderPDF()
llm.invoke("Sing a ballad of LangChain.")
```

## Embeddings

`OpenDataLoaderPDFEmbeddings` class exposes embeddings from OpenDataLoaderPDF.

```python
from langchain_opendataloader_pdf import OpenDataLoaderPDFEmbeddings

embeddings = OpenDataLoaderPDFEmbeddings()
embeddings.embed_query("What is the meaning of life?")
```

## LLMs

`OpenDataLoaderPDFLLM` class exposes LLMs from OpenDataLoaderPDF.

```python
from langchain_opendataloader_pdf import OpenDataLoaderPDFLLM

llm = OpenDataLoaderPDFLLM()
llm.invoke("The meaning of life is")
```
