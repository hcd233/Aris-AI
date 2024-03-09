import re
from datetime import datetime
from typing import List

from altair import Literal
from langchain_community.document_loaders import ArxivLoader, GitLoader, RecursiveUrlLoader, SeleniumURLLoader
from langchain_core.documents import Document

from src.logger import logger

from .text_splitter import SUFFIX_LANGUAGE_MAP


def _load_from_arxiv(urls: List[str]) -> List[Document]:
    def _match_arxiv_url(url: str) -> str:
        _match = re.match(r"(https://|http://|)(www\.|)arxiv.org/abs/(\d+\.\d+)", url, re.IGNORECASE)

        if not _match:
            raise ValueError(f"Invalid arxiv url: {url}")
        url = _match.group(3)

        return url

    documents = []

    for url in urls:
        url = _match_arxiv_url(url)
        loader = ArxivLoader(query=url)
        documents.extend(loader.load())

    return documents


def _load_from_git(urls: List[str]) -> List[Document]:
    def _match_git_url(url: str) -> str:
        _match = re.match(r"(https://|http://|)(www\.|)(github|gitee).com/([^/]+/[^/]+)", url, re.IGNORECASE)

        if not _match:
            raise ValueError(f"Invalid git url: {url}")
        url = _match.group(4)
        return url

    documents = []
    for url in urls:
        repo_url = _match_git_url(url)
        url = url[: url.rfind(repo_url) + len(repo_url)]
        temp_repo_path = f"./github_repos/{repo_url}/{datetime.now().strftime('%Y%m%d%H%M%S')}"
        loader = GitLoader(
            clone_url=url, repo_path=temp_repo_path, branch="master", file_filter=lambda x: any(x.endswith(suffix) for suffix in SUFFIX_LANGUAGE_MAP)
        )
        documents.extend(loader.load())

    return documents


def _load_from_selenium(urls: List[str]) -> List[Document]:
    loader = SeleniumURLLoader(urls=urls)

    documents = loader.load()

    return documents


def _load_from_recursive(urls: List[str]) -> List[Document]:
    documents = []

    for url in urls:
        loader = RecursiveUrlLoader(url=url, max_depth=2)
        documents.extend(loader.load())

    return documents


def load_upload_urls(urls: List[str], url_type: Literal["arxiv", "git", "render", "recursive"]) -> List[Document]:
    match url_type:
        case "arxiv":
            docs = _load_from_arxiv(urls)
        case "git":
            docs = _load_from_git(urls)
        case "render":
            docs = _load_from_selenium(urls)
        case "recursive":
            docs = _load_from_recursive(urls)
        case _:
            raise ValueError(f"Unsupported url type: {url_type}")

    logger.debug(f"Loaded {len(docs)} documents from {url_type} {len(urls)} urls")
    return docs
