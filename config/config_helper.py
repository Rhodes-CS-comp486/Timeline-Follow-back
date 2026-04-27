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
    base_headers = ["user_id", "date", "has_drinking", "has_gambling"]
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


def field_map_from_schema(schema: dict) -> dict:
    """
    Return a dict mapping canonical role names to the actual stored question IDs
    for the given schema.  Positional order mirrors questions.json:
      drinking[0]  → num_drinks
      gambling[0]  → gambling_type
      gambling[1]  → time_spent
      gambling[2]  → money_intended
      gambling[3]  → money_spent
      gambling[4]  → money_earned
      gambling[5]  → drinks_while_gambling
    Falls back to the canonical name when a position is absent.
    """
    defaults = {
        'num_drinks':            'num_drinks',
        'gambling_type':         'gambling_type',
        'time_spent':            'time_spent',
        'money_intended':        'money_intended',
        'money_spent':           'money_spent',
        'money_earned':          'money_earned',
        'drinks_while_gambling': 'drinks_while_gambling',
    }
    if not schema:
        return defaults
    d_qs = schema.get('drinking', [])
    g_qs = schema.get('gambling', [])
    if not d_qs and not g_qs:
        return defaults
    return {
        'num_drinks':            d_qs[0]['id'] if len(d_qs) > 0 else defaults['num_drinks'],
        'gambling_type':         g_qs[0]['id'] if len(g_qs) > 0 else defaults['gambling_type'],
        'time_spent':            g_qs[1]['id'] if len(g_qs) > 1 else defaults['time_spent'],
        'money_intended':        g_qs[2]['id'] if len(g_qs) > 2 else defaults['money_intended'],
        'money_spent':           g_qs[3]['id'] if len(g_qs) > 3 else defaults['money_spent'],
        'money_earned':          g_qs[4]['id'] if len(g_qs) > 4 else defaults['money_earned'],
        'drinks_while_gambling': g_qs[5]['id'] if len(g_qs) > 5 else defaults['drinks_while_gambling'],
    }


def get_header_label_map(schema: dict) -> dict:
    """
    Maps each report column ID to a human-readable display label.
    Base columns get clean fixed labels; question columns use their schema label.
    """
    label_map = {
        "user_id":      "User ID",
        "date":         "Date",
        "has_drinking": "Drinking",
        "has_gambling": "Gambling",
    }
    for section in ["drinking", "gambling"]:
        for q in (schema or {}).get(section, []):
            label_map[q["id"]] = q["label"]
    return label_map


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