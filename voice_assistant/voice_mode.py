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
    engine.setProperty("rate", 160)
    engine.setProperty("volume", 1.0)
    return engine


def speak(engine, text):
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()


def listen(recognizer, microphone):
    with microphone as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.6)
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)

    return recognizer.recognize_google(audio)


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
            print("Typed commands are only used for stopping voice mode. Say health details aloud.")
    return False


def print_debug_details(result):
    if result.get("emergency"):
        print("Emergency alert: yes")
    if result.get("emergency_alert") is not None:
        print("Emergency notification:")
        print(json.dumps(result["emergency_alert"], indent=2))
    print("Structured data:")
    print(json.dumps(result["extracted_data"], indent=2))
    if result["backend_response"] is not None:
        print("Backend prediction:")
        print(json.dumps(result["backend_response"], indent=2))
    print()


def main():
    recognizer = sr.Recognizer()
    speaker = create_speaker()
    session = ConversationSession()
    typed_commands = start_keyboard_listener()

    try:
        microphone = sr.Microphone()
    except OSError:
        print("Microphone was not found. Please check your input device.")
        return

    print("SAMPARK Voice Assistant - Voice Mode")
    print("Say 'exit', 'quit', or 'stop' to close.")
    print("You can also type 'stop' here and press Enter.")
    if llm_enabled():
        print(f"LLM mode is enabled. Provider: {provider_name()}")
    speak(speaker, "SAMPARK voice assistant is ready.")

    while True:
        if typed_stop_requested(typed_commands):
            speak(speaker, "Take care. Goodbye.")
            break

        try:
            message = listen(recognizer, microphone)
        except sr.WaitTimeoutError:
            if typed_stop_requested(typed_commands):
                speak(speaker, "Take care. Goodbye.")
                break
            print("No speech detected. Please try again.")
            continue
        except sr.UnknownValueError:
            speak(speaker, "Sorry, I could not understand that. Please repeat.")
            continue
        except sr.RequestError:
            speak(speaker, "Speech recognition service is unavailable. Please check your internet connection.")
            continue

        print(f"User: {message}")

        if is_stop_command(message) or typed_stop_requested(typed_commands):
            speak(speaker, "Take care. Goodbye.")
            break

        try:
            result = handle_user_message(message, session)
        except requests.exceptions.ConnectionError:
            speak(speaker, "Backend is not running. Please start Flask first.")
            continue
        except requests.exceptions.RequestException as error:
            speak(speaker, f"Could not send data to backend. {error}")
            continue

        speak(speaker, result["reply"])
        print_debug_details(result)


if __name__ == "__main__":
    main()
