"""Tests for report dataset and CSV generation."""
import csv
from datetime import datetime

from csv_formatting.csv_creator import build_report_dataset, generate_all_users_csv
from database.db_initialization import CalendarEntry, Drinking, Gambling, User, db


CUSTOM_SCHEMA = {
    "drinking": [
        {"id": "beer_count", "label": "Beers", "type": "number"},
    ],
    "gambling": [
        {"id": "casino_game", "label": "Casino game", "type": "text"},
        {"id": "cash_wagered", "label": "Cash wagered", "type": "number"},
    ],
}


def _create_custom_activity_user():
    user = User(
        username="custom-report@test.com",
        password="x",
        is_admin=False,
        study_group_code="custom01",
    )
    db.session.add(user)
    db.session.commit()

    entry = CalendarEntry(user_id=user.id, entry_date=datetime(2026, 4, 15))
    db.session.add(entry)
    db.session.commit()

    db.session.add(Drinking(
        user_id=user.id,
        entry_id=entry.id,
        drinking_questions={"beer_count": "3"},
    ))
    db.session.add(Gambling(
        user_id=user.id,
        entry_id=entry.id,
        gambling_questions={"casino_game": "Slots", "cash_wagered": "50"},
    ))
    db.session.commit()

    return user


def test_report_dataset_uses_custom_study_schema(app_context):
    """Custom study question IDs should appear as headers and populated row values."""
    user = _create_custom_activity_user()

    headers, rows = build_report_dataset(user_ids=[user.id], schema=CUSTOM_SCHEMA)

    assert headers == [
        "user_id",
        "date",
        "has_drinking",
        "has_gambling",
        "beer_count",
        "casino_game",
        "cash_wagered",
    ]
    assert len(rows) == 1
    assert rows[0]["beer_count"] == "3"
    assert rows[0]["casino_game"] == "Slots"
    assert rows[0]["cash_wagered"] == "50"


def test_all_users_csv_uses_custom_study_schema(app_context, tmp_path):
    """CSV downloads should write custom study values instead of blank default columns."""
    user = _create_custom_activity_user()
    output_path = tmp_path / "custom-report.csv"

    generate_all_users_csv(
        user_ids=[user.id],
        output_path=str(output_path),
        schema=CUSTOM_SCHEMA,
    )

    with open(output_path, newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["beer_count"] == "3"
    assert rows[0]["casino_game"] == "Slots"
    assert rows[0]["cash_wagered"] == "50"
