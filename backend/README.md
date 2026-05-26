# SAMPARK Backend

This is the first backend for the SAMPARK elderly care system.

It can:

- receive health data from a watch app or voice assistant
- store health records in SQLite
- predict risk with a Random Forest model
- create caregiver alerts for high-risk events
- send Gmail emergency alerts when configured
- return saved records for a dashboard

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python train_model.py
python app.py
```

The server runs at:

```text
http://127.0.0.1:5000
```

The backend also listens on your local network for phone testing:

```text
http://YOUR_LAPTOP_IP:5000
```

## Train ML Model

Run this once before starting the backend:

```bash
python train_model.py
```

This creates:

```text
synthetic_health_data.csv
sampark_model.pkl
```

The backend will use `sampark_model.pkl` for predictions. If the model file is missing, it falls back to rule-based prediction.

## Test Prediction

```bash
curl -X POST http://127.0.0.1:5000/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"heart_rate\":80,\"spo2\":97,\"steps\":4000,\"sleep_hours\":4,\"missed_meds\":1,\"missed_meals\":0,\"falls\":0}"
```

## Save Health Data

```bash
curl -X POST http://127.0.0.1:5000/health-data ^
  -H "Content-Type: application/json" ^
  -d "{\"heart_rate\":80,\"spo2\":97,\"steps\":4000,\"sleep_hours\":4,\"missed_meds\":1,\"missed_meals\":0,\"falls\":0}"
```

## View Latest Record

```bash
curl http://127.0.0.1:5000/health-data/latest
```

## View Alerts

```bash
curl http://127.0.0.1:5000/alerts
```

```bash
curl http://127.0.0.1:5000/alerts/latest
```

## Gmail Emergency Alerts

Use a Gmail App Password, not your normal Gmail password.

Set these in the PowerShell window where the backend runs:

```powershell
$env:SAMPARK_GMAIL_ADDRESS="your_sender@gmail.com"
$env:SAMPARK_GMAIL_APP_PASSWORD="your_16_character_app_password"
$env:SAMPARK_CARETAKER_EMAIL="caretaker@example.com"
python app.py
```

Test emergency alert:

```powershell
curl -Method POST http://127.0.0.1:5000/emergency `
  -ContentType "application/json" `
  -Body '{"message":"I have chest pain","source":"test"}'
```

If Gmail credentials are not configured, the backend creates an alert and returns demo/simulated email mode.

## Simulated Watch Data

Until Google Fit is connected, use:

```powershell
cd ..\wearable_simulator
python simulator.py
```

This sends watch-like heart rate, SpO2, steps, and sleep data into the backend.
