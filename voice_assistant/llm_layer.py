import json
import os
import time


OPENAI_MODEL_NAME = os.getenv("SAMPARK_OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL_NAME = os.getenv("SAMPARK_GEMINI_MODEL", "gemini-2.5-flash-lite")


HEALTH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {
            "type": "string",
            "description": "A short, caring reply to the elderly user.",
        },
        "data": {
            "type": "object",
            "properties": {
                "heart_rate": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                "spo2": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                "steps": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                "sleep_hours": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                "missed_meds": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                "missed_meals": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                "missed_meds_detail": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "missed_meals_detail": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "falls": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            },
            "required": [
                "heart_rate",
                "spo2",
                "steps",
                "sleep_hours",
                "missed_meds",
                "missed_meals",
                "missed_meds_detail",
                "missed_meals_detail",
                "falls",
            ],
            "additionalProperties": False,
        },
    },
    "required": ["reply", "data"],
    "additionalProperties": False,
}

GEMINI_HEALTH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {
            "type": "string",
            "description": "A short, caring reply to the elderly user.",
        },
        "data": {
            "type": "object",
            "properties": {
                "heart_rate": {"type": ["integer", "null"]},
                "spo2": {"type": ["integer", "null"]},
                "steps": {"type": ["integer", "null"]},
                "sleep_hours": {"type": ["number", "null"]},
                "missed_meds": {"type": ["integer", "null"]},
                "missed_meals": {"type": ["integer", "null"]},
                "missed_meds_detail": {"type": ["string", "null"]},
                "missed_meals_detail": {"type": ["string", "null"]},
                "falls": {"type": ["integer", "null"]},
            },
            "required": [
                "heart_rate",
                "spo2",
                "steps",
                "sleep_hours",
                "missed_meds",
                "missed_meals",
                "missed_meds_detail",
                "missed_meals_detail",
                "falls",
            ],
            "additionalProperties": False,
        },
    },
    "required": ["reply", "data"],
    "additionalProperties": False,
}


SYSTEM_PROMPT = """
You are SAMPARK, a calm elderly-care voice assistant.

Speak like a gentle human caregiver, not like a form or chatbot.
Use warm, simple language an elderly person can understand.
Keep replies short because they will be spoken aloud: usually 1 to 3 sentences.
Do not over-question the user. Ask only one clear follow-up question when needed.
If the user is happy or feeling well, respond warmly before asking about health.
If the user is worried, first reassure them, then give one practical next step.
If the user asks about medicine, never tell them to skip it. Encourage following the prescribed schedule or checking with a caregiver/doctor.
Your job is to:
1. Respond like a caring assistant.
2. Extract structured health data from the user's message.
3. Ask one useful follow-up question if important health information is missing.

Use these extraction rules:
- missed_meds is 1 if the user missed, forgot, or did not take medicine.
- missed_meds is 0 if the user says they took medicine.
- missed_meds_detail should say which scheduled dose was missed, such as "Morning medicine", "8 PM medicine", or "Bedtime medicine". Use null if unknown.
- missed_meals is 1 if the user skipped or did not eat a meal.
- missed_meals is 0 if the user says they ate or had food.
- missed_meals_detail should say which meal was missed: "Breakfast", "Lunch", "Dinner", or a comma-separated combination. Use null if unknown.
- falls is 1 if the user fell, slipped, or reports a fall.
- falls is 0 if the user says they did not fall.
- Use null for any unknown value.
- Do not assume missed_meds is 0 just because the user says they feel good.
- Do not assume missed_meals is 0 just because the user says they feel good.
- Do not assume falls is 0 unless the user clearly says they did not fall.

Do not diagnose disease. For serious risk, advise rest and caregiver/doctor contact.
For emergencies such as chest pain, breathing difficulty, or "I am dying", urge immediate caregiver/doctor/emergency help.
Return only the structured response requested by the API.
"""


def enabled():
    return os.getenv("SAMPARK_USE_LLM", "").lower() in {"1", "true", "yes", "on"}


def provider_name():
    configured_provider = os.getenv("SAMPARK_LLM_PROVIDER")
    if configured_provider:
        return configured_provider.lower()
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return "openai"


def remove_unknown_values(data):
    return {key: value for key, value in data.items() if value is not None}


def ask_llm(message, collected_data=None):
    if provider_name() == "gemini":
        return ask_gemini(message, collected_data)
    return ask_openai(message, collected_data)


def user_payload(message, collected_data=None):
    return {
        "latest_user_message": message,
        "already_collected_health_data": collected_data or {},
    }


def ask_openai(message, collected_data=None):
    from openai import OpenAI

    client = OpenAI()

    response = client.responses.create(
        model=OPENAI_MODEL_NAME,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload(message, collected_data))},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "sampark_health_response",
                "schema": HEALTH_RESPONSE_SCHEMA,
                "strict": True,
            }
        },
    )

    parsed = json.loads(response.output_text)
    return {
        "reply": parsed["reply"],
        "data": remove_unknown_values(parsed["data"]),
    }


def ask_gemini(message, collected_data=None):
    from google import genai

    client = genai.Client()
    prompt = f"{SYSTEM_PROMPT}\n\nUser/context JSON:\n{json.dumps(user_payload(message, collected_data))}"

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": GEMINI_HEALTH_RESPONSE_SCHEMA,
                },
            )
            break
        except Exception as error:
            if attempt == 1 or "503" not in str(error):
                raise
            time.sleep(2)

    parsed = json.loads(response.text)
    return {
        "reply": parsed["reply"],
        "data": remove_unknown_values(parsed["data"]),
    }
