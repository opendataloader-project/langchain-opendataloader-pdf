"""Test ChatOpenDataLoaderPDF chat model."""

from typing import Type

from langchain_opendataloader_pdf.chat_models import ChatOpenDataLoaderPDF
from langchain_tests.integration_tests import ChatModelIntegrationTests


class TestChatParrotLinkIntegration(ChatModelIntegrationTests):
    @property
    def chat_model_class(self) -> Type[ChatOpenDataLoaderPDF]:
        return ChatOpenDataLoaderPDF

    @property
    def chat_model_params(self) -> dict:
        # These should be parameters used to initialize your integration for testing
        return {
            "model": "bird-brain-001",
            "temperature": 0,
            "parrot_buffer_length": 50,
        }
