# SAMPARK Phone Voice Assistant

This is a browser-based phone voice assistant.

It can:

- listen using the phone microphone
- speak replies using browser speech synthesis
- send conversation text to the Flask backend
- use the same Gemini/backend assistant logic as `pc_assistant.py`
- send emergency alerts through the backend

The UI is intentionally simple:

- Start Conversation
- Stop
- Emergency Alert
- Backend URL settings

## Run On PC First

Start backend:

```powershell
cd ..\backend
$env:GEMINI_API_KEY="your_gemini_key"
$env:SAMPARK_USE_LLM="1"
$env:SAMPARK_LLM_PROVIDER="gemini"
python app.py
```

Open:

```text
phone_voice/index.html
```

Use backend URL:

```text
http://127.0.0.1:5000
```

## Run On Phone

1. Connect phone and laptop to the same Wi-Fi.
2. Start backend on laptop.
3. Find laptop IP:

```powershell
ipconfig
```

4. Serve the project folder from laptop:

```powershell
cd ..
python -m http.server 9000
```

5. On phone Chrome, open:

```text
http://192.168.1.5:9000/phone_voice/
```

6. Set backend URL like:

```text
http://192.168.1.5:5000
```

Replace `192.168.1.5` with your laptop IPv4 address.

## Possible Phone Issues

- Chrome on Android works best.
- iPhone/Safari speech recognition may not work reliably.
- Microphone access may require HTTPS depending on browser/security settings.
- Windows Firewall may block phone access to Flask.
- Phone cannot use `127.0.0.1` for laptop backend.
- Gemini/API keys stay on backend, not inside browser JavaScript.
