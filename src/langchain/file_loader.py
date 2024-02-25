from pathlib import Path
from typing import List

from langchain_community.document_loaders import PDFMinerLoader, TextLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader
from langchain_core.documents import Document


def load_upload_files(paths: List[Path]) -> List[Document]:
    documents = []
    for path in paths:
        match path.suffix:
            case ".html" | ".htm":
                loader_cls = UnstructuredHTMLLoader
            case ".pdf":
                loader_cls = PDFMinerLoader
            case ".md":
                loader_cls = UnstructuredMarkdownLoader
            case ".txt":
                loader_cls = TextLoader
            case _:
                raise ValueError(f"Unsupported file type: {path.suffix}")
        loader = loader_cls(file_path=str(path))
        docs = loader.load()
        documents.extend(docs)

    return documents
