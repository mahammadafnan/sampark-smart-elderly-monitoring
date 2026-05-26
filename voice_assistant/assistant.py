import json

import requests

from extractor import extract_health_data, make_reply
from llm_layer import ask_llm, enabled as llm_enabled, provider_name


BACKEND_URL = "http://127.0.0.1:5000"
STOP_WORDS = {"exit", "quit", "stop"}
GREETING_WORDS = {"hello", "hi", "hey", "namaste"}
CHECKIN_PHRASES = [
    "not feeling well",
    "feel tired",
    "feeling tired",
    "feel weak",
    "feeling weak",
    "dizzy",
    "pain",
    "unwell",
]
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
ADVICE_ONLY_PHRASES = [
    "should i",
    "do i need",
    "do i have to",
    "what to do",
    "what should i do",
]


def is_stop_command(message):
    words = message.lower().split()
    return bool(words) and all(word in STOP_WORDS for word in words)


def send_to_backend(data):
    response = requests.post(f"{BACKEND_URL}/health-data", json=data, timeout=10)
    response.raise_for_status()
    return response.json()


def send_emergency_to_backend(message):
    response = requests.post(
        f"{BACKEND_URL}/emergency",
        json={"message": message, "source": "voice_assistant"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def is_greeting(message):
    words = set(message.lower().replace(",", " ").replace(".", " ").split())
    return bool(words.intersection(GREETING_WORDS))


def needs_checkin(message):
    text = message.lower()
    return any(phrase in text for phrase in CHECKIN_PHRASES)


def is_emergency(message):
    text = message.lower()
    return any(phrase in text for phrase in EMERGENCY_PHRASES)


def is_advice_only(message):
    text = message.lower()
    return any(phrase in text for phrase in ADVICE_ONLY_PHRASES)


def emergency_response(message):
    if "call" in message.lower():
        return "This sounds urgent. Please press the emergency button or call your caretaker now. If you have severe symptoms, call local emergency services immediately."
    return "Chest pain or severe discomfort can be serious. Please stop activity, sit down, and contact your caretaker or doctor immediately."


class ConversationSession:
    def __init__(self):
        self.collected_data = {}
        self.last_question = None

    def reset(self):
        self.collected_data = {}
        self.last_question = None

    def handle(self, message):
        llm_reply = None
        extracted_data = {}
        had_new_data = False

        if is_emergency(message):
            emergency_alert = send_emergency_to_backend(message)
            return self.no_save_response(
                llm_reply or emergency_response(message),
                emergency=True,
                emergency_alert=emergency_alert,
            )

        if llm_enabled():
            try:
                llm_result = ask_llm(message, self.collected_data)
                llm_reply = llm_result["reply"]
                extracted_data = llm_result["data"]
            except Exception as error:
                print(f"LLM unavailable, using local assistant: {error}")

        if not extracted_data:
            extracted_data = extract_health_data(message)

        if extracted_data:
            had_new_data = any(
                self.collected_data.get(key) != value for key, value in extracted_data.items()
            )
            self.collected_data.update(extracted_data)

            if not had_new_data or is_advice_only(message):
                return {
                    "reply": llm_reply
                    or "I understand. Please follow your prescribed routine, and contact your caregiver if you are unsure.",
                    "extracted_data": dict(self.collected_data),
                    "backend_response": None,
                    "emergency": False,
                }

            saved_record = send_to_backend(self.collected_data)
            reply = llm_reply or make_reply(message, self.collected_data, saved_record)
            follow_up = self.next_question()
            if follow_up and saved_record.get("risk") != "High":
                reply = f"{reply} {follow_up}"

            return {
                "reply": reply,
                "extracted_data": dict(self.collected_data),
                "backend_response": saved_record,
                "emergency": False,
            }

        if is_greeting(message):
            return self.no_save_response(
                llm_reply
                or "Hello. I am here with you. How are you feeling today? Did you sleep well and take your medicine?"
            )

        if needs_checkin(message):
            self.last_question = "sleep"
            return self.no_save_response(
                llm_reply
                or "I am sorry you are not feeling well. How many hours did you sleep, and did you take your medicine?"
            )

        return self.no_save_response(
            llm_reply
            or "I heard you. Please tell me about your sleep, medicine, food, fall, heart rate, oxygen level, or steps."
        )

    def no_save_response(self, reply, emergency=False, emergency_alert=None):
        return {
            "reply": reply,
            "extracted_data": {},
            "backend_response": None,
            "emergency": emergency,
            "emergency_alert": emergency_alert,
        }

    def next_question(self):
        if "sleep_hours" not in self.collected_data:
            return "How many hours did you sleep last night?"
        if "missed_meds" not in self.collected_data:
            return "Did you take your medicine today?"
        if "missed_meals" not in self.collected_data:
            return "Did you eat your meals today?"
        if "falls" not in self.collected_data:
            return "Did you fall or feel dizzy today?"
        return None


DEFAULT_SESSION = ConversationSession()


def handle_user_message(message, session=None):
    active_session = session or DEFAULT_SESSION
    return active_session.handle(message)


def main():
    session = ConversationSession()
    print("SAMPARK Voice Assistant")
    print("Type what the elderly user says. Type 'exit' to stop.")
    if llm_enabled():
        print(f"LLM mode is enabled. Provider: {provider_name()}")
    print()

    while True:
        message = input("User: ").strip()
        if is_stop_command(message):
            print("Assistant: Take care. Goodbye.")
            break

        if not message:
            continue

        try:
            result = handle_user_message(message, session)
        except requests.exceptions.ConnectionError:
            print("Assistant: Backend is not running. Start Flask with 'python app.py' first.")
            continue
        except requests.exceptions.RequestException as error:
            print(f"Assistant: Could not send data to backend: {error}")
            continue

        print(f"Assistant: {result['reply']}")
        print("Structured data:")
        print(json.dumps(result["extracted_data"], indent=2))
        if result["backend_response"] is not None:
            print("Backend prediction:")
            print(json.dumps(result["backend_response"], indent=2))
        if result.get("emergency_alert") is not None:
            print("Emergency alert:")
            print(json.dumps(result["emergency_alert"], indent=2))
        print()


if __name__ == "__main__":
    main()
