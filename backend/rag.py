# rag.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from typing import List
from gemini_chain import get_llm_response   # your Gemini wrapper

VSTORE_DIR = "./vectorstores"
COLLECTION = "compliance"

def _get_vectorstore(collection_name=COLLECTION, persist_directory=VSTORE_DIR):
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding_function=embedding
    )
    return vectordb

def check_compliance_rag(product: str, docs: List[str], k: int = 4) -> str:
    """
    Query the compliance vectorstore and ask the LLM to summarize
    missing documents or compliance flags relative to 'product' and 'docs' provided.
    """
    vectordb = _get_vectorstore()
    retriever = vectordb.as_retriever(search_kwargs={"k": k})

    query = (
        f"Product: {product}\n"
        f"Provided documents: {', '.join(docs) if docs else 'none'}\n"
        "Identify compliance issues for shipping (air/sea), list specific missing documents "
        "or labels the user must supply, and be concise."
    )

    retrieved = retriever.get_relevant_documents(query)
    if not retrieved:
        return "No compliance guidance found in knowledge base. Please upload the relevant regulatory docs."

    # Limit page content to avoid token overflow
    context = "\n\n---\n\n".join([
        f"Source: {d.metadata.get('source', 'unknown')}\n\n{d.page_content[:2000]}"
        for d in retrieved
    ])

    prompt = (
        "You are an experienced trade compliance assistant. Use the following extracted passages "
        "from official guidance documents:\n\n"
        f"{context}\n\n"
        f"User query:\n{query}\n\n"
        "Answer concisely. If specific documents are missing, list them as bullet points. "
        "If shipment is restricted or requires special declarations (e.g., Dangerous Goods Declaration), "
        "say so and list the exact names of the documents/forms required."
    )

    llm_response = get_llm_response(prompt)

    sources = ", ".join(sorted({d.metadata.get("source", 'unknown') for d in retrieved}))
    return f"{llm_response}\n\nSources: {sources}"
