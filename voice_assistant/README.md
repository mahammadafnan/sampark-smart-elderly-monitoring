# SAMPARK Voice Assistant

This module contains the voice assistant data flow.

It supports:

- typed text mode
- microphone voice mode
- spoken replies
- basic conversation flow and follow-up questions

## What It Does

Example user sentence:

```text
I did not take medicine and slept only 4 hours
```

The assistant extracts:

```json
{
  "sleep_hours": 4,
  "missed_meds": 1
}
```

Then it sends that data to:

```text
POST http://127.0.0.1:5000/health-data
```

The backend stores it and returns the ML risk prediction.

## Run Text Mode

First start the backend:

```powershell
cd ..\backend
python app.py
```

In another PowerShell window:

```powershell
cd voice_assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python assistant.py
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run Voice Mode

Keep the backend running. Then run:

```powershell
python pc_assistant.py
```

The assistant will listen through your microphone and reply using system speech.

Say one of these to stop:

```text
exit
quit
stop
```

In voice mode, you can also type `stop` in the PowerShell window and press Enter.

For typed fallback:

```powershell
python pc_assistant.py --mode text
```

## If PyAudio Fails

On Windows, microphone support may fail while installing `PyAudio`.

If that happens, continue using text mode:

```powershell
python assistant.py
```

Text mode still proves the full AI data flow:

```text
conversation input -> structured data -> backend -> risk prediction -> response
```

## Example Inputs

```text
hello
I am not feeling well
I did not take medicine and slept only 4 hours
My heart rate is 115 and oxygen level is 92
I skipped food today and fell down
I walked 3000 steps and slept 7 hours
I took my medicine and had food
```

## Conversation Ability

This assistant is conversational at a prototype level. It can greet the user, ask follow-up questions, remember collected details during the session, and save structured health data to the backend.

For fully human-like conversation, the next upgrade is to connect an LLM such as ChatGPT or Gemini. The current version avoids API keys and works as a student-friendly offline prototype.

The assistant also has local emergency handling for phrases such as chest pain, breathing problems, or requests to call a caretaker. This works even if the LLM is temporarily unavailable.

## Optional Human-Like LLM Mode

The assistant can use Gemini or OpenAI for more natural conversation and structured data extraction.

Install dependencies:

```powershell
pip install -r requirements.txt
```

### Gemini

Set your Gemini API key for the current PowerShell window:

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:SAMPARK_USE_LLM="1"
$env:SAMPARK_LLM_PROVIDER="gemini"
```

Run text mode:

```powershell
python assistant.py
```

Run voice mode:

```powershell
python voice_mode.py
```

Optional Gemini model override:

```powershell
$env:SAMPARK_GEMINI_MODEL="gemini-2.5-flash-lite"
```

### OpenAI

Set your OpenAI API key for the current PowerShell window:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
$env:SAMPARK_USE_LLM="1"
$env:SAMPARK_LLM_PROVIDER="openai"
```

Run text mode:

```powershell
python assistant.py
```

Run voice mode:

```powershell
python voice_mode.py
```

Optional model override:

```powershell
$env:SAMPARK_OPENAI_MODEL="gpt-4o-mini"
```

If the API key is missing or the LLM call fails, the assistant automatically falls back to the local conversation logic.
