"""def check_compliance(product, docs):
    # Dummy: Require "bill of lading" and "tax certificate" for all products
    required = {"bill_of_lading", "tax_certificate"}
    provided = set(docs)
    missing = list(required - provided)
    if missing:
        return f"Missing documents: {', '.join(missing)}"
    return f"All required documents are present for {product}. No restrictions."
"""
# compliance.py (replace old dummy function)
# compliance.py
from rag import check_compliance_rag

def check_compliance(product, docs):
    """
    Runs compliance check using RAG.
    If RAG fails for some reason, fall back to dummy logic.
    """
    try:
        return check_compliance_rag(product, docs)
    except Exception as e:
        # Fallback dummy logic so your flow doesn’t break
        required = {"bill_of_lading", "tax_certificate"}
        provided = set(docs)
        missing = list(required - provided)
        if missing:
            return f"(Fallback) Missing documents: {', '.join(missing)}"
        return f"(Fallback) All required documents are present for {product}. No restrictions."
