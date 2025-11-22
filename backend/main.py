from flask import Flask, request, jsonify
from firebase_db import init_firebase, get_messages
from captain_agent import captain_conversation
from flask_cors import CORS
import time
import logging
from monitoring import log_api_call, check_safety_violations, record_performance_metric, monitor
from evaluation import evaluate_agent_response
from rag_system import get_rag_response, search_knowledge_base
from compliance.extract_text import extract_text_from_pdf
from compliance.verify_details import extract_key_fields, verify_with_backend
from datetime import datetime
from fpdf import FPDF  # ✅ Add this line

import os
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_firebase()

@app.route("/api/chat", methods=["POST"])
def chat():
    """Enhanced chat endpoint with monitoring and safety checks"""
    start_time = time.time()
    user = "demo"  # ensure defined for error paths
    session = "default"
    try:
        data = request.get_json(silent=True) or {}
        user = data.get("user", "demo")
        session = data.get("session", "default")
        user_key = f"{user}:{session}"
        message = data.get("message", "")
        if not message:
            raise ValueError("Missing 'message' in request body")
        # Check for safety violations
        safety_violations = check_safety_violations(message, user_key)
        if safety_violations:
            response_time = time.time() - start_time
            log_api_call("/api/chat", "POST", 400, response_time, user,
                        error_message="Safety violation detected")
            return jsonify({
                "reply": "I cannot process this request due to safety policy violations. Please rephrase your message.",
                "safety_violations": [v.__dict__ for v in safety_violations]
            }), 400
        # Process conversation
        reply = captain_conversation(user_key, message)
        # Record performance metrics
        response_time = time.time() - start_time
        record_performance_metric("response_time", response_time, "seconds", tags={"user": user, "session": session})
        # Log API call
        log_api_call("/api/chat", "POST", 200, response_time, user_key)
        # Evaluate response quality
        try:
            evaluation = evaluate_agent_response(message, reply, {"user": user, "session": session})
            record_performance_metric("llm_judge_score", evaluation.llm_judge_score, "score", tags={"user": user, "session": session})
        except Exception as e:
            logger.warning(f"Evaluation failed: {e}")
        return jsonify({"reply": reply})
    except Exception as e:
        response_time = time.time() - start_time
        log_api_call("/api/chat", "POST", 500, response_time, f"{user}:{session}", error_message=str(e))
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({"reply": "I encountered an error processing your request. Please try again."}), 500

@app.route("/api/history", methods=["GET"])
def history():
    """Get chat history with monitoring"""
    start_time = time.time()
    user = request.args.get("user", "demo")
    session = request.args.get("session", "default")
    user_key = f"{user}:{session}"
    
    try:
        hist = get_messages(user_key)
        res = [{"role": m["role"], "content": m["content"]} for k, m in (hist or {}).items()]
        
        response_time = time.time() - start_time
        log_api_call("/api/history", "GET", 200, response_time, user_key)
        
        return jsonify(res)
    except Exception as e:
        response_time = time.time() - start_time
        log_api_call("/api/history", "GET", 500, response_time, user_key, error_message=str(e))
        return jsonify({"error": "Failed to retrieve history"}), 500

@app.route("/api/rag", methods=["POST"])
def rag_query():
    """RAG system endpoint for knowledge base queries"""
    start_time = time.time()
    
    try:
        data = request.json
        query = data.get("query", "")
        category = data.get("category", None)
        user = data.get("user", "demo")
        
        # Get RAG response
        response = get_rag_response(query, category, {"user": user})
        
        response_time = time.time() - start_time
        log_api_call("/api/rag", "POST", 200, response_time, user)
        
        return jsonify({"response": response})
        
    except Exception as e:
        response_time = time.time() - start_time
        log_api_call("/api/rag", "POST", 500, response_time, user, error_message=str(e))
        return jsonify({"error": "RAG query failed"}), 500

