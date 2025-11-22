"""
NITISARA Proprietary Dataset Trainer (RAG Builder)
--------------------------------------------------
Trains FAISS vector databases from internal CSV datasets.
"""

import os
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

# ==========================================================
# 1️⃣ Environment Setup
# ==========================================================
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("⚠️ GOOGLE_API_KEY not found in .env file")

# ==========================================================
# 2️⃣ Paths and Model Setup
# ==========================================================
DATA_FOLDER = "data"
VECTOR_FOLDER = "vector_dbs"
os.makedirs(VECTOR_FOLDER, exist_ok=True)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ==========================================================
# 3️⃣ Training Function
# ==========================================================
def train_rag_for_all():
    datasets = [
        "companies.csv",
        "contacts.csv",
        "containers.csv",
        "customs.csv",
        "locations.csv",
        "products.csv",
        "quotes.csv",
        "shipments.csv",
        "tracking.csv",
    ]

    for filename in datasets:
        filepath = os.path.join(DATA_FOLDER, filename)
        if not os.path.exists(filepath):
            print(f"⚠️ Skipping missing file: {filename}")
            continue

        print(f"\n📄 Loading dataset: {filename}")
        loader = CSVLoader(file_path=filepath)
        docs = loader.load()

        print(f"🔍 Creating FAISS index for {filename}...")
        db = FAISS.from_documents(docs, embeddings)

        db_name = filename.replace(".csv", "")
        db_path = os.path.join(VECTOR_FOLDER, f"{db_name}_db")
        db.save_local(db_path)

        print(f"✅ Saved FAISS DB: {db_path}")

    print("\n🎯 Training complete! All datasets are now embedded and searchable.\n")

# ==========================================================
# 4️⃣ Entry Point
# ==========================================================
if __name__ == "__main__":
    train_rag_for_all()
