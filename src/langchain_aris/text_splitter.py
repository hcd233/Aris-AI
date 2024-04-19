from typing import List

from langchain_core.documents import Document

from langchain.text_splitter import Language, RecursiveCharacterTextSplitter
from src.logger import logger

SUFFIX_LANGUAGE_MAP = {
    "cpp": Language.CPP,
    "h": Language.CPP,
    "hpp": Language.CPP,
    "go": Language.GO,
    "java": Language.JAVA,
    "kt": Language.KOTLIN,
    "js": Language.JS,
    "ts": Language.TS,
    "php": Language.PHP,
    "proto": Language.PROTO,
    "py": Language.PYTHON,
    "rst": Language.RST,
    "rb": Language.RUBY,
    "rs": Language.RUST,
    "scala": Language.SCALA,
    "swift": Language.SWIFT,
    "md": Language.MARKDOWN,
    "tex": Language.LATEX,
    "html": Language.MARKDOWN,  # converted to markdown
    "htm": Language.MARKDOWN,  # converted to markdown
    "sol": Language.SOL,
    "cs": Language.CSHARP,
    "cbl": Language.COBOL,
    "cob": Language.COBOL,
}


def split_documents(documents: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
    splitted_documents = []

    for doc in documents:
        params = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}

        source: str = doc.metadata.get("source", ".")

        if source.split(".")[-1] in SUFFIX_LANGUAGE_MAP:
            splitter_cls = RecursiveCharacterTextSplitter
            suffix = source.split(".")[-1]
            params.update({"separators": splitter_cls.get_separators_for_language(SUFFIX_LANGUAGE_MAP[suffix])})

        elif any([source.startswith(prefix) for prefix in ["https://", "http://", "www."]]):
            splitter_cls = RecursiveCharacterTextSplitter
            params.update({"separators": splitter_cls.get_separators_for_language(SUFFIX_LANGUAGE_MAP["md"])})

        else:
            splitter_cls = RecursiveCharacterTextSplitter

        splitter = splitter_cls(**params)
        splitted_doc = splitter.split_documents([doc])
        splitted_documents.extend(splitted_doc)

    logger.debug(f"Split {len(documents)} documents into {len(splitted_documents)} documents")
    return splitted_documents
