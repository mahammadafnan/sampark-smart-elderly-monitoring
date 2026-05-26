import csv
import pickle
import random
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from risk_engine import FEATURES, MODEL_PATH, calculate_rule_score


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "synthetic_health_data.csv"


def risk_label_from_score(score):
    if score >= 4:
        return 2
    if score >= 2:
        return 1
    return 0


def create_sample():
    heart_rate = random.randint(45, 130)
    spo2 = random.randint(88, 100)
    steps = random.randint(0, 9000)
    sleep_hours = round(random.uniform(2.5, 9.5), 1)
    missed_meds = random.choices([0, 1, 2], weights=[75, 20, 5])[0]
    missed_meals = random.choices([0, 1, 2], weights=[80, 17, 3])[0]
    falls = random.choices([0, 1], weights=[94, 6])[0]

    data = {
        "heart_rate": heart_rate,
        "spo2": spo2,
        "steps": steps,
        "sleep_hours": sleep_hours,
        "missed_meds": missed_meds,
        "missed_meals": missed_meals,
        "falls": falls,
    }
    score, _ = calculate_rule_score(data)
    data["risk"] = risk_label_from_score(score)
    return data


def generate_dataset(total_rows=2000):
    random.seed(42)
    rows = [create_sample() for _ in range(total_rows)]

    with DATASET_PATH.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=[*FEATURES, "risk"])
        writer.writeheader()
        writer.writerows(rows)

    return rows


def train_model(rows):
    x = [[row[feature] for feature in FEATURES] for row in rows]
    y = [row["risk"] for row in rows]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=120,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)

    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(model, model_file)

    print(f"Dataset saved to: {DATASET_PATH}")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Accuracy: {accuracy:.2%}")
    print(classification_report(y_test, predictions, target_names=["Low", "Medium", "High"]))


if __name__ == "__main__":
    dataset = generate_dataset()
    train_model(dataset)
