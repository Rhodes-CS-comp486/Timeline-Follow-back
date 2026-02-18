from datetime import datetime

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func

from database.db_initialization import CalendarEntry, Drinking, Gambling, db

# Create a blueprint to handle events, this will be called in app.py
events_handler_bp = Blueprint('events_handler', __name__)


def get_user_id():
    user_id = session.get('user_id')
    return user_id if user_id else 1


def parse_iso_date(date_value: str):
    if not date_value or not isinstance(date_value, str):
        return None
    try:
        return datetime.strptime(date_value, '%Y-%m-%d')
    except ValueError:
        return None


def clean_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed if trimmed else None
    return value


def find_calendar_entry(user_id: int, entry_type: str, entry_date: datetime):
    return CalendarEntry.query.filter(
        CalendarEntry.user_id == user_id,
        CalendarEntry.entry_type == entry_type,
        func.date(CalendarEntry.entry_date) == entry_date.date(),
    ).first()


def ensure_calendar_entry(user_id: int, entry_type: str, entry_date: datetime):
    existing = find_calendar_entry(user_id, entry_type, entry_date)
    if existing:
        return existing

    created = CalendarEntry(
        user_id=user_id,
        entry_type=entry_type,
        entry_date=entry_date,
    )
    db.session.add(created)
    db.session.flush()
    return created


def upsert_drinking(user_id: int, entry_date: datetime, data: dict):
    entry = ensure_calendar_entry(user_id, 'drinking', entry_date)
    drinks = clean_value(data.get('drinks'))

    drinking_record = Drinking.query.filter_by(entry_id=entry.id).first()
    drinking_payload = {
        'user_id': user_id,
        'entry_id': entry.id,
        'num_drinks': drinks,
    }

    if drinking_record:
        drinking_record.drinking_questions = drinking_payload
    else:
        db.session.add(
            Drinking(
                user_id=user_id,
                entry_id=entry.id,
                drinking_questions=drinking_payload,
            )
        )


def upsert_gambling(user_id: int, entry_date: datetime, data: dict):
    entry = ensure_calendar_entry(user_id, 'gambling', entry_date)

    gambling_payload = {
        'user_id': user_id,
        'entry_id': entry.id,
        'gambling_type': clean_value(data.get('gambling_type')),
        'time_spent': clean_value(data.get('time_spent')),
        'amount_intended_spent': clean_value(data.get('money_intended')),
        'amount_spent': clean_value(data.get('money_spent')),
        'amount_earned': clean_value(data.get('money_earned')),
        'num_drinks': clean_value(data.get('drinks_while_gambling')),
    }

    gambling_record = Gambling.query.filter_by(entry_id=entry.id).first()
    if gambling_record:
        gambling_record.gambling_questions = gambling_payload
    else:
        db.session.add(
            Gambling(
                user_id=user_id,
                entry_id=entry.id,
                gambling_questions=gambling_payload,
            )
        )


def serialize_entry_by_date(user_id: int, entry_date: datetime):
    date_key = entry_date.date().isoformat()
    result = {
        'date': date_key,
        'drinking': None,
        'gambling': None,
    }

    rows = CalendarEntry.query.filter(
        CalendarEntry.user_id == user_id,
        func.date(CalendarEntry.entry_date) == entry_date.date(),
    ).all()

    for row in rows:
        if row.entry_type == 'drinking':
            drinking = Drinking.query.filter_by(entry_id=row.id).first()
            num_drinks = None
            if drinking and drinking.drinking_questions:
                num_drinks = drinking.drinking_questions.get('num_drinks')
            result['drinking'] = {
                'id': row.id,
                'drinks': num_drinks,
            }
        elif row.entry_type == 'gambling':
            gambling = Gambling.query.filter_by(entry_id=row.id).first()
            payload = gambling.gambling_questions if gambling and gambling.gambling_questions else {}
            result['gambling'] = {
                'id': row.id,
                'gambling_type': payload.get('gambling_type'),
                'time_spent': payload.get('time_spent'),
                'money_intended': payload.get('amount_intended_spent'),
                'money_spent': payload.get('amount_spent'),
                'money_earned': payload.get('amount_earned'),
                'drinks_while_gambling': payload.get('num_drinks'),
            }

    return result


