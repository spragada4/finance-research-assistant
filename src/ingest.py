# src/ingest.py

import os
import sys
os.environ["USER_AGENT"] = "finance-qa-tool/1.0"

from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from config import (
    EMBEDDING_MODEL,
    CHROMA_DB_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    FINANCE_URLS,
    RAW_DATA_PATH,
)

def load_web_docs(urls: list) -> list:
    """Load documents from URLs with fallback logging."""
    print(f"\n📥 Loading {len(urls)} URLs...")
    all_docs    = []
    failed_urls = []

    for url in urls:
        try:
            print(f"  → {url}")
            loader = WebBaseLoader(url)
            loader.requests_kwargs = {
                "headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
                "timeout": 15,
            }
            docs    = loader.load()
            content = docs[0].page_content.strip() if docs else ""

            if len(content) < 200:
                print(f"     ⚠️  Too little content ({len(content)} chars) — skipping")
                failed_urls.append(url)
                continue

            all_docs.extend(docs)
            print(f"     ✓ Loaded {len(docs)} doc(s), {len(content)} chars")

        except Exception as e:
            print(f"     ✗ Failed: {e}")
            failed_urls.append(url)

    if failed_urls:
        print(f"\n⚠️  {len(failed_urls)} URLs failed:")
        for url in failed_urls:
            print(f"   - {url}")
        print("   → Download these as PDFs and place in data/raw/\n")

    return all_docs


def load_pdf_docs(folder: str) -> list:
    """Load PDFs from data/raw/"""
    all_docs = []
    if not os.path.exists(folder):
        return all_docs
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            path = os.path.join(folder, filename)
            print(f"  → Loading PDF: {filename}")
            try:
                loader = PyPDFLoader(path)
                docs   = loader.load()
                all_docs.extend(docs)
                print(f"     ✓ {len(docs)} pages")
            except Exception as e:
                print(f"     ✗ Failed: {e}")
    return all_docs


def chunk_documents(docs: list) -> list:
    """Split documents into overlapping chunks."""
    print(f"\n✂️  Chunking {len(docs)} documents...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"   ✓ Created {len(chunks)} chunks")
    return chunks


def build_vectorstore(chunks: list) -> Chroma:
    """Embed chunks and store in ChromaDB."""
    print(f"\n🔢 Embedding and storing in ChromaDB...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )
    print(f"   ✓ Saved to {CHROMA_DB_PATH}")
    return vectorstore


def run_ingestion():
    print("=" * 55)
    print("  FINANCE QA — DOCUMENT INGESTION")
    print("=" * 55)

    web_docs = load_web_docs(FINANCE_URLS)
    pdf_docs = load_pdf_docs(RAW_DATA_PATH)
    all_docs = web_docs + pdf_docs

    if not all_docs:
        print("\n❌ No documents loaded.")
        sys.exit(1)

    print(f"\n📄 Total documents: {len(all_docs)}")
    chunks = chunk_documents(all_docs)
    build_vectorstore(chunks)
    print("\n✅ Ingestion complete! Ready to query.\n")


if __name__ == "__main__":
    run_ingestion()