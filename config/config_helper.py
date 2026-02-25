import os
import json
from flask import current_app

def load_questions():
    path = os.path.join(current_app.root_path,"config", "questions.json")
    with open(path) as f:
        return json.load(f)


def get_all_field_ids(schema: dict):
    """
    Returns all question IDs from drinking + gambling.
    Example: ['num_drinks', 'gambling_type', ...]
    """
    fields = []

    for section in ["drinking", "gambling"]:
        for q in schema.get(section, []):
            fields.append(q["id"])

    return fields


def get_csv_headers(schema: dict):
    """
    Build dynamic CSV headers.
    """
    base_headers = ["user_id", "username", "date", "has_drinking", "has_gambling"]
    dynamic_fields = get_all_field_ids(schema)

    return base_headers + dynamic_fields


def extract_answers(schema_section: list, answers_dict: dict):
    """
    Safely extract only valid fields from stored JSON.
    Prevents random keys from breaking your CSV.
    """
    result = {}

    if not answers_dict:
        return result

    valid_ids = [q["id"] for q in schema_section]

    for field_id in valid_ids:
        result[field_id] = answers_dict.get(field_id)

    return result


def merge_activity_data(schema: dict, drinking_data: dict, gambling_data: dict):
    """
    Combine drinking + gambling into one flat row.
    """
    merged = {}

    drinking_fields = extract_answers(schema["drinking"], drinking_data)
    gambling_fields = extract_answers(schema["gambling"], gambling_data)

    merged.update(drinking_fields)
    merged.update(gambling_fields)

    return merged