"""Document ingestion script for loading learning materials."""
import asyncio
import os
from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain_core.documents import Document
from app.services.rag_service import rag_service
from app.config import settings


async def ingest_documents(subject: str, directory: str):
    """Ingest documents from a directory into the vector store.

    Args:
        subject: Subject category (math, physics, chemistry)
        directory: Directory containing documents
    """
    print(f"Ingesting documents for {subject} from {directory}...")

    documents = []
    directory_path = Path(directory)

    if not directory_path.exists():
        print(f"Directory {directory} does not exist!")
        return

    # Process all files in directory
    for file_path in directory_path.rglob("*"):
        if not file_path.is_file():
            continue

        print(f"Processing {file_path}...")

        try:
            # Load based on file type
            if file_path.suffix == ".pdf":
                loader = PyPDFLoader(str(file_path))
                docs = loader.load()
            elif file_path.suffix == ".txt":
                loader = TextLoader(str(file_path), encoding="utf-8")
                docs = loader.load()
            elif file_path.suffix == ".md":
                loader = UnstructuredMarkdownLoader(str(file_path))
                docs = loader.load()
            else:
                print(f"Skipping unsupported file type: {file_path.suffix}")
                continue

            # Add metadata
            for doc in docs:
                doc.metadata["subject"] = subject
                doc.metadata["source"] = str(file_path.name)

            documents.extend(docs)
            print(f"Loaded {len(docs)} documents from {file_path.name}")

        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    # Ingest documents
    if documents:
        print(f"\nIngesting {len(documents)} documents into vector store...")
        await rag_service.add_documents(documents, subject)
        print(f"Successfully ingested {len(documents)} documents for {subject}!")
    else:
        print("No documents found to ingest.")


async def main():
    """Main ingestion function."""
    # Ingest documents for each subject
    subjects = {
        "math": "./data/documents/math",
        "physics": "./data/documents/physics",
        "chemistry": "./data/documents/chemistry"
    }

    for subject, directory in subjects.items():
        await ingest_documents(subject, directory)
        print()


if __name__ == "__main__":
    asyncio.run(main())
