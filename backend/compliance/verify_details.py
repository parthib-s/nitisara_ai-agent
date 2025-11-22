import re

def extract_key_fields(text: str):
    """Extract key compliance details such as product, HSN, cargo, etc."""
    data = {}

    # Simple regex patterns (can be improved later)
    hsn_match = re.search(r"H\.?S\.?N\.?\s*Code[:\-]?\s*([0-9]{4,8})", text, re.IGNORECASE)
    product_match = re.search(r"Product\s*[:\-]?\s*([\w\s]+)", text, re.IGNORECASE)
    weight_match = re.search(r"Weight\s*[:\-]?\s*([\d\.]+\s*\w*)", text, re.IGNORECASE)

    data["product_name"] = product_match.group(1).strip() if product_match else "N/A"
    data["hsn_code"] = hsn_match.group(1).strip() if hsn_match else "N/A"
    data["weight"] = weight_match.group(1).strip() if weight_match else "N/A"
    return data

def verify_with_backend(fields):
    """
    Mock backend verification.
    In real case, this should check fields against a database or manifest.
    """
    verified = True
    missing_fields = [k for k, v in fields.items() if v == "N/A"]
    
    result = {
        "status": "Verified" if verified else "Failed",
        "missing_fields": missing_fields,
        "remarks": "All mandatory fields present" if not missing_fields else "Missing key details",
    }
    return result
