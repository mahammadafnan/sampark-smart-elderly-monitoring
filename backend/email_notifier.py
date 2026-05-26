import os
import smtplib
from email.message import EmailMessage


def gmail_configured():
    required_values = [
        os.getenv("SAMPARK_GMAIL_ADDRESS"),
        os.getenv("SAMPARK_GMAIL_APP_PASSWORD"),
        os.getenv("SAMPARK_CARETAKER_EMAIL"),
    ]
    return all(required_values)


def gmail_status():
    return {
        "gmail_address_set": bool(os.getenv("SAMPARK_GMAIL_ADDRESS")),
        "app_password_set": bool(os.getenv("SAMPARK_GMAIL_APP_PASSWORD")),
        "caretaker_email_set": bool(os.getenv("SAMPARK_CARETAKER_EMAIL")),
        "configured": gmail_configured(),
    }


def send_caretaker_email(subject, body):
    sender = os.getenv("SAMPARK_GMAIL_ADDRESS")
    app_password = os.getenv("SAMPARK_GMAIL_APP_PASSWORD")
    recipient = os.getenv("SAMPARK_CARETAKER_EMAIL")

    if not gmail_configured():
        return {
            "sent": False,
            "mode": "demo",
            "message": "Gmail credentials are not configured. Email alert simulated.",
        }

    email = EmailMessage()
    email["From"] = sender
    email["To"] = recipient
    email["Subject"] = subject
    email.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(email)

    return {
        "sent": True,
        "mode": "gmail",
        "message": f"Email alert sent to {recipient}.",
    }
