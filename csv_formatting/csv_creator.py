import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta

from database.db_initialization import User, CalendarEntry, Drinking, Gambling
from config.config_helper import *

# Directory for temporary export files (avoids cluttering project root)
EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp", "exports")


def parse_report_date(date_str, include_end_of_day=False):
    if not date_str:
        return None

    parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
    if include_end_of_day:
        return parsed_date + timedelta(days=1)
    return parsed_date


def parse_filter_number(value):
    if value is None or str(value).strip() == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_reported_drink_values(row):
    drink_values = []

    for field in ["num_drinks", "drinks_while_gambling"]:
        parsed_value = parse_filter_number(row.get(field))
        if parsed_value is not None:
            drink_values.append(parsed_value)

    return drink_values


def row_matches_filters(row, report_type=None, num_drinks=None, gambling_without_drinks=False):
    if report_type == "drinking" and not row["has_drinking"]:
        return False

    if report_type == "gambling" and not row["has_gambling"]:
        return False

    reported_drinks = get_reported_drink_values(row)

    if num_drinks is not None:
        if not reported_drinks:
            return False
        if not any(drink_value == num_drinks for drink_value in reported_drinks):
            return False

    if gambling_without_drinks:
        if not row["has_gambling"] or row["has_drinking"]:
            return False
        if any(drink_value > 0 for drink_value in reported_drinks):
            return False

    return True


def build_report_dataset(user_id=None, user_ids=None, start_date=None, end_date=None, report_type=None, num_drinks=None, gambling_without_drinks=False):
    schema = load_questions()
    headers = get_csv_headers(schema)
    dynamic_fields = get_all_field_ids(schema)

    parsed_start_date = parse_report_date(start_date)
    parsed_end_date = parse_report_date(end_date, include_end_of_day=True)
    parsed_num_drinks = parse_filter_number(num_drinks)

    users_query = User.query.filter(User.is_admin.is_(False))
    if user_id is not None:
        users = users_query.filter_by(id=user_id).order_by(User.username.asc()).all()
    elif user_ids is not None:
        if user_ids:
            users = users_query.filter(User.id.in_(user_ids)).order_by(User.username.asc()).all()
        else:
            users = []
    else:
        users = users_query.order_by(User.username.asc()).all()

    rows = []

    for user in users:
        query = CalendarEntry.query.filter_by(user_id=user.id)

        if parsed_start_date:
            query = query.filter(CalendarEntry.entry_date >= parsed_start_date)
        if parsed_end_date:
            query = query.filter(CalendarEntry.entry_date < parsed_end_date)

        entries = query.order_by(CalendarEntry.entry_date.asc(), CalendarEntry.id.asc()).all()

        grouped_entries = defaultdict(list)
        for entry in entries:
            date_str = entry.entry_date.strftime("%Y-%m-%d")
            grouped_entries[date_str].append(entry)

        for date, day_entries in sorted(grouped_entries.items()):
            has_drinking = False
            has_gambling = False

            drinking_data = {}
            gambling_data = {}

            for entry in day_entries:
                drinking = Drinking.query.filter_by(entry_id=entry.id).first()
                gambling = Gambling.query.filter_by(entry_id=entry.id).first()

                if drinking and drinking.drinking_questions:
                    has_drinking = True
                    drinking_data.update(drinking.drinking_questions)

                if gambling and gambling.gambling_questions:
                    has_gambling = True
                    gambling_data.update(gambling.gambling_questions)

            merged_data = merge_activity_data(schema, drinking_data, gambling_data)

            row = {
                "user_id": user.id,
                "username": user.username,
                "date": date,
                "has_drinking": has_drinking,
                "has_gambling": has_gambling,
            }

            for field in dynamic_fields:
                row[field] = merged_data.get(field)

            if row_matches_filters(
                row,
                report_type=report_type,
                num_drinks=parsed_num_drinks,
                gambling_without_drinks=gambling_without_drinks,
            ):
                rows.append(row)

    return headers, rows

# This function generates the csv file for a single user
# Parameters: N/A
# Returns: the output path for the csv to be saved
def generate_user_csv_report(user_id: int, start_date=None, end_date=None, report_type=None, num_drinks=None, gambling_without_drinks=False, output_path: str = None):
    user = User.query.get(user_id)
    if not user:
        raise Exception(f"User {user_id} not found")

    headers, rows = build_report_dataset(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        report_type=report_type,
        num_drinks=num_drinks,
        gambling_without_drinks=gambling_without_drinks,
    )

    if not output_path:
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(EXPORTS_DIR, f"user_{user_id}_report_{timestamp}.csv")

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(headers)

        for row in rows:
            writer.writerow([row.get(header) for header in headers])

    return output_path

# This function generates the csv file for all users
# Parameters: N/A
# Returns: the output path for the csv to be saved
def generate_all_users_csv(start_date=None, end_date=None, report_type=None, num_drinks=None, gambling_without_drinks=False, user_ids=None, output_path=None):
    if output_path is None:
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(EXPORTS_DIR, f"all_users_report_{timestamp}.csv")

    headers, rows = build_report_dataset(
        user_ids=user_ids,
        start_date=start_date,
        end_date=end_date,
        report_type=report_type,
        num_drinks=num_drinks,
        gambling_without_drinks=gambling_without_drinks,
    )

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(headers)

        for row in rows:
            writer.writerow([row.get(header) for header in headers])

    return output_path
