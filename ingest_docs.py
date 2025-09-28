# ingest_docs.py
import os
import argparse
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma

VSTORE_DIR = "./vectorstores"
COLLECTION = "compliance"

def ingest_pdf(path, collection_name=COLLECTION, persist_directory=VSTORE_DIR):
    loader = PyPDFLoader(path)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    # add helpful metadata
    for c in chunks:
        c.metadata["source"] = os.path.basename(path)

    embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma(persist_directory=persist_directory,
                      collection_name=collection_name,
                      embedding_function=embedding)
    vectordb.add_documents(chunks)
    vectordb.persist()
    print(f"Ingested {len(chunks)} chunks from {path} into collection '{collection_name}'")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="Path to PDF to ingest")
    args = ap.parse_args()
    ingest_pdf(args.path)
