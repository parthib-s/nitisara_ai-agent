from gemini_chain import get_llm_response
from rag import check_compliance_rag  # RAG-powered
from rate import estimate_rate
from firebase_db import get_state, store_state, append_message
"""
def captain_conversation(user, user_message):
    state = get_state(user) or {}
    step = state.get('step', 'start')
    print("DEBUG: user =", user)
    print("DEBUG: retrieved state =", state)
    print("DEBUG: current step =", step)

    if step == 'start':
        store_state(user, {'step': 'order_location'})
        reply = "Hello! I'm Captain. Where do you want to ship your order?"
    
    elif step == 'order_location':
        state['origin'] = user_message
        store_state(user, {'origin': user_message, 'step': 'cargo_details'})
        reply = "Great. Can you describe your cargo or shipment type?"
    
    elif step == 'cargo_details':
        state['cargo'] = user_message
        store_state(user, {'cargo': user_message, 'step': 'compliance_docs'})
        reply = "To check trade compliance, please list your available documents (comma-separated)."
    
    elif step == 'compliance_docs':
        docs = [d.strip() for d in user_message.split(',')]
        state['docs'] = docs
        try:
            compliance_msg = check_compliance_rag(state.get('cargo', ''), docs)
        except Exception as e:
            print(f"RAG compliance error: {e}")
            # fallback
            required = {"bill_of_lading", "tax_certificate"}
            missing = list(required - set(docs))
            if missing:
                compliance_msg = f"(Fallback) Missing documents: {', '.join(missing)}"
            else:
                compliance_msg = f"(Fallback) All required documents are present for {state.get('cargo', '')}. No restrictions."

        store_state(user, {'docs': docs, 'step': 'rate_questions'})
        reply = compliance_msg + " Now, let's estimate the shipping rate. What's the cargo size?"
    
    elif step == 'rate_questions':
        state['size'] = user_message
        store_state(user, {'size': user_message, 'step': 'rate_weight'})
        reply = "What's the cargo weight (kg)?"
    
    elif step == 'rate_weight':
        state['weight'] = user_message
        store_state(user, {'weight': user_message, 'step': 'rate_timeline'})
        reply = "What's your schedule or required timeline? (standard/express)"
    
    elif step == 'rate_timeline':
        state['timeline'] = user_message
        store_state(user, {'timeline': user_message, 'step': 'rate_done'})
        ship_details = {
            "size": state.get("size"),
            "weight": state.get("weight"),
            "route": f"{state.get('origin')} to destination",
            "timeline": state.get("timeline")
        }
        rate_msg = estimate_rate(ship_details)
        reply = rate_msg + " Would you like to book this shipment?"
    
    else:
        reply = "Thank you for using Captain! If you'd like another quote, just start a new chat."

    append_message(user, 'user', user_message)
    append_message(user, 'captain', reply)
    return reply
"""
def captain_conversation(user, user_message):
     # Restart conversation on explicit user command
    if user_message.lower() in ["restart", "new quote", "start"]:
        state = {'step': 'start'}
        store_state(user, state)
        reply = "Conversation restarted. Hello! I'm Captain. Where do you want to ship your order?"
        append_message(user, 'user', user_message)
        append_message(user, 'captain', reply)
        return reply
    state = get_state(user) or {}
    step = state.get('step', 'start')
    print("DEBUG: user =", user)
    print("DEBUG: retrieved state =", state)
    print("DEBUG: current step =", step)

   

    if step == 'start':
        state['step'] = 'order_location'
        store_state(user, state)
        reply = "Hello! I'm Captain. Where do you want to ship your order?"
    elif step == 'order_location':
        state['origin'] = user_message
        state['step'] = 'cargo_details'
        store_state(user, state)
        reply = "Great. Can you describe your cargo or shipment type?"
    elif step == 'cargo_details':
        state['cargo'] = user_message
        state['step'] = 'compliance_docs'
        store_state(user, state)
        reply = "To check trade compliance, please list your available documents (comma-separated)."
    

    elif step == 'compliance_docs':
        docs = [d.strip() for d in user_message.split(',') if d.strip()]
        state['docs'] = docs
        compliance_msg = ""
        try:
            print(f"DEBUG: Running check_compliance_rag for product: {state.get('cargo', '')} with docs: {docs}")
            compliance_msg = check_compliance_rag(state.get('cargo', ''), docs)
            print(f"DEBUG: Compliance message received: {compliance_msg}")
            if not compliance_msg or compliance_msg.strip() == "":
                compliance_msg = "No compliance info found. Please check your documents and try again."
        except Exception as e:
            print(f"ERROR during RAG compliance check: {e}")
            required = {"bill_of_lading", "tax_certificate"}
            missing = list(required - set(docs))
            if missing:
                compliance_msg = f"(Fallback) Missing documents: {', '.join(missing)}"
            else:
                compliance_msg = f"(Fallback) All required documents are present for {state.get('cargo', '')}. No restrictions."
        
        # Always advance the step and store state regardless
        state['step'] = 'rate_questions'
        store_state(user, state)
        reply = compliance_msg + " Now, let's estimate the shipping rate. What's the cargo size?"


    elif step == 'rate_questions':
        state['size'] = user_message
        state['step'] = 'rate_weight'
        store_state(user, state)
        reply = "What's the cargo weight (kg)?"
    elif step == 'rate_weight':
        state['weight'] = user_message
        state['step'] = 'rate_timeline'
        store_state(user, state)
        reply = "What's your schedule or required timeline? (standard/express)"
    elif step == 'rate_timeline':
        state['timeline'] = user_message
        ship_details = {
            "size": state.get("size"),
            "weight": state.get("weight"),
            "route": f"{state.get('origin')} to destination",
            "timeline": state.get("timeline")
        }
        rate_msg = estimate_rate(ship_details)
        state['step'] = 'rate_done'
        store_state(user, state)
        reply = rate_msg + " Would you like to book this shipment?"
    elif step == 'rate_done':
        reply = "Thank you for using Captain! If you'd like another quote, just start a new chat."
        # Reset state after completion so next message restarts flow
        state = {'step': 'start'}
        store_state(user, state)
    else:
        reply = "Conversation error: Unrecognized state. Restarting."
        state = {'step': 'start'}
        store_state(user, state)

    append_message(user, 'user', user_message)
    append_message(user, 'captain', reply)
    return reply
