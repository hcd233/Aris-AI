from pathlib import Path
from typing import List

from langchain.text_splitter import HTMLHeaderTextSplitter, MarkdownTextSplitter, TextSplitter, RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFMinerLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader, TextLoader
from langchain_core.documents import Document


def load_upload_files(paths: List[Path]) -> List[Document]:
    documents = []
    for path in paths:
        match path.suffix:
            case ".html":
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


def split_documents(documents: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
    splitted_documents = []
    params = {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }
    for doc in documents:
        match doc.metadata.get("source").split(".")[-1]:
            case "md":
                splitter_cls = MarkdownTextSplitter
            case "html":
                splitter_cls = HTMLHeaderTextSplitter
                params.update(
                    {
                        "headers_to_split_on": [
                            (f"h{i}", f"Header {i}")
                            for i in range(1, 7)
                        ]
                    }
                )
            case _:
                splitter_cls = RecursiveCharacterTextSplitter

        splitter = splitter_cls(**params)
        splitted_doc = splitter.split_documents([doc])
        splitted_documents.extend(splitted_doc)

    return splitted_documents
