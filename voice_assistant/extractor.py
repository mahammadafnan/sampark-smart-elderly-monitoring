import re


NEGATIVE_MEDICINE_PHRASES = [
    "did not take medicine",
    "didn't take medicine",
    "missed medicine",
    "missed my medicine",
    "forgot medicine",
    "forgot my medicine",
    "did not take meds",
    "didn't take meds",
    "missed meds",
    "missed my meds",
]

POSITIVE_MEDICINE_PHRASES = [
    "took medicine",
    "taken medicine",
    "took my medicine",
    "i took medicine",
    "i took my medicine",
    "had medicine",
]

NEGATIVE_MEAL_PHRASES = [
    "did not eat",
    "didn't eat",
    "did not eat food",
    "didn't eat food",
    "miss breakfast",
    "missed breakfast",
    "miss the breakfast",
    "miss lunch",
    "missed lunch",
    "miss dinner",
    "missed dinner",
    "skipped breakfast",
    "skipped lunch",
    "skipped dinner",
    "missed meal",
    "missed my meal",
    "skipped food",
    "skipped meal",
    "not eaten",
]

POSITIVE_MEAL_PHRASES = [
    "i ate",
    "had food",
    "ate food",
    "had breakfast",
    "had lunch",
    "had dinner",
]

FALL_PHRASES = [
    "i fell",
    "fallen",
    "fall down",
    "fell down",
    "slipped",
]

NO_FALL_PHRASES = [
    "no fall",
    "did not fall",
    "didn't fall",
    "not fallen",
]


MEAL_DETAILS = {
    "breakfast": ["breakfast", "morning meal"],
    "lunch": ["lunch", "afternoon meal"],
    "dinner": ["dinner", "supper", "night meal"],
}

MEDICINE_TIME_PATTERNS = [
    r"(\d{1,2})(:\d{2})?\s*(am|pm)\s*(medicine|meds|tablet|dose)",
    r"(medicine|meds|tablet|dose)\s*(at|for|of)?\s*(\d{1,2})(:\d{2})?\s*(am|pm)",
    r"(morning|afternoon|evening|night|bedtime)\s*(medicine|meds|tablet|dose)",
    r"(medicine|meds|tablet|dose)\s*(at|for|of)?\s*(morning|afternoon|evening|night|bedtime)",
]


def find_number_before_keywords(text, keywords):
    for keyword in keywords:
        pattern = rf"(\d+(\.\d+)?)\s*(hours|hour|hrs|hr)?\s*(of\s*)?{keyword}"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    return None


def find_number_after_keywords(text, keywords):
    for keyword in keywords:
        pattern = rf"{keyword}\s*(is|was|of|only|for|:)?\s*(\d+(\.\d+)?)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(2))
    return None


def find_only_hours(text):
    pattern = r"(only|just)\s*(\d+(\.\d+)?)\s*(hours|hour|hrs|hr)"
    match = re.search(pattern, text)
    if match:
        return float(match.group(2))
    return None


def contains_any(text, phrases):
    return any(phrase in text for phrase in phrases)


def contains_missed_medicine(text):
    return contains_any(text, NEGATIVE_MEDICINE_PHRASES) or bool(
        re.search(r"(missed|forgot|skip|skipped|did not take|didn't take).{0,30}(medicine|meds|tablet|dose)", text)
    )


def contains_missed_meal(text):
    return contains_any(text, NEGATIVE_MEAL_PHRASES) or bool(
        re.search(r"(missed|forgot|skip|skipped|did not eat|didn't eat|did not have|didn't have).{0,30}(breakfast|lunch|dinner|meal|food)", text)
    )


def extract_meal_detail(text):
    missed = []
    for meal, phrases in MEAL_DETAILS.items():
        if contains_any(text, phrases):
            missed.append(meal.title())
    return ", ".join(missed)


def normalize_time_detail(value):
    words = {
        "morning": "Morning medicine",
        "afternoon": "Afternoon medicine",
        "evening": "Evening medicine",
        "night": "Night medicine",
        "bedtime": "Bedtime medicine",
    }
    return words.get(value, value.upper() if value in {"am", "pm"} else value)


def extract_medicine_detail(text):
    for pattern in MEDICINE_TIME_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue

        groups = [group for group in match.groups() if group]
        period = next((group for group in groups if group in {"am", "pm"}), "")
        clock = next((group for group in groups if re.fullmatch(r"\d{1,2}", group)), "")
        minutes = next((group for group in groups if re.fullmatch(r":\d{2}", group)), "")
        named_time = next(
            (group for group in groups if group in {"morning", "afternoon", "evening", "night", "bedtime"}),
            "",
        )

        if clock:
            return f"{clock}{minutes} {period.upper()} medicine".strip()
        if named_time:
            return normalize_time_detail(named_time)
    return ""


def extract_health_data(message):
    text = message.lower()
    data = {}

    sleep_hours = find_number_before_keywords(text, ["sleep", "slept"])
    if sleep_hours is None:
        sleep_hours = find_number_after_keywords(text, ["sleep", "slept", "select"])
    if sleep_hours is None:
        sleep_hours = find_only_hours(text)
    if sleep_hours is not None:
        data["sleep_hours"] = sleep_hours

    heart_rate = find_number_after_keywords(text, ["heart rate", "pulse"])
    if heart_rate is not None:
        data["heart_rate"] = int(heart_rate)

    spo2 = find_number_after_keywords(text, ["spo2", "oxygen", "oxygen level"])
    if spo2 is not None:
        data["spo2"] = int(spo2)

    steps = find_number_after_keywords(text, ["steps", "walked"])
    if steps is not None:
        data["steps"] = int(steps)

    if contains_missed_medicine(text):
        data["missed_meds"] = 1
        detail = extract_medicine_detail(text)
        if detail:
            data["missed_meds_detail"] = detail
    elif contains_any(text, POSITIVE_MEDICINE_PHRASES):
        data["missed_meds"] = 0

    if contains_missed_meal(text):
        data["missed_meals"] = 1
        detail = extract_meal_detail(text)
        if detail:
            data["missed_meals_detail"] = detail
    elif contains_any(text, POSITIVE_MEAL_PHRASES):
        data["missed_meals"] = 0

    if contains_any(text, NO_FALL_PHRASES):
        data["falls"] = 0
    elif contains_any(text, FALL_PHRASES):
        data["falls"] = 1

    return data


def make_reply(message, extracted_data, saved_record):
    if saved_record is None:
        saved_record = {}

    risk = saved_record.get("risk", "Low")
    reasons = saved_record.get("reasons", [])

    if not extracted_data:
        return "I could not find health details in that sentence. Please tell me about sleep, medicine, meals, or symptoms."

    if risk == "High":
        reason_text = ", ".join(reasons) if reasons else "your current health details"
        return f"Your risk looks high because of {reason_text}. Please rest and inform a caregiver."

    if risk == "Medium":
        reason_text = ", ".join(reasons) if reasons else "some warning signs"
        return f"I noticed {reason_text}. Please take care and follow your routine."

    return "Thank you. Your details have been saved, and your current risk looks low."
