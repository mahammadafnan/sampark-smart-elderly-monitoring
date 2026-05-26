import sys
from pathlib import Path

from database import create_alert, create_health_record, update_alert_notification
from email_notifier import send_caretaker_email


VOICE_DIR = Path(__file__).resolve().parent.parent / "voice_assistant"
if str(VOICE_DIR) not in sys.path:
    sys.path.insert(0, str(VOICE_DIR))

from extractor import extract_health_data  # noqa: E402
from llm_layer import ask_llm, enabled as llm_enabled, provider_name  # noqa: E402


SESSIONS = {}

EMERGENCY_PHRASES = [
    "chest pain",
    "pain in my chest",
    "heart pain",
    "can't breathe",
    "cannot breathe",
    "breathing problem",
    "call my caretaker",
    "call caretaker",
    "call caregiver",
    "call doctor",
    "emergency",
    "i am dying",
    "i'm dying",
    "dying",
]

GREETING_WORDS = {"hello", "hi", "hey", "namaste"}
CHECKIN_PHRASES = ["not feeling well", "feel tired", "feeling tired", "feel weak", "feeling weak", "dizzy", "pain", "unwell"]
ADVICE_ONLY_PHRASES = ["should i", "do i need", "do i have to", "what to do", "what should i do"]


def session_data(session_id):
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {}
    return SESSIONS[session_id]


def contains_any(text, phrases):
    return any(phrase in text for phrase in phrases)


def is_emergency(message):
    return contains_any(message.lower(), EMERGENCY_PHRASES)


def is_greeting(message):
    words = set(message.lower().replace(",", " ").replace(".", " ").split())
    return bool(words.intersection(GREETING_WORDS))


def needs_checkin(message):
    return contains_any(message.lower(), CHECKIN_PHRASES)


def is_advice_only(message):
    return contains_any(message.lower(), ADVICE_ONLY_PHRASES)


def emergency_reply(message):
    if "call" in message.lower():
        return "This sounds urgent. I am sending an alert to your caretaker now. Please stay calm and call local emergency services if symptoms are severe."
    return "This may be serious. I am sending an alert to your caretaker now. Please sit down, rest, and get help immediately."


def create_emergency_alert(message, source):
    alert = create_alert(
        None,
        "High",
        "Emergency",
        f"Emergency from {source}: {message}",
    )

    email_result = send_caretaker_email(
        "SAMPARK Emergency Alert",
        (
            "SAMPARK detected an emergency.\n\n"
            f"Source: {source}\n"
            f"Message: {message}\n\n"
            "Please check on the elderly person immediately."
        ),
    )
    status = "sent" if email_result["sent"] else "simulated"
    alert = update_alert_notification(alert["id"], status)
    return {"alert": alert, "email": email_result}


def next_question(data):
    if "sleep_hours" not in data:
        return "How many hours did you sleep last night?"
    if "missed_meds" not in data:
        return "Did you take your medicine today?"
    if "missed_meals" not in data:
        return "Did you eat your meals today?"
    return None


def no_save_response(reply, session_id, emergency=False, emergency_alert=None):
    return {
        "reply": reply,
        "session_id": session_id,
        "extracted_data": {},
        "backend_response": None,
        "emergency": emergency,
        "emergency_alert": emergency_alert,
        "llm_enabled": llm_enabled(),
        "llm_provider": provider_name() if llm_enabled() else "local",
    }


def handle_assistant_message(message, session_id="web-default", source="web_voice"):
    current_data = session_data(session_id)
    llm_reply = None
    extracted_data = {}

    if is_emergency(message):
        emergency_alert = create_emergency_alert(message, source)
        return no_save_response(
            emergency_reply(message),
            session_id,
            emergency=True,
            emergency_alert=emergency_alert,
        )

    if llm_enabled():
        try:
            llm_result = ask_llm(message, current_data)
            llm_reply = llm_result["reply"]
            extracted_data = llm_result["data"]
        except Exception as error:
            print(f"LLM unavailable for web assistant, using local fallback: {error}")

    if not extracted_data:
        extracted_data = extract_health_data(message)

    if extracted_data:
        had_new_data = any(current_data.get(key) != value for key, value in extracted_data.items())
        current_data.update(extracted_data)

        if not had_new_data or is_advice_only(message):
            return {
                "reply": llm_reply or "I understand. Please follow your prescribed routine, and contact your caregiver if you are unsure.",
                "session_id": session_id,
                "extracted_data": dict(current_data),
                "backend_response": None,
                "emergency": False,
                "emergency_alert": None,
                "llm_enabled": llm_enabled(),
                "llm_provider": provider_name() if llm_enabled() else "local",
            }

        record = create_health_record(current_data)
        reply = llm_reply or f"Your current risk is {record['risk']}."
        follow_up = next_question(current_data)
        if follow_up and record["risk"] != "High":
            reply = f"{reply} {follow_up}"

        return {
            "reply": reply,
            "session_id": session_id,
            "extracted_data": dict(current_data),
            "backend_response": record,
            "emergency": False,
            "emergency_alert": None,
            "llm_enabled": llm_enabled(),
            "llm_provider": provider_name() if llm_enabled() else "local",
        }

    if is_greeting(message):
        return no_save_response(llm_reply or "Hello. I am here with you. How are you feeling today?", session_id)

    if needs_checkin(message):
        return no_save_response(
            llm_reply or "I am sorry you are not feeling well. How many hours did you sleep, and did you take your medicine?",
            session_id,
        )

    return no_save_response(
        llm_reply or "I heard you. Please tell me about sleep, medicine, food, heart rate, oxygen level, or steps.",
        session_id,
    )
