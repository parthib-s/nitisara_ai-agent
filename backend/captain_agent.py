import json
import re
import os
from datetime import datetime
from fpdf import FPDF
from rate import estimate_rate
from firebase_db import get_state, store_state, append_message, get_messages
from foundational_config import ask_gemini

class NitisaraCaptain:
    """
    NITISARA Captain AI - Domain Restricted
    - Same intelligent architecture as before.
    - NEW: Enforces domain boundaries (Logistics/Supply Chain only).
    - Refuses to answer general trivia or off-topic questions.
    """

    def __init__(self):
        self.system_prompt = """
        You are Captain, a senior logistics consultant for NITISARA.
        
        CORE PROTOCOL:
        1. **Analyze First**: Determine the user's intent before acting.
        2. **Geospatial Expert**: Calculate real distances (km) for every route.
        3. **Strict Booking**: ONLY authorize a booking ("CONFIRM_BOOKING") if the user explicitly says "yes", "confirm", or "proceed".
        4. **Negation Handling**: If the user says "no", "don't", "cancel", or "wait", you MUST NOT confirm.
        5. **DOMAIN RESTRICTION**: You are a specialized AI for Logistics, Freight, Supply Chain, and ESG.
           - IF the user asks about these topics: Answer professionally.
           - IF the user asks about general trivia (e.g., "sunrise", "movies", "weather", "jokes"): You MUST politely refuse. Say: "I am a logistics consultant and can only assist with shipping, rates, and supply chain queries."
        
        DATA REQUIREMENTS:
        To generate a quote, you need: Origin, Destination, Cargo Description, and Weight.
        """

    def process_conversation(self, user, message):
        # 1. Save User Message
        append_message(user, "user", message)

        # 2. Get Context
        state = get_state(user)
        if not state or "booking_data" not in state:
            state = {
                "step": "conversation", 
                "booking_data": {
                    "origin": None, 
                    "destination": None, 
                    "cargo": None, 
                    "weight": None,
                    "distance_km": None
                }
            }
        
        history_text = self._format_history(get_messages(user))

        # 3. THE LLM BRAIN - Decides Action & Content
        decision = self._decide_action_with_llm(message, state["booking_data"], history_text)

        # 4. Execute Logic based on LLM Decision
        action = decision.get("action")
        reply_text = decision.get("reply")
        data_updates = decision.get("extracted_data", {})

        # Update State with any new data found
        current_data = state["booking_data"]
        for k, v in data_updates.items():
            if v is not None: 
                current_data[k] = v
                
        state["booking_data"] = current_data
        store_state(user, state)

        # --- ACTION HANDLERS ---
        
        if action == "GENERATE_QUOTE":
            if not current_data.get("distance_km"):
                current_data["distance_km"] = decision.get("distance_km", 5000)
                state["booking_data"] = current_data
            
            quote_details = self._calculate_quote(current_data)
            final_response = f"{reply_text}\n\n{quote_details}\n\n**Would you like to confirm this booking?**"
            store_state(user, state)

        elif action == "CONFIRM_BOOKING":
            order_id = f"NTS-{abs(hash(user + datetime.now().isoformat())) % 10000:04d}"
            bill_url = self._generate_bill_pdf(current_data, order_id)
            
            final_response = (
                f"🎉 **Booking Confirmed!**\n"
                f"🆔 **Order ID:** {order_id}\n"
                f"📄 **[Download Bill of Lading]({bill_url})**\n\n"
                f"{reply_text}"
            )
            store_state(user, {"step": "conversation", "booking_data": {}})

        elif action == "CANCEL_BOOKING":
             store_state(user, {"step": "conversation", "booking_data": {}})
             final_response = reply_text

        else:
            # "INFO", "ASK_DETAILS", "GENERAL_QUERY", "DECLINE"
            final_response = reply_text

        # 5. Save & Return Response
        append_message(user, "captain", final_response)
        return final_response

    def _decide_action_with_llm(self, message, current_data, history_text):
        """
        Single-shot decision making with Domain Restriction.
        """
        prompt = f"""
        **Conversation History:**
        {history_text}

        **Current Data State:**
        {json.dumps(current_data)}

        **User's Latest Message:**
        "{message}"

        **YOUR TASK:**
        1. Analyze Intent.
        2. **SCOPE CHECK**: Is the user asking about logistics/shipping? 
           - YES -> Proceed.
           - NO (e.g. sports, weather, life) -> Set intent to 'GENERAL_QUERY' and 'reply' with a polite refusal based on your system instructions.
        3. Extract Data (Origin, Dest, Cargo, Weight).
        4. Decide Action.

        **VALID ACTIONS:**
        - `UPDATE_INFO`: Gathering details.
        - `GENERATE_QUOTE`: Have all info + user wants quote.
        - `CONFIRM_BOOKING`: Explicit "Yes/Confirm".
        - `CANCEL_BOOKING`: User wants to quit.
        - `GENERAL_QUERY`: General questions (Logistics = Answer; Off-topic = Refuse).

        **OUTPUT JSON ONLY:**
        {{
            "action": "ONE_OF_THE_VALID_ACTIONS",
            "extracted_data": {{ 
                "origin": "City, Country" or null, 
                "destination": "City, Country" or null, 
                "cargo": "desc" or null,
                "weight": 1000.0 (float) or null,
                "distance_km": 12345 (int) or null
            }},
            "reply": "Natural response text."
        }}
        """
        try:
            raw = ask_gemini(prompt, self.system_prompt)
            return self._clean_and_parse_json(raw)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"action": "GENERAL_QUERY", "reply": "I apologize, I'm processing a high volume of requests. Could you repeat that?"}

    def _calculate_quote(self, data):
        weight = data.get("weight")
        if not weight and isinstance(data.get("cargo"), str):
            w_match = re.search(r'(\d[\d,]*)\s*kg', data["cargo"].lower().replace(",", ""))
            if w_match: weight = float(w_match.group(1))
        if not weight: weight = 500.0

        dist = data.get("distance_km", 8000)
        
        return estimate_rate({
            "origin": data["origin"],
            "destination": data["destination"],
            "cargo": data["cargo"],
            "weight": weight,
            "distance_km": dist
        })

    def _clean_and_parse_json(self, text):
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end])
        except:
            return {"action": "GENERAL_QUERY", "reply": "I understood, but had a system error. Please try again."}

    def _format_history(self, raw_history):
        if not raw_history: return "No history."
        sorted_msgs = sorted(raw_history.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
        lines = []
        for _, msg in sorted_msgs[-6:]:
            lines.append(f"{msg['role'].upper()}: {msg['content']}")
        return "\n".join(lines)

    def _generate_bill_pdf(self, data, order_id):
        folder = os.path.join(os.getcwd(), "static", "bills")
        os.makedirs(folder, exist_ok=True)
        filename = f"laidbill_{order_id}.pdf"
        filepath = os.path.join(folder, filename)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt="NITISARA BILL OF LADING", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Order ID: {order_id}", ln=True)
        pdf.cell(200, 10, txt=f"Origin: {data.get('origin', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Destination: {data.get('destination', 'N/A')}", ln=True)
        
        c_desc = data.get("cargo", "General Cargo")
        w_val = data.get("weight", "N/A")
        pdf.cell(200, 10, txt=f"Cargo: {c_desc}", ln=True)
        pdf.cell(200, 10, txt=f"Total Weight: {w_val} kg", ln=True)
        
        pdf.output(filepath)
        return f"http://127.0.0.1:5000/static/bills/{filename}"

def captain_conversation(user, message):
    captain = NitisaraCaptain()
    return captain.process_conversation(user, message)