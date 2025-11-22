"""
NITISARA Foundational Model Configuration
-----------------------------------------
Gemini 2.5 Flash integration using LangChain Google Generative AI wrapper.
Handles general reasoning, trade advisory, and open-ended queries.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

# ==============================================================
# 1️⃣ Environment Setup
# ==============================================================

# Load environment variables
load_dotenv()

# Ensure GOOGLE_API_KEY exists
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("⚠️ GOOGLE_API_KEY not found in environment. Please add it to your .env file.")

# ==============================================================
# 2️⃣ Model Initialization
# ==============================================================

# Initialize Gemini Model (fast and efficient)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",       # can switch to gemini-2.5-pro for reasoning-heavy tasks
    temperature=0.3,                # balanced factual tone
    max_tokens=None,
    timeout=30,
    max_retries=2,
    google_api_key=api_key          # ✅ ensures explicit key passing (avoids ADC credential issue)
)

# ==============================================================
# 3️⃣ Core Function: ask_gemini()
# ==============================================================
def query_proprietary_data(query: str, db_name: str = "companies") -> str:
    """
    Search NITISARA proprietary FAISS-trained datasets (RAG layer).
    Args:
        query (str): Natural language question.
        db_name (str): Dataset name (e.g., 'companies', 'quotes', 'shipments').
    Returns:
        str: Gemini’s grounded answer using the trained dataset.
    """
    try:
        db_path = os.path.join("vector_dbs", f"{db_name}_db")
        if not os.path.exists(db_path):
            return f"[Error] Dataset '{db_name}' not found or not trained yet."

        # Use HuggingFace for embeddings (free + local)
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)

        retriever = db.as_retriever(search_kwargs={"k": 3})

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
        )

        response = qa_chain.invoke(query)
        return response

    except Exception as e:
        return f"[RAG Error] {str(e)}"
    

def ask_gemini(prompt: str, system_message: str = None) -> str:
    """
    Query the Gemini model for reasoning, insights, or open-ended responses.

    Args:
        prompt (str): User query or message.
        system_message (str): Optional system context or model role.

    Returns:
        str: Gemini’s natural language response.
    """
    try:
        messages = []

        if system_message:
            messages.append(SystemMessage(content=system_message))

        messages.append(HumanMessage(content=prompt))

        ai_msg = llm.invoke(messages)

        if hasattr(ai_msg, "content"):
            return ai_msg.content.strip()
        else:
            return str(ai_msg)

    except Exception as e:
        return f"[Gemini Error] {str(e)}"

# ==============================================================
# 4️⃣ Test Run (optional)
# ==============================================================

if __name__ == "__main__":
    print("🚀 Testing Gemini integration...\n")
    response = ask_gemini(
        "I want to ship goods from UK to India. Which is better: Mumbai or Cochin port, considering congestion and tariffs?",
        system_message="You are NITISARA Captain, an expert freight consultant who gives data-backed trade insights."
    )
    print("Gemini Reply:\n", response)
