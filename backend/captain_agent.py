from gemini_chain import get_llm_response
from compliance import check_compliance
from rate import estimate_rate
from firebase_db import get_state, store_state, append_message

def captain_conversation(user, user_message):
    state = get_state(user)
    step = state.get('step', 'start')

    if step == 'start':
        store_state(user, {'step': 'order_location'})
        reply = "Hello! I'm Captain. Where do you want to ship your order?"
    elif step == 'order_location':
        state['origin'] = user_message
        store_state(user, {**state, 'step': 'cargo_details'})
        reply = "Great. Can you describe your cargo or shipment type?"
    elif step == 'cargo_details':
        state['cargo'] = user_message
        store_state(user, {**state, 'step': 'compliance_docs'})
        reply = "To check trade compliance, please list your available documents (comma-separated)."
    elif step == 'compliance_docs':
        docs = [d.strip() for d in user_message.split(',')]
        compliance_msg = check_compliance(state.get('cargo', ''), docs)
        state['docs'] = docs
        store_state(user, {**state, 'step': 'rate_questions'})
        reply = compliance_msg + " Now, let's estimate the shipping rate. What's the cargo size?"
    elif step == 'rate_questions':
        state['size'] = user_message
        store_state(user, {**state, 'step': 'rate_weight'})
        reply = "What's the cargo weight (kg)?"
    elif step == 'rate_weight':
        state['weight'] = user_message
        store_state(user, {**state, 'step': 'rate_timeline'})
        reply = "What's your schedule or required timeline? (standard/express)"
    elif step == 'rate_timeline':
        state['timeline'] = user_message
        store_state(user, {**state, 'step': 'rate_done'})
        ship_details = {
            "size": state.get("size"),
            "weight": state.get("weight"),
            "route": f"{state.get('origin')} to destination",  # You can prompt for destination for full demo
            "timeline": state.get("timeline")
        }
        rate_msg = estimate_rate(ship_details)
        reply = rate_msg + " Would you like to book this shipment?"
    else:
        reply = "Thank you for using Captain! If you'd like another quote, just start a new chat."

    append_message(user, 'user', user_message)
    append_message(user, 'captain', reply)
    return reply
