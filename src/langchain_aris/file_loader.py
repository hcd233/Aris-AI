from pathlib import Path
from typing import List

from langchain_community.document_loaders import PDFMinerLoader, TextLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_core.documents import Document

from .transformers import Jupyter2MarkdownTransformer


def load_upload_files(paths: List[Path]) -> List[Document]:
    documents = []
    for path in paths:
        match path.suffix:
            case ".pdf":
                loader_cls = PDFMinerLoader
                transformer_cls = None
            case ".txt" | ".md":
                loader_cls = TextLoader
                transformer_cls = None
            case ".html" | ".htm":
                loader_cls = TextLoader
                transformer_cls = Html2TextTransformer
                trans_params = {"ignore_links": False, "ignore_images": False}

            case ".ipynb":
                loader_cls = TextLoader
                transformer_cls = Jupyter2MarkdownTransformer
                trans_params = {}
            case _:
                raise ValueError(f"Unsupported file type: {path.suffix}")
        loader = loader_cls(file_path=str(path))
        docs = loader.load()

        if transformer_cls:
            transformer = transformer_cls(**trans_params)
            docs = transformer.transform_documents(docs)

        documents.extend(docs)

    return documents
