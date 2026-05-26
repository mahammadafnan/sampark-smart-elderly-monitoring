from flask import Flask, jsonify, request
from flask_cors import CORS

from database import (
    create_alert,
    create_health_record,
    get_latest_alert,
    get_health_record,
    get_latest_health_record,
    init_db,
    list_alerts,
    list_health_records,
    update_alert_notification,
)
from email_notifier import gmail_status, send_caretaker_email
from assistant_web import handle_assistant_message
from risk_engine import predict_risk


app = Flask(__name__)
CORS(app)


@app.before_request
def setup_database():
    init_db()


@app.get("/")
def home():
    return jsonify(
        {
            "app": "SAMPARK Backend",
            "status": "running",
            "endpoints": {
                "create_health_record": "POST /health-data",
                "list_health_records": "GET /health-data",
                "latest_health_record": "GET /health-data/latest",
                "list_alerts": "GET /alerts",
                "latest_alert": "GET /alerts/latest",
                "emergency_alert": "POST /emergency",
                "email_status": "GET /email-status",
                "assistant_message": "POST /assistant-message",
                "predict_without_saving": "POST /predict",
            },
        }
    )


@app.post("/health-data")
def save_health_data():
    payload = request.get_json(silent=True) or {}
    record = create_health_record(payload)
    return jsonify(record), 201


@app.get("/health-data")
def health_records():
    return jsonify({"records": list_health_records()})


@app.get("/health-data/latest")
def latest_health_record():
    record = get_latest_health_record()
    if record is None:
        return jsonify({"error": "No health records found"}), 404
    return jsonify(record)


@app.get("/health-data/<int:record_id>")
def health_record(record_id):
    record = get_health_record(record_id)
    if record is None:
        return jsonify({"error": "Health record not found"}), 404
    return jsonify(record)


@app.get("/alerts")
def alerts():
    return jsonify({"alerts": list_alerts()})


@app.get("/alerts/latest")
def latest_alert():
    alert = get_latest_alert()
    if alert is None:
        return jsonify({"error": "No alerts found"}), 404
    return jsonify(alert)


@app.get("/email-status")
def email_status():
    return jsonify(gmail_status())


@app.post("/emergency")
def emergency():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "Emergency reported by SAMPARK voice assistant.")
    source = payload.get("source", "voice_assistant")

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

    return jsonify({"alert": alert, "email": email_result}), 201


@app.post("/assistant-message")
def assistant_message():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "").strip()
    session_id = payload.get("session_id", "web-default")
    source = payload.get("source", "web_voice")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    result = handle_assistant_message(message, session_id=session_id, source=source)
    return jsonify(result)


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    result = predict_risk(payload)
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
