import re
import os

def check_compliance(product, docs=None):
    """
    NITISARA Hybrid Trade Compliance Checker
    Handles both text-based cargo descriptions and document-based checks.
    """
    if docs is None:
        docs = []

    # If product seems like a file path, handle it separately
    if os.path.exists(product):
        return _analyze_document_compliance(product)

    # Otherwise treat it as a text description (like “2 pallets, 600 kg”)
    return _analyze_compliance(product, docs)


def _analyze_document_compliance(file_path):
    """Mock document-based compliance for uploaded files."""
    try:
        import fitz  # PyMuPDF
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text("text")
        return f"📄 Compliance Check (Document Mode): Successfully parsed {len(text)} characters from PDF."
    except Exception as e:
        return f"⚠️ Document compliance scan failed: {str(e)}"


def _analyze_compliance(product, docs):
    """Analyze compliance requirements based on cargo/product text."""
    product = str(product or "").lower()
    docs = docs or []

    # Extract keywords to detect type
    if re.search(r'chemical|acid|paint|hazard', product):
        product_type = "chemical"
    elif re.search(r'food|snack|spice|beverage', product):
        product_type = "food"
    elif re.search(r'electronic|mobile|computer|device', product):
        product_type = "electronics"
    elif re.search(r'steel|metal|copper|wire', product):
        product_type = "metal"
    else:
        product_type = "general cargo"

    # Hazard detection
    hazardous = bool(re.search(r'chemical|acid|hazard|explosive|flammable', product))
    fragile = bool(re.search(r'glass|fragile|electronic|delicate', product))
    restricted = bool(re.search(r'weapon|ivory|endangered|narcotic', product))

    # Standard docs
    standard_docs = ["Commercial Invoice", "Packing List", "Bill of Lading", "Certificate of Origin"]
    provided = {doc.lower().replace(" ", "_") for doc in docs}
    missing = [doc for doc in standard_docs if doc.lower().replace(" ", "_") not in provided]

    # Core compliance output
    status = "✅ COMPLIANCE VERIFIED" if not missing and not hazardous and not restricted else "⚠️ COMPLIANCE ATTENTION REQUIRED"
    result = [f"{status}\n"]

    # Append analysis
    result.append(f"🧾 Product Type: {product_type.title()}")
    result.append(f"• Hazardous: {'Yes ❌' if hazardous else 'No ✅'}")
    result.append(f"• Fragile: {'Yes ⚠️' if fragile else 'No ✅'}")
    result.append(f"• Restricted: {'Yes ❌' if restricted else 'No ✅'}")

    if missing:
        result.append("\n📄 Missing Required Documents:")
        for doc in missing:
            result.append(f"• {doc}")

    # HS code suggestion
    hs_code = _suggest_hs_code(product)
    result.append(f"\n📋 Suggested HS Code: {hs_code}")

    # Final compliance note
    result.append("\n🌍 Trade Guidance:")
    result.append("• Verify destination import restrictions.")
    result.append("• Ensure packaging and labeling meet IMO standards.")
    result.append("• Validate insurance coverage and customs docs.")

    return "\n".join(result)


def _suggest_hs_code(product):
    """Suggest HS code intelligently based on text."""
    p = product.lower()
    if "copper" in p:
        return "7408.19.00"  # Copper wire
    if "steel" in p:
        return "7326.90.90"
    if "textile" in p or "fabric" in p:
        return "6203.42.00"
    if "food" in p or "spice" in p:
        return "2106.90.00"
    if "chemical" in p:
        return "3822.00.00"
    if "electronic" in p or "mobile" in p:
        return "8517.12.00"
    return "9999.99.99"
 