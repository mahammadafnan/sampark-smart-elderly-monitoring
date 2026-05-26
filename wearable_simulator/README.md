# SAMPARK Wearable Simulator

This simulates watch data before real Google Fit integration.

It sends data like:

```json
{
  "heart_rate": 82,
  "spo2": 98,
  "steps": 4200,
  "sleep_hours": 7.2
}
```

to:

```text
POST http://127.0.0.1:5000/health-data
```

## Run

Start backend first:

```powershell
cd ..\backend
python app.py
```

Then in another PowerShell:

```powershell
cd wearable_simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python simulator.py
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Examples

Send one random watch record:

```powershell
python simulator.py
```

Send one warning/risky watch record:

```powershell
python simulator.py --mode warning
```

Send live data every 10 seconds:

```powershell
python simulator.py --live
```

Send warning data every 5 seconds:

```powershell
python simulator.py --mode warning --live --interval 5
```