@app.route("/api/search", methods=["GET"])
def search_knowledge():
    """Search knowledge base endpoint"""
    start_time = time.time()
    
    try:
        query = request.args.get("q", "")
        category = request.args.get("category", None)
        user = request.args.get("user", "demo")
        
        results = search_knowledge_base(query, category)
        
        response_time = time.time() - start_time
        log_api_call("/api/search", "GET", 200, response_time, user)
        
        return jsonify({"results": results})
        
    except Exception as e:
        response_time = time.time() - start_time
        log_api_call("/api/search", "GET", 500, response_time, user, error_message=str(e))
        return jsonify({"error": "Search failed"}), 500

@app.route("/api/monitoring", methods=["GET"])
def get_monitoring_data():
    """Get monitoring and observability data"""
    start_time = time.time()
    user = request.args.get("user", "admin")
    
    try:
        # Get monitoring report
        report = monitor.generate_monitoring_report()
        
        response_time = time.time() - start_time
        log_api_call("/api/monitoring", "GET", 200, response_time, user)
        
        return jsonify(report)
        
    except Exception as e:
        response_time = time.time() - start_time
        log_api_call("/api/monitoring", "GET", 500, response_time, user, error_message=str(e))
        return jsonify({"error": "Monitoring data unavailable"}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "service": "NITISARA Captain AI"
    })

