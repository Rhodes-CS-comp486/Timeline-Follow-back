import csv
from collections import defaultdict
from datetime import datetime, timedelta

from database.db_initialization import User, CalendarEntry, Drinking, Gambling
from config.config_helper import *

# This function generates the csv file for all users
# Parameters: N/A
# Returns: the output path for the csv to be saved
def generate_user_csv_report(user_id: int, start_date=None, end_date=None, output_path: str = None):
    # load in the scheme/questions from our JSON file
    schema = load_questions()
    # generate cvs headers with our question
    headers = get_csv_headers(schema)
    # getting the "field id" of the questions noted as "id" in our JSON file
    dynamic_fields = get_all_field_ids(schema)

    user = User.query.get(user_id)
    if not user:
        raise Exception(f"User {user_id} not found")

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        # include full end day
        end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

    query = CalendarEntry.query.filter_by(user_id=user_id)

    if start_date:
        query = query.filter(CalendarEntry.entry_date >= start_date)
    if end_date:
        query = query.filter(CalendarEntry.entry_date < end_date)

    entries = query.all()

    # Group by date
    grouped = defaultdict(list)
    for e in entries:
        date_str = e.entry_date.strftime("%Y-%m-%d")
        grouped[date_str].append(e)

    if not output_path:
        output_path = f"user_{user_id}_report.csv"

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(headers)

        for date, day_entries in sorted(grouped.items()):
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

            # Look to change this since it is hard code!
            row = [
                user.id,
                user.username,
                date,
                has_drinking,
                has_gambling,
            ]

            for field in dynamic_fields:
                row.append(merged_data.get(field))

            writer.writerow(row)

    return output_path

# This function generates the csv file for a single users
# Parameters: N/A
# Returns: the output path for the csv to be saved
def generate_all_users_csv(start_date=None, end_date=None, output_path="all_users_report.csv"):
    schema = load_questions()
    headers = get_csv_headers(schema)
    dynamic_fields = get_all_field_ids(schema)

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

    users = User.query.all()

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(headers)

        for user in users:

            query = CalendarEntry.query.filter_by(user_id=user.id)

            if start_date:
                query = query.filter(CalendarEntry.entry_date >= start_date)
            if end_date:
                query = query.filter(CalendarEntry.entry_date < end_date)

            entries = query.all()

            grouped = defaultdict(list)
            for e in entries:
                date_str = e.entry_date.strftime("%Y-%m-%d")
                grouped[date_str].append(e)

            for date, day_entries in sorted(grouped.items()):
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

                row = [
                    user.id,
                    user.username,
                    date,
                    has_drinking,
                    has_gambling,
                ]

                for field in dynamic_fields:
                    row.append(merged_data.get(field))

                writer.writerow(row)

    return output_path