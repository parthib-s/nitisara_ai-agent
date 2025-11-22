"""
Analytics Hooks for Tasks 8️⃣–🔟
Auto-log model performance, brain interventions, and comparisons
during live Captain conversations.
"""

import json, time, logging
from datetime import datetime
from foundational_config import ask_gemini, query_proprietary_data
from model_judge_framework import _semantic_overlap, _estimate_factual_score, _estimate_reasoning_score

# Configure main trace log
logging.basicConfig(filename="brain_trace.log", level=logging.INFO, format="%(asctime)s - %(message)s")
JUDGE_LOG = "model_judge_log.json"


# ---------------------------------------------------------------
# 🧠 Task 9 — Brain Intervention Trace
# ---------------------------------------------------------------
def log_brain_intervention(context, query, response):
    entry = (
        f"\n🧠 FOUNDATIONAL MODEL INTERVENTION\n"
        f"Context: {context}\n"
        f"Query: {query}\n"
        f"Response: {response[:250]}...\n{'-'*60}\n"
    )
    logging.info(entry)


# ---------------------------------------------------------------
# 🧪 Task 8 + 10 — Live Comparison & Metrics
# ---------------------------------------------------------------
def log_comparison(query, dataset, agentic_text, gemini_text, start_time):
    duration = round(time.time() - start_time, 2)
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "dataset": dataset,
        "agentic_answer": agentic_text,
        "general_answer": gemini_text,
        "semantic_overlap": _semantic_overlap(agentic_text, gemini_text),
        "factual_score": _estimate_factual_score(agentic_text),
        "reasoning_score": _estimate_reasoning_score(gemini_text),
        "response_time_sec": duration,
        "final_verdict": (
            "🧠 Gemini" if _estimate_reasoning_score(gemini_text) > _estimate_factual_score(agentic_text)
            else "🏢 Agentic (RAG)"
        )
    }

    # Append to JSON log
    if not os.path.exists(JUDGE_LOG):
        with open(JUDGE_LOG, "w") as f: json.dump([], f)
    with open(JUDGE_LOG, "r") as f: data = json.load(f)
    data.append(result)
    with open(JUDGE_LOG, "w") as f: json.dump(data, f, indent=2)

    return result
