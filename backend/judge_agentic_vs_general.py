# judge_agentic_vs_general.py
"""
Task 8️⃣: Agentic vs General Gemini Comparison
-----------------------------------------------
Evaluates factual (RAG) vs reasoning (Gemini) responses
and produces a 'which is better' qualitative judgment.
"""

import time
from foundational_config import ask_gemini, query_proprietary_data


def compare_agentic_vs_general(query: str, dataset: str):
    print(f"\n🧪 Comparing responses for query: {query}\n")

    start_time = time.time()

    # 1️⃣ Agentic (RAG)
    try:
        agentic = query_proprietary_data(query, dataset)
        agentic_text = str(agentic)
    except Exception as e:
        agentic_text = f"[RAG Error] {str(e)}"

    # 2️⃣ General (Gemini)
    try:
        general = ask_gemini(
            prompt=query,
            system_message="You are NITISARA Captain, a freight logistics expert providing clear, data-backed insights."
        )
    except Exception as e:
        general = f"[Gemini Error] {str(e)}"

    duration = round(time.time() - start_time, 2)
    overlap = _semantic_overlap(agentic_text, general)

    # 3️⃣ Evaluate and judge which is better
    reasoning_score = _estimate_reasoning_score(general)
    factual_score = _estimate_factual_score(agentic_text)

    if factual_score > reasoning_score:
        verdict = "🏢 Agentic (RAG) performed better — more factual/relevant to dataset."
    elif reasoning_score > factual_score:
        verdict = "🧠 Gemini performed better — deeper reasoning or conceptual understanding."
    else:
        verdict = "⚖️ Both comparable — factual vs conceptual balance."

    result = {
        "query": query,
        "agentic_answer": agentic_text,
        "general_answer": general,
        "semantic_overlap": overlap,
        "factual_score": factual_score,
        "reasoning_score": reasoning_score,
        "response_time_sec": duration,
        "final_verdict": verdict
    }

    return result


def _semantic_overlap(text1: str, text2: str) -> float:
    t1, t2 = set(str(text1).lower().split()), set(str(text2).lower().split())
    if not t1 or not t2:
        return 0.0
    return round(len(t1 & t2) / len(t1 | t2), 2)


def _estimate_reasoning_score(answer: str) -> float:
    """Heuristic for reasoning depth."""
    length = len(answer.split())
    structure = sum(1 for w in ["because", "therefore", "hence", "means", "implies"] if w in answer.lower())
    return min(1.0, 0.3 + 0.002 * length + 0.1 * structure)


def _estimate_factual_score(answer: str) -> float:
    """Heuristic for factual grounding."""
    if "error" in answer.lower():
        return 0.0
    numbers = sum(c.isdigit() for c in answer)
    has_ids = "id" in answer.lower() or "_" in answer
    return min(1.0, 0.4 + 0.1 * has_ids + 0.02 * numbers)


if __name__ == "__main__":
    query = "List all forwarders with CIF terms"
    dataset = "companies"

    comparison = compare_agentic_vs_general(query, dataset)

    print("🔍 COMPARISON RESULT")
    for k, v in comparison.items():
        print(f"{k}: {v}")
