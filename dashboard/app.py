import pandas as pd
import requests
import streamlit as st


BACKEND_URL = "http://127.0.0.1:5000"


RISK_COLORS = {
    "Low": "#17803d",
    "Medium": "#b7791f",
    "High": "#c53030",
}


def fetch_json(path):
    response = requests.get(f"{BACKEND_URL}{path}", timeout=8)
    response.raise_for_status()
    return response.json()


def risk_badge(risk):
    color = RISK_COLORS.get(risk, "#4a5568")
    st.markdown(
        f"""
        <div class="risk-badge" style="border-color:{color}; color:{color};">
            {risk} Risk
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_metric_grid(record):
    first_row = st.columns(4)
    first_row[0].metric("Heart Rate", f"{record['heart_rate']} bpm")
    first_row[1].metric("SpO2", f"{record['spo2']}%")
    first_row[2].metric("Steps", f"{record['steps']}")
    first_row[3].metric("Sleep", f"{record['sleep_hours']} hrs")

    second_row = st.columns(3)
    second_row[0].metric("Missed Meds", record["missed_meds"])
    second_row[1].metric("Missed Meals", record["missed_meals"])
    second_row[2].metric("Falls", record["falls"])


def show_alerts(record):
    reasons = record.get("reasons", [])
    risk = record.get("risk", "Low")

    if risk == "High":
        st.error("High risk detected. Caregiver attention is recommended.")
    elif risk == "Medium":
        st.warning("Medium risk detected. Monitor the patient closely.")
    else:
        st.success("Current health status looks stable.")

    if reasons:
        st.write("Alert reasons:")
        for reason in reasons:
            st.write(f"- {reason}")


def records_to_dataframe(records):
    df = pd.DataFrame(records)
    if df.empty:
        return df

    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at")
    df["reasons"] = df["reasons"].apply(lambda items: ", ".join(items) if items else "")
    return df


def add_styles():
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 2rem;
            max-width: 1160px;
        }
        .risk-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 44px;
            padding: 0 18px;
            border: 2px solid;
            border-radius: 8px;
            font-size: 22px;
            font-weight: 700;
        }
        div[data-testid="stMetric"] {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px 16px;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="SAMPARK Dashboard", page_icon="S", layout="wide")
    add_styles()

    st.title("SAMPARK Elderly Care Dashboard")
    st.caption("Real-time health monitoring, risk prediction, and alerts")

    with st.sidebar:
        st.header("Controls")
        st.write("Backend")
        st.code(BACKEND_URL)
        refresh = st.button("Refresh Data", use_container_width=True)
        if refresh:
            st.rerun()

    try:
        latest = fetch_json("/health-data/latest")
        records_response = fetch_json("/health-data")
    except requests.exceptions.ConnectionError:
        st.error("Backend is not running. Start Flask first with `python app.py`.")
        return
    except requests.exceptions.HTTPError:
        st.info("No health records found yet. Use the voice assistant to add data.")
        return
    except requests.exceptions.RequestException as error:
        st.error(f"Could not load backend data: {error}")
        return

    records = records_response.get("records", [])
    df = records_to_dataframe(records)

    top_left, top_right = st.columns([2, 1])
    with top_left:
        st.subheader("Latest Health Status")
        show_metric_grid(latest)
    with top_right:
        st.subheader("Risk")
        risk_badge(latest.get("risk", "Low"))
        st.write(f"Updated: {latest['created_at']}")
        show_alerts(latest)

    st.divider()

    st.subheader("Health Trends")
    if df.empty:
        st.info("No trend data available yet.")
    else:
        chart_df = df.set_index("created_at")
        st.line_chart(chart_df[["heart_rate", "spo2", "sleep_hours"]])
        st.bar_chart(chart_df[["steps"]])

    st.subheader("Saved Health Records")
    if df.empty:
        st.info("No saved records yet.")
    else:
        display_columns = [
            "id",
            "created_at",
            "risk",
            "risk_score",
            "heart_rate",
            "spo2",
            "steps",
            "sleep_hours",
            "missed_meds",
            "missed_meals",
            "falls",
            "reasons",
        ]
        st.dataframe(df.sort_values("created_at", ascending=False)[display_columns], use_container_width=True)


if __name__ == "__main__":
    main()
