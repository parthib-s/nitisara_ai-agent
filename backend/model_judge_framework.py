# model_judge_framework.py
"""
NITISARA Model Judge Framework
--------------------------------
Combines Tasks 8️⃣, 9️⃣, and 10️⃣:
- Compare Agentic (RAG) vs Foundational (Gemini)
- Log all evaluations
- Measure performance and identify failures
"""

import os
import json
import time
from datetime import datetime
from foundational_config import ask_gemini, query_proprietary_data


LOG_FILE = "model_judge_log.json"


# ============================================================
# CORE COMPARISON
# ============================================================

def compare_agentic_vs_general(query: str, dataset: str):
    """
    Compare factual vs reasoning responses and measure consistency, performance, and latency.
    """
    print(f"\n🧪 Comparing responses for query: {query}\n")

    start_time = time.time()
    error_flag = None

    # ------------------ RAG / Agentic ------------------
    try:
        agentic = query_proprietary_data(query, dataset)
        agentic_text = str(agentic)
    except Exception as e:
        agentic_text = f"[RAG Error] {str(e)}"
        error_flag = "RAG"

    # ------------------ Gemini ------------------
    try:
        general = ask_gemini(
            prompt=query,
            system_message="You are NITISARA Captain, a freight logistics expert. Give accurate, concise, and data-backed insights."
        )
    except Exception as e:
        general = f"[Gemini Error] {str(e)}"
        error_flag = "Gemini"

    duration = round(time.time() - start_time, 2)
    overlap = _semantic_overlap(agentic_text, general)
    factual_score = _estimate_factual_score(agentic_text)
    reasoning_score = _estimate_reasoning_score(general)

    # --------------- Verdict ----------------
    if factual_score > reasoning_score:
        verdict = "🏢 Agentic (RAG) performed better — factual grounding stronger."
    elif reasoning_score > factual_score:
        verdict = "🧠 Gemini performed better — reasoning depth stronger."
    else:
        verdict = "⚖️ Balanced — factual vs conceptual alignment."

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "dataset": dataset,
        "agentic_answer": agentic_text,
        "general_answer": general,
        "semantic_overlap": overlap,
        "factual_score": factual_score,
        "reasoning_score": reasoning_score,
        "response_time_sec": duration,
        "final_verdict": verdict,
        "error_flag": error_flag,
    }

    _log_result(result)
    return result


# ============================================================
# UTILITY HELPERS
# ============================================================

def _semantic_overlap(text1: str, text2: str) -> float:
    """Token-level overlap metric."""
    t1, t2 = set(str(text1).lower().split()), set(str(text2).lower().split())
    if not t1 or not t2:
        return 0.0
    return round(len(t1 & t2) / len(t1 | t2), 2)


def _estimate_reasoning_score(answer: str) -> float:
    """Heuristic for reasoning depth (based on length and logic markers)."""
    length = len(answer.split())
    logic_terms = sum(1 for w in ["because", "hence", "therefore", "means", "thus"] if w in answer.lower())
    return min(1.0, 0.25 + 0.002 * length + 0.1 * logic_terms)


def _estimate_factual_score(answer: str) -> float:
    """Heuristic for factual structure: presence of IDs, numbers, or dataset-specific info."""
    if "error" in answer.lower():
        return 0.0
    numbers = sum(c.isdigit() for c in answer)
    has_ids = "id" in answer.lower() or "_" in answer
    return min(1.0, 0.4 + 0.1 * has_ids + 0.02 * numbers)


# ============================================================
# LOGGING & PERFORMANCE TRACKING
# ============================================================

def _log_result(entry):
    """Store comparison result into JSON file."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append(entry)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"📊 Logged comparison to {LOG_FILE}")


# ============================================================
# PERFORMANCE ANALYSIS (Task 10)
# ============================================================

def generate_performance_summary():
    """Reads the log file and generates performance metrics."""
    if not os.path.exists(LOG_FILE):
        print("⚠️ No comparison logs found.")
        return None

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    gemini_wins = sum(1 for d in data if "Gemini" in d["final_verdict"])
    rag_wins = sum(1 for d in data if "Agentic" in d["final_verdict"])
    avg_latency = round(sum(d["response_time_sec"] for d in data) / total, 2)
    avg_overlap = round(sum(d["semantic_overlap"] for d in data) / total, 2)
    avg_factual = round(sum(d["factual_score"] for d in data) / total, 2)
    avg_reasoning = round(sum(d["reasoning_score"] for d in data) / total, 2)

    report = {
        "total_comparisons": total,
        "avg_latency_sec": avg_latency,
        "avg_semantic_overlap": avg_overlap,
        "avg_factual_score": avg_factual,
        "avg_reasoning_score": avg_reasoning,
        "Gemini_wins": gemini_wins,
        "RAG_wins": rag_wins,
        "Failures_detected": [d for d in data if d["error_flag"] is not None],
    }

    print("\n📈 PERFORMANCE SUMMARY")
    print(json.dumps(report, indent=2))
    return report


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    # Try multiple example queries
    tests = [
        ("List all forwarders with CIF terms", "companies"),
        ("Average surcharge where validity_days > 15", "quotes"),
        ("Which company has prepaid billing with EXW incoterms?", "companies")
    ]

    for q, ds in tests:
        compare_agentic_vs_general(q, ds)

    generate_performance_summary()
