"""
gemini_chain.py

This file first attempts to import your real LangChain/Gemini integration.
If that import fails (e.g., when running locally without the extra package),
it provides a small fallback `get_llm_response` that returns a safe canned string.

Replace or remove the fallback when running with your real Gemini integration.
"""

try:
    # Attempt to import the real LangChain/Google generative integration
    from langchain_google_genai import ChatGoogleGenerativeAI
    from config import GEMINI_API_KEY

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)

    def get_llm_response(prompt: str) -> str:
        # Real LLM call
        return llm.predict(prompt)

except Exception:
    # Fallback stub for local testing without dependencies
    def get_llm_response(prompt: str) -> str:
        # Provide a safe, short canned reply and encourage fetching official guidance
        sample = (
            "I can help look that up. I don't have access to the official doc right now. "
            "Shall I fetch official guidance and cite the source? (yes/no)"
        )
        # Keep response short to avoid blocking flows during tests
        return sample