@app.route("/api/compliance/upload", methods=["POST"])
def compliance_upload():
    """
    Handles PDF uploads for compliance & documentation verification.
    1. Extracts text from PDF.
    2. Extracts key fields (e.g., product name, HSN code, cargo info).
    3. Verifies with backend (e.g., order system or cargo manifest).
    """
    start_time = time.time()
    user = request.form.get("user", "demo")

    try:
        # Step 1: Ensure file exists
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["file"]
        filename = file.filename
        file_path = os.path.join("uploads", filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(file_path)

        # Step 2: Extract text
        extracted_text = extract_text_from_pdf(file_path)

        # Step 3: Extract structured data
        key_fields = extract_key_fields(extracted_text)

        # Step 4: Verify with backend/order DB
        verification_result = verify_with_backend(key_fields)

        # Step 5: Combine summary
        summary = {
            "file_name": filename,
            "summary": extracted_text[:500],  # trimmed preview
            "key_fields": key_fields,
            "verification": verification_result,
        }

        response_time = time.time() - start_time
        log_api_call("/api/compliance/upload", "POST", 200, response_time, user)

        return jsonify(summary)

    except Exception as e:
        response_time = time.time() - start_time
        log_api_call("/api/compliance/upload", "POST", 500, response_time, user, error_message=str(e))
        logger.error(f"Compliance upload error: {e}")
        return jsonify({"error": "Failed to process document"}), 500

"""
@app.route('/api/generate_laidbill', methods=['POST'])
def generate_laidbill():
    
    from fpdf import FPDF
    from datetime import datetime

    try:
        data = request.get_json()
        os.makedirs("bills", exist_ok=True)
        filename = f"laidbill_{int(time.time())}.pdf"
        filepath = os.path.join("bills", filename)

        pdf = FPDF()
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 12, "BILL OF LADING", ln=True, align="C")
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")

        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Shipment Details", ln=True)
        pdf.set_font("Helvetica", size=11)

        def field(label, key):
            pdf.cell(0, 8, f"{label}: {data.get(key, 'N/A')}", ln=True)

        field("Customer", "customer")
        field("Operator", "operator")
        field("Administrator", "administrator")
        field("Carrier", "carrier")
        field("Driver", "driver")
        field("Truck No.", "truck_number")
        field("Trailer No.", "trailer_number")
        field("Gross Weight", "gross")
        field("Tare Weight", "tare")
        field("Net Weight", "net")
        field("PO #", "po_number")
        field("Job #", "job_number")
        field("SO #", "so_number")

        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 6, 
            "HEALTH HAZARD WARNING: CONTAINS FREE SILICA. DO NOT BREATHE DUST. "
            "Follow all safety protocols for handling crystalline silica."
        )

        pdf.output(filepath)

        return jsonify({
            "message": "Laid Bill generated successfully",
            "file_url": f"http://127.0.0.1:5000/{filepath}",
            **data
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to generate Laid Bill: {str(e)}"}), 500
"""


@app.route("/api/generate_laidbill", methods=["POST"])
def generate_laidbill():
    data = request.get_json()
    print("DEBUG BILL DATA:", data)  # 👀 Confirm incoming data

    # ✅ Use field names exactly as sent from frontend
    customer = data.get("customer")
    operator = data.get("operator")
    administrator = data.get("administrator")
    carrier = data.get("carrier")
    driver = data.get("driver")
    truck = data.get("truck_number")
    trailer = data.get("trailer_number")
    gross = data.get("gross")
    tare = data.get("tare")
    net = data.get("net")
    po = data.get("po_number")
    job = data.get("job_number")
    so = data.get("so_number")

    # 📁 Create folder inside static if missing
    bill_folder = os.path.join(os.getcwd(), "static", "bills")
    os.makedirs(bill_folder, exist_ok=True)

    filename = f"laidbill_{int(datetime.now().timestamp())}.pdf"
    filepath = os.path.join(bill_folder, filename)

    # 🧾 Generate a simple PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="BILL OF LADING", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Customer: {customer}", ln=True)
    pdf.cell(200, 10, txt=f"Operator: {operator}", ln=True)
    pdf.cell(200, 10, txt=f"Administrator: {administrator}", ln=True)
    pdf.cell(200, 10, txt=f"Carrier: {carrier}", ln=True)
    pdf.cell(200, 10, txt=f"Driver: {driver}", ln=True)
    pdf.cell(200, 10, txt=f"Truck #: {truck}", ln=True)
    pdf.cell(200, 10, txt=f"Trailer #: {trailer}", ln=True)
    pdf.cell(200, 10, txt=f"Gross Weight: {gross}", ln=True)
    pdf.cell(200, 10, txt=f"Net Weight: {net}", ln=True)
    pdf.output(filepath)

    print(f"✅ LAID BILL GENERATED: {filepath}")

    # ✅ Return the public URL
    return jsonify({
        "message": "Laid Bill generated successfully",
        "file_url": f"http://127.0.0.1:5000/static/bills/{filename}",
        "customer": customer,
        "driver": driver,
        "gross": gross,
        "net": net
    })

@app.route('/api/generate_bill', methods=['POST'])
def generate_bill():
    """Generate a simple Laid Bill (mock backend)."""

    try:
        data = request.get_json(force=True)
        print("DEBUG BILL DATA:", data)

        company = data.get("companyName")
        items_raw = data.get('items', [])
        tax = data.get('tax', 0)
        total = data.get('total', 0)

        # ✅ Handle cases where 'items' comes as string instead of list
        if isinstance(items_raw, str):
            try:
                items = json.loads(items_raw.replace("'", '"'))
            except Exception as e:
                return jsonify({"error": f"Invalid items JSON format: {str(e)}"}), 400
        else:
            items = items_raw

        # ✅ Type safety
        try:
            tax = float(tax)
        except:
            tax = 0

        # ✅ Ensure company name is provided
        if not company:
            return jsonify({"error": "Missing company name"}), 400

        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"error": "Missing or invalid items list"}), 400

        # ✅ Compute totals safely
        subtotal = sum(float(item.get('amount', 0)) for item in items)
        tax_amount = subtotal * (tax / 100)
        grand_total = subtotal + tax_amount

        # ✅ Build and return summary
        bill_summary = {
            "company": company,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "subtotal": round(subtotal, 2),
            "tax": f"{tax}%",
            "tax_amount": round(tax_amount, 2),
            "grand_total": round(grand_total, 2),
            "items": items
        }

        print("✅ BILL GENERATED SUCCESSFULLY:", bill_summary)
        return jsonify(bill_summary), 200

    except Exception as e:
        print("❌ BILL GENERATION ERROR:", e)
        return jsonify({"error": f"Bill generation failed: {str(e)}"}), 500
if __name__ == "__main__":
    logger.info("Starting NITISARA Captain AI Server...")
    app.run(port=5000, debug=True)
