def check_compliance(product, docs):
    # Dummy: Require "bill of lading" and "tax certificate" for all products
    required = {"bill_of_lading", "tax_certificate"}
    provided = set(docs)
    missing = list(required - provided)
    if missing:
        return f"Missing documents: {', '.join(missing)}"
    return f"All required documents are present for {product}. No restrictions."
