"""Test OpenDataLoaderPDF embeddings."""

from typing import Type

from langchain_opendataloader_pdf.embeddings import OpenDataLoaderPDFEmbeddings
from langchain_tests.integration_tests import EmbeddingsIntegrationTests


class TestParrotLinkEmbeddingsIntegration(EmbeddingsIntegrationTests):
    @property
    def embeddings_class(self) -> Type[OpenDataLoaderPDFEmbeddings]:
        return OpenDataLoaderPDFEmbeddings

    @property
    def embedding_model_params(self) -> dict:
        return {"model": "nest-embed-001"}
