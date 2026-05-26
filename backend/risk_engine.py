import pickle
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "sampark_model.pkl"
FEATURES = [
    "heart_rate",
    "spo2",
    "steps",
    "sleep_hours",
    "missed_meds",
    "missed_meals",
    "falls",
]

DEFAULT_HEALTH_DATA = {
    "heart_rate": 80,
    "spo2": 97,
    "steps": 3000,
    "sleep_hours": 7,
    "missed_meds": 0,
    "missed_meals": 0,
    "falls": 0,
}

RISK_LABELS = {
    0: "Low",
    1: "Medium",
    2: "High",
}


def to_number(value, default):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_health_data(payload):
    return {
        "heart_rate": int(to_number(payload.get("heart_rate"), DEFAULT_HEALTH_DATA["heart_rate"])),
        "spo2": int(to_number(payload.get("spo2"), DEFAULT_HEALTH_DATA["spo2"])),
        "steps": int(to_number(payload.get("steps"), DEFAULT_HEALTH_DATA["steps"])),
        "sleep_hours": to_number(payload.get("sleep_hours"), DEFAULT_HEALTH_DATA["sleep_hours"]),
        "missed_meds": int(to_number(payload.get("missed_meds"), DEFAULT_HEALTH_DATA["missed_meds"])),
        "missed_meals": int(to_number(payload.get("missed_meals"), DEFAULT_HEALTH_DATA["missed_meals"])),
        "falls": int(to_number(payload.get("falls"), DEFAULT_HEALTH_DATA["falls"])),
    }


def calculate_rule_score(data):
    score = 0
    reasons = []

    if data["spo2"] < 94:
        score += 3
        reasons.append("Low SpO2")

    if data["heart_rate"] < 55 or data["heart_rate"] > 110:
        score += 2
        reasons.append("Abnormal heart rate")

    if data["sleep_hours"] < 5:
        score += 2
        reasons.append("Poor sleep")

    if data["steps"] < 1000:
        score += 1
        reasons.append("Low activity")

    if data["missed_meds"] > 0:
        score += 2
        reasons.append("Missed medicine")

    if data["missed_meals"] > 0:
        score += 1
        reasons.append("Missed meal")

    if data["falls"] > 0:
        score += 3
        reasons.append("Fall reported")

    return score, reasons


def score_to_risk(score):
    if score >= 4:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"


def load_model():
    if not MODEL_PATH.exists():
        return None

    with MODEL_PATH.open("rb") as model_file:
        return pickle.load(model_file)


def model_input(data):
    return [[data[feature] for feature in FEATURES]]


def predict_risk_with_rules(payload):
    data = normalize_health_data(payload)
    score, reasons = calculate_rule_score(data)

    return {
        "risk": score_to_risk(score),
        "risk_score": score,
        "reasons": reasons,
        "input": data,
        "prediction_source": "rules",
    }


def predict_risk(payload):
    data = normalize_health_data(payload)
    score, reasons = calculate_rule_score(data)
    model = load_model()

    if model is None:
        return predict_risk_with_rules(data)

    prediction = int(model.predict(model_input(data))[0])
    risk = RISK_LABELS.get(prediction, "Low")

    return {
        "risk": risk,
        "risk_score": score,
        "reasons": reasons,
        "input": data,
        "prediction_source": "random_forest",
    }
