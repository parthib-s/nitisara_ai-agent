from .extract_text import extract_text_from_pdf
from .verify_details import extract_key_fields, verify_with_backend

def check_compliance(file_path):
    """
    Reads a PDF file, extracts text, finds key fields, 
    and verifies them with backend rules.
    """
    try:
        text = extract_text_from_pdf(file_path)
        key_fields = extract_key_fields(text)
        verification = verify_with_backend(key_fields)
        
        return {
            "file_name": file_path.split("/")[-1],
            "summary": text[:500],  # short summary preview
            "key_fields": key_fields,
            "verification": verification
        }
    except Exception as e:
        return {"error": f"Compliance check failed: {str(e)}"}
