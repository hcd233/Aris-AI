from typing import Any, Sequence

from langchain_core.documents import Document
from langchain_core.documents.transformers import BaseDocumentTransformer


class Jupyter2MarkdownTransformer(BaseDocumentTransformer):
    def transform_documents(self, documents: Sequence[Document], **kwargs: Any) -> Sequence[Document]:
        try:
            import nbformat
            from nbconvert import MarkdownExporter
        except ImportError:
            raise ImportError(
                """nbformat or nbconvert package not found, please
                install it with `pip install nbformat nbconvert`"""
            )

        new_documents = []
        for d in documents:
            notebook = nbformat.reads(d.page_content, as_version=4)
            markdown_exporter = MarkdownExporter()
            markdown, _ = markdown_exporter.from_notebook_node(notebook)
            new_document = Document(page_content=markdown, metadata={**d.metadata})
            new_documents.append(new_document)

        return new_documents
