# SAMPARK - AI-Based Elderly Care System

SAMPARK is an elderly care prototype that combines wearable-style health data, conversational input, machine learning risk prediction, alerts, and a dashboard.

## One-Line Explanation

SAMPARK integrates wearable data and conversational inputs to predict elderly health risks and provide real-time monitoring and alerts.

## System Architecture

```text
Wearable / Watch Data
        |
        v
Wearable Simulator / Google Fit in future
        |
        v
Flask Backend + SQLite Database + ML Model
        ^
        |
Voice Assistant -> Structured Health Data
        |
        v
Dashboard + Alerts + Voice Response
```

## Project Parts

```text
backend/
  Flask API, SQLite database, Random Forest training, risk prediction

voice_assistant/
  Text assistant and microphone voice assistant

dashboard/
  Browser dashboard and optional Streamlit dashboard

wearable_simulator/
  Simulated watch data sender for heart rate, SpO2, steps, and sleep

demo_cases.json
  Sample Low, Medium, and High risk test cases
```

## Features Completed

- Flask backend API
- SQLite health record storage
- Random Forest ML model training
- Rule-based fallback prediction
- Text assistant
- Microphone voice assistant
- Optional LLM-powered human-like assistant mode
- Browser dashboard
- Caregiver alert log
- Gmail emergency email alerts
- Wearable data simulator
- Demo test cases

## Main Data Format

```json
{
  "heart_rate": 80,
  "spo2": 97,
  "steps": 4000,
  "sleep_hours": 4,
  "missed_meds": 1,
  "missed_meals": 0,
  "falls": 0
}
```

If some fields are missing, the backend fills default values. This is useful because the final watch parameters may change.

## How To Run

### 1. Start Backend

```powershell
cd "C:\Users\maham\Documents\Codex\2026-04-29\project-overview-sampark-ai-based-elderly\backend"
python app.py
```

Backend URL:

```text
http://127.0.0.1:5000
```

### 2. Open Dashboard

Open this file in your browser:

```text
C:\Users\maham\Documents\Codex\2026-04-29\project-overview-sampark-ai-based-elderly\dashboard\index.html
```

### 3. Run Text Assistant

Open a second PowerShell:

```powershell
cd "C:\Users\maham\Documents\Codex\2026-04-29\project-overview-sampark-ai-based-elderly\voice_assistant"
python assistant.py
```

Try:

```text
I did not take medicine and slept only 4 hours
```

### 4. Run Voice Assistant

```powershell
cd "C:\Users\maham\Documents\Codex\2026-04-29\project-overview-sampark-ai-based-elderly\voice_assistant"
python voice_mode.py
```

Say:

```text
I slept only 4 hours and I did not eat food
```

Say `stop` to close.

Optional human-like mode with Gemini:

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:SAMPARK_USE_LLM="1"
$env:SAMPARK_LLM_PROVIDER="gemini"
python voice_mode.py
```

Optional human-like mode with OpenAI:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
$env:SAMPARK_USE_LLM="1"
$env:SAMPARK_LLM_PROVIDER="openai"
python voice_mode.py
```

### 5. Run Wearable Simulator

Open another PowerShell:

```powershell
cd "C:\Users\maham\Documents\Codex\2026-04-29\project-overview-sampark-ai-based-elderly\wearable_simulator"
python simulator.py
```

Risky watch data:

```powershell
python simulator.py --mode warning
```

Live watch data:

```powershell
python simulator.py --live
```

## ML Model

The backend uses a Random Forest Classifier trained on synthetic health data.

Training file:

```text
backend/train_model.py
```

Generated files:

```text
backend/synthetic_health_data.csv
backend/sampark_model.pkl
```

To retrain:

```powershell
cd "C:\Users\maham\Documents\Codex\2026-04-29\project-overview-sampark-ai-based-elderly\backend"
python train_model.py
```

## API Endpoints

```text
GET  /
POST /health-data
GET  /health-data
GET  /health-data/latest
GET  /health-data/<id>
GET  /alerts
GET  /alerts/latest
POST /emergency
POST /predict
```

## Demo Flow

1. Start Flask backend.
2. Open browser dashboard.
3. Run voice assistant and speak a health sentence.
4. Show that the dashboard updates with the saved record.
5. Run wearable simulator and show watch data entering the system.
6. Explain that Google Fit can later replace the simulator.

## Google Fit Plan

For the final watch integration:

```text
Mi Band -> Mi Fitness -> Google Fit -> Mobile App / API -> Flask Backend
```

The current simulator represents this future watch data source. The backend is already ready to receive the same JSON format from a real mobile app.

## Viva Explanation

SAMPARK is built as a modular system. The voice assistant collects behavioral data such as missed medicine, meals, sleep, and falls. The wearable side provides physical activity and health parameters such as heart rate, SpO2, steps, and sleep. The Flask backend merges these values, stores them in SQLite, and predicts health risk using a Random Forest model. The dashboard displays real-time status and alerts for caregivers.