def normalize_legacy_payload(data: dict):
    activities = data.get('activities')
    if isinstance(activities, dict):
        return activities

    legacy_type = data.get('type')
    if legacy_type == 'drinking':
        return {
            'drinking': {
                'drinks': data.get('drinks'),
            }
        }
    if legacy_type == 'gambling':
        return {
            'gambling': {
                'gambling_type': data.get('gambling_type'),
                'time_spent': data.get('time_spent'),
                'money_intended': data.get('money_intended'),
                'money_spent': data.get('money_spent'),
                'money_earned': data.get('money_earned'),
                'drinks_while_gambling': data.get('drinks_while_gambling'),
            }
        }
    return {}


@events_handler_bp.route('/log-activity', methods=['POST'])
def log_activity():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    user_id = get_user_id()
    entry_date = parse_iso_date(data.get('date'))
    if not entry_date:
        return jsonify({'status': 'error', 'message': 'Invalid or missing date'}), 400

    activities = normalize_legacy_payload(data)
    if not activities:
        return jsonify({'status': 'error', 'message': 'No activity selected'}), 400

    try:
        if activities.get('drinking'):
            upsert_drinking(user_id, entry_date, activities.get('drinking') or {})

        if activities.get('gambling'):
            upsert_gambling(user_id, entry_date, activities.get('gambling') or {})

        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Activity saved successfully',
            'entry': serialize_entry_by_date(user_id, entry_date),
        }), 200
    except Exception as exc:
        db.session.rollback()
        print(f'Save Error: {exc}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to save activity. Check server logs for details.',
        }), 500


@events_handler_bp.route('/delete-activity', methods=['POST'])
def delete_activity():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    entry_date = parse_iso_date(data.get('date'))
    entry_type = data.get('type')
    if not entry_date or entry_type not in {'drinking', 'gambling'}:
        return jsonify({'status': 'error', 'message': 'Invalid date or type'}), 400

    user_id = get_user_id()
    entry = find_calendar_entry(user_id, entry_type, entry_date)
    if not entry:
        return jsonify({'status': 'error', 'message': 'Entry not found'}), 404

    try:
        if entry_type == 'drinking':
            Drinking.query.filter_by(entry_id=entry.id).delete()
        else:
            Gambling.query.filter_by(entry_id=entry.id).delete()

        db.session.delete(entry)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'{entry_type.title()} entry deleted',
            'entry': serialize_entry_by_date(user_id, entry_date),
        }), 200
    except Exception as exc:
        db.session.rollback()
        print(f'Delete Error: {exc}')
        return jsonify({'status': 'error', 'message': 'Failed to delete entry'}), 500


@events_handler_bp.route('/calendar-events', methods=['GET'])
def get_calendar_events():
    user_id = get_user_id()

    try:
        rows = CalendarEntry.query.filter_by(user_id=user_id).order_by(
            CalendarEntry.entry_date
        ).all()

        grouped = {}
        for row in rows:
            date_key = row.entry_date.date().isoformat()
            if date_key not in grouped:
                grouped[date_key] = {
                    'date': date_key,
                    'drinking': None,
                    'gambling': None,
                }

            if row.entry_type == 'drinking':
                drinking = Drinking.query.filter_by(entry_id=row.id).first()
                num_drinks = None
                if drinking and drinking.drinking_questions:
                    num_drinks = drinking.drinking_questions.get('num_drinks')
                grouped[date_key]['drinking'] = {
                    'id': row.id,
                    'drinks': num_drinks,
                }
            elif row.entry_type == 'gambling':
                gambling = Gambling.query.filter_by(entry_id=row.id).first()
                payload = gambling.gambling_questions if gambling and gambling.gambling_questions else {}
                grouped[date_key]['gambling'] = {
                    'id': row.id,
                    'gambling_type': payload.get('gambling_type'),
                    'time_spent': payload.get('time_spent'),
                    'money_intended': payload.get('amount_intended_spent'),
                    'money_spent': payload.get('amount_spent'),
                    'money_earned': payload.get('amount_earned'),
                    'drinks_while_gambling': payload.get('num_drinks'),
                }

        return jsonify(list(grouped.values())), 200
    except Exception as exc:
        print(f'Error retrieving calendar events: {exc}')
        return jsonify({'status': 'error', 'message': 'Failed to retrieve events'}), 500
