import sqlite3
from datetime import datetime
from pathlib import Path

from risk_engine import normalize_health_data, predict_risk


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sampark.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                heart_rate INTEGER NOT NULL,
                spo2 INTEGER NOT NULL,
                steps INTEGER NOT NULL,
                sleep_hours REAL NOT NULL,
                missed_meds INTEGER NOT NULL,
                missed_meals INTEGER NOT NULL,
                missed_meds_detail TEXT,
                missed_meals_detail TEXT,
                falls INTEGER NOT NULL,
                risk TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                reasons TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                health_record_id INTEGER,
                severity TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0,
                notification_status TEXT NOT NULL DEFAULT 'not_sent',
                FOREIGN KEY (health_record_id) REFERENCES health_records (id)
            )
            """
        )
        ensure_health_record_column(connection, "missed_meds_detail", "TEXT")
        ensure_health_record_column(connection, "missed_meals_detail", "TEXT")
        ensure_alert_column(connection, "notification_status", "TEXT NOT NULL DEFAULT 'not_sent'")


def ensure_health_record_column(connection, column_name, definition):
    columns = connection.execute("PRAGMA table_info(health_records)").fetchall()
    existing_columns = {column["name"] for column in columns}
    if column_name not in existing_columns:
        connection.execute(f"ALTER TABLE health_records ADD COLUMN {column_name} {definition}")


def ensure_alert_column(connection, column_name, definition):
    columns = connection.execute("PRAGMA table_info(alerts)").fetchall()
    existing_columns = {column["name"] for column in columns}
    if column_name not in existing_columns:
        connection.execute(f"ALTER TABLE alerts ADD COLUMN {column_name} {definition}")


def row_to_dict(row):
    data = dict(row)
    data["reasons"] = [reason for reason in data["reasons"].split("|") if reason]
    data.setdefault("missed_meds_detail", "")
    data.setdefault("missed_meals_detail", "")
    return data


def clean_detail(value):
    if value is None:
        return ""
    return str(value).strip()[:80]


def payload_with_latest_sleep(payload):
    data = dict(payload)
    if data.get("sleep_hours") not in (None, ""):
        return data

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT sleep_hours
            FROM health_records
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    if row:
        data["sleep_hours"] = row["sleep_hours"]
    return data


def create_health_record(payload):
    payload = payload_with_latest_sleep(payload)
    health_data = normalize_health_data(payload)
    prediction = predict_risk(health_data)
    created_at = datetime.now().isoformat(timespec="seconds")
    missed_meds_detail = clean_detail(payload.get("missed_meds_detail"))
    missed_meals_detail = clean_detail(payload.get("missed_meals_detail"))

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO health_records (
                heart_rate,
                spo2,
                steps,
                sleep_hours,
                missed_meds,
                missed_meals,
                missed_meds_detail,
                missed_meals_detail,
                falls,
                risk,
                risk_score,
                reasons,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                health_data["heart_rate"],
                health_data["spo2"],
                health_data["steps"],
                health_data["sleep_hours"],
                health_data["missed_meds"],
                health_data["missed_meals"],
                missed_meds_detail,
                missed_meals_detail,
                health_data["falls"],
                prediction["risk"],
                prediction["risk_score"],
                "|".join(prediction["reasons"]),
                created_at,
            ),
        )

    record = get_health_record(cursor.lastrowid)
    create_alerts_for_record(record)
    return record


def create_alert(record_id, severity, alert_type, message):
    created_at = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO alerts (
                health_record_id,
                severity,
                alert_type,
                message,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (record_id, severity, alert_type, message, created_at),
        )

    return get_alert(cursor.lastrowid)


def update_alert_notification(alert_id, status):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE alerts
            SET notification_status = ?
            WHERE id = ?
            """,
            (status, alert_id),
        )

    return get_alert(alert_id)


def send_high_risk_email(record, alert):
    from email_notifier import send_caretaker_email

    reasons = ", ".join(record["reasons"]) if record["reasons"] else "High risk prediction"
    medicine_detail = record.get("missed_meds_detail") or "Not specified"
    meal_detail = record.get("missed_meals_detail") or "Not specified"

    email_result = send_caretaker_email(
        "SAMPARK High Risk Health Alert",
        (
            "SAMPARK detected a high-risk health record.\n\n"
            f"Record ID: {record['id']}\n"
            f"Time: {record['created_at']}\n"
            f"Risk Score: {record['risk_score']}\n"
            f"Reasons: {reasons}\n\n"
            f"Heart Rate: {record['heart_rate']} bpm\n"
            f"SpO2: {record['spo2']}%\n"
            f"Steps: {record['steps']}\n"
            f"Sleep: {record['sleep_hours']} hours\n"
            f"Missed Medicine: {record['missed_meds']} ({medicine_detail})\n"
            f"Missed Meal: {record['missed_meals']} ({meal_detail})\n\n"
            "Please check the dashboard and contact the elderly person if needed."
        ),
    )
    status = "sent" if email_result["sent"] else "simulated"
    return update_alert_notification(alert["id"], status)


def create_alerts_for_record(record):
    if record["risk"] == "High":
        alert = create_alert(
            record["id"],
            "High",
            "High Risk",
            "High health risk detected. Caregiver attention is recommended.",
        )
        send_high_risk_email(record, alert)

    if record["falls"] > 0:
        create_alert(
            record["id"],
            "High",
            "Fall",
            "Fall reported. Check the elderly person immediately.",
        )

    if record["spo2"] < 94:
        create_alert(
            record["id"],
            "High",
            "Low SpO2",
            "Low oxygen level detected.",
        )

    if record["heart_rate"] < 55 or record["heart_rate"] > 110:
        create_alert(
            record["id"],
            "Medium",
            "Abnormal Heart Rate",
            "Heart rate is outside the normal monitoring range.",
        )

    if record["missed_meds"] > 0:
        create_alert(
            record["id"],
            "Medium",
            "Missed Medicine",
            "Medicine was missed. Reminder or caregiver follow-up is needed.",
        )


def list_health_records(limit=50):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM health_records
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def alert_row_to_dict(row):
    data = dict(row)
    data["acknowledged"] = bool(data["acknowledged"])
    return data


def list_alerts(limit=50):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM alerts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [alert_row_to_dict(row) for row in rows]


def get_latest_alert():
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM alerts
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return alert_row_to_dict(row) if row else None


def get_alert(alert_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM alerts
            WHERE id = ?
            """,
            (alert_id,),
        ).fetchone()

    return alert_row_to_dict(row) if row else None


def get_latest_health_record():
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM health_records
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return row_to_dict(row) if row else None


def get_health_record(record_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM health_records
            WHERE id = ?
            """,
            (record_id,),
        ).fetchone()

    return row_to_dict(row) if row else None
