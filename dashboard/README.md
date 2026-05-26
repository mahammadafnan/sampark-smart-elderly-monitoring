# SAMPARK Dashboard

This folder has two dashboard options:

- `index.html`: dependency-free browser dashboard
- `app.py`: Streamlit dashboard

## Recommended: Browser Dashboard

Start the backend first:

```powershell
cd ..\backend
python app.py
```

Then open this file in your browser:

```text
dashboard/index.html
```

This avoids Streamlit/pyarrow problems on restricted Windows systems.

The browser dashboard includes:

- patient profile header
- dedicated Patient Profile tab
- large Low / Medium / High risk panel
- health metric cards
- clickable missed meds and missed meals cards
- separate medicine and meal history tabs with exact date/time
- caregiver alert timeline
- saved health records on a separate tab
- auto-refresh every 5 seconds

Edit the `patientProfile` object in `index.html` to change the elder's name, age, gender, height, weight, conditions, caretaker, and emergency contact.

## Optional: Streamlit Dashboard

Start the backend first:

```powershell
cd ..\backend
python app.py
```

Then open a second PowerShell window:

```powershell
cd dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

The dashboard reads:

```text
GET http://127.0.0.1:5000/health-data/latest
GET http://127.0.0.1:5000/health-data
GET http://127.0.0.1:5000/alerts
```
