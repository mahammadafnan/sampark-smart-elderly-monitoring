import argparse
import json
import queue
import threading

import pyttsx3
import requests
import speech_recognition as sr

from assistant import ConversationSession, handle_user_message, is_stop_command
from llm_layer import enabled as llm_enabled, provider_name


def create_speaker():
    engine = pyttsx3.init()
    engine.setProperty("rate", 155)
    engine.setProperty("volume", 1.0)
    return engine


def speak(engine, text):
    print(f"\nSAMPARK: {text}")
    engine.say(text)
    engine.runAndWait()


def print_header(mode):
    print()
    print("=" * 58)
    print("SAMPARK PC Voice Assistant")
    print("=" * 58)
    print(f"Mode: {mode}")
    if llm_enabled():
        print(f"LLM: enabled")
        print(f"Provider: {provider_name()}")
    else:
        print("LLM: local fallback mode")
    print("Say or type 'stop' to exit.")
    print("=" * 58)
    print()


def start_keyboard_listener():
    commands = queue.Queue()

    def read_commands():
        while True:
            try:
                command = input().strip()
            except EOFError:
                break
            commands.put(command)

    thread = threading.Thread(target=read_commands, daemon=True)
    thread.start()
    return commands


def typed_stop_requested(commands):
    while not commands.empty():
        command = commands.get()
        if is_stop_command(command):
            return True
        if command:
            print("Typed input in voice mode is only used for stop. Say health details aloud.")
    return False


def listen_once(recognizer, microphone):
    with microphone as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.6)
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=12)

    return recognizer.recognize_google(audio)


def short_status(result):
    if result.get("emergency_alert"):
        email = result["emergency_alert"].get("email", {})
        if email.get("sent"):
            return "Emergency email sent to caretaker."
        return "Emergency alert created. Email was simulated or not configured."

    prediction = result.get("backend_response")
    if prediction:
        reasons = prediction.get("reasons", [])
        reason_text = f" Reasons: {', '.join(reasons)}." if reasons else ""
        return f"Saved record. Risk: {prediction.get('risk')}.{reason_text}"

    extracted = result.get("extracted_data", {})
    if extracted:
        return f"Collected data: {json.dumps(extracted)}"

    return "No health record saved for this message."


def handle_message(message, session, speaker):
    print(f"\nUser: {message}")

    if is_stop_command(message):
        speak(speaker, "Take care. Goodbye.")
        return False

    try:
        result = handle_user_message(message, session)
    except requests.exceptions.ConnectionError:
        speak(speaker, "Backend is not running. Please start Flask first.")
        return True
    except requests.exceptions.RequestException as error:
        speak(speaker, f"Could not contact backend. {error}")
        return True

    speak(speaker, result["reply"])
    print(f"Status: {short_status(result)}")
    return True


def run_voice_mode():
    print_header("microphone")
    speaker = create_speaker()
    recognizer = sr.Recognizer()
    session = ConversationSession()
    typed_commands = start_keyboard_listener()

    try:
        microphone = sr.Microphone()
    except OSError:
        print("Microphone was not found. Run typed mode with: python pc_assistant.py --mode text")
        return

    speak(speaker, "SAMPARK is ready.")

    while True:
        if typed_stop_requested(typed_commands):
            speak(speaker, "Take care. Goodbye.")
            break

        try:
            message = listen_once(recognizer, microphone)
        except sr.WaitTimeoutError:
            if typed_stop_requested(typed_commands):
                speak(speaker, "Take care. Goodbye.")
                break
            print("No speech detected. Try again.")
            continue
        except sr.UnknownValueError:
            speak(speaker, "Sorry, I could not understand that. Please repeat.")
            continue
        except sr.RequestError:
            speak(speaker, "Speech recognition service is unavailable. Please check internet.")
            continue

        if typed_stop_requested(typed_commands) or not handle_message(message, session, speaker):
            break


def run_text_mode():
    print_header("typed")
    speaker = create_speaker()
    session = ConversationSession()
    speak(speaker, "SAMPARK typed assistant is ready.")

    while True:
        message = input("User: ").strip()
        if not message:
            continue

        if not handle_message(message, session, speaker):
            break


def parse_args():
    parser = argparse.ArgumentParser(description="Run the polished SAMPARK PC assistant.")
    parser.add_argument(
        "--mode",
        choices=["voice", "text"],
        default="voice",
        help="Use microphone voice mode or typed mode.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.mode == "text":
        run_text_mode()
    else:
        run_voice_mode()


if __name__ == "__main__":
    main()
