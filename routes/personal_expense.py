import calendar
import csv
import io
import json
import re
from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, Response, abort, redirect, render_template, request, session, url_for
from sqlalchemy import MetaData, Table, and_, insert, select, update
from sqlalchemy.exc import NoSuchTableError, SQLAlchemyError

from database.db_initialization import User, db


personal_expense_bp = Blueprint("personal_expense", __name__)


FIELD_DEFINITIONS = [
    {"key": "income", "label": "Income", "color": "#1f8a70"},
    {"key": "food_groceries", "label": "Food/groceries", "color": "#2a9d8f"},
    {"key": "utilities", "label": "Utilities", "color": "#457b9d"},
    {"key": "phone_internet_and_or_tv", "label": "Phone, Internet, and/or TV", "color": "#264653"},
    {"key": "rent_mortgage", "label": "Rent/mortgage", "color": "#e76f51"},
    {"key": "transportation_car", "label": "Transportation/car", "color": "#f4a261"},
    {"key": "medical_expenses", "label": "Medical expenses", "color": "#e63946"},
    {"key": "school_books_class_fees_tuition", "label": "School (books, class fees, tuition)", "color": "#6d597a"},
    {"key": "debt_repayment", "label": "Debt repayment", "color": "#b56576"},
    {"key": "savings", "label": "Savings", "color": "#43aa8b"},
]

EXPENSE_FIELDS = [field for field in FIELD_DEFINITIONS if field["key"] != "income"]
FIELD_KEYS = [field["key"] for field in FIELD_DEFINITIONS]

FIELD_ALIASES = {
    "income": ["income", "monthly_income", "take_home_income", "monthly_take_home"],
    "food_groceries": ["food_groceries", "food_and_groceries", "groceries", "food"],
    "utilities": ["utilities", "utility"],
    "phone_internet_and_or_tv": [
        "phone_internet_and_or_tv",
        "phone_internet_tv",
        "phone_internet_cable",
        "phone_tv_internet",
    ],
    "rent_mortgage": ["rent_mortgage", "rent_or_mortgage", "rent", "mortgage"],
    "transportation_car": ["transportation_car", "transportation", "car", "transport"],
    "medical_expenses": ["medical_expenses", "medical", "healthcare_expenses", "healthcare"],
    "school_books_class_fees_tuition": [
        "school_books_class_fees_tuition",
        "school_expenses",
        "school",
        "tuition",
        "books_fees_tuition",
    ],
    "debt_repayment": ["debt_repayment", "debt", "loan_repayment", "repayment"],
    "savings": ["savings", "saving"],
}


def normalize_name(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower()) if value else ""


def parse_decimal(raw_value, label):
    value = str(raw_value or "").strip()
    if not value:
        return 0.0, None

    if not re.fullmatch(r"\d+(\.\d{1,2})?", value):
        return None, f"{label} must be a non-negative number with at most 2 decimal places."

    amount = float(value)
    if amount < 0:
        return None, f"{label} cannot be negative."

    return amount, None


def to_float(value):
    if value in (None, ""):
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_json_value(raw_value):
    if raw_value in (None, ""):
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def default_payload():
    return {field["key"]: 0.0 for field in FIELD_DEFINITIONS}


def current_month_key():
    today = date.today()
    return f"{today.year}-{today.month:02d}"


def month_options():
    year = date.today().year
    return [
        {
            "value": f"{year}-{month:02d}",
            "label": f"{calendar.month_name[month]} {year}",
        }
        for month in range(1, 13)
    ]


def resolve_month_key(raw_value):
    valid_values = {option["value"] for option in month_options()}
    if raw_value in valid_values:
        return raw_value
    return current_month_key()


def month_context(month_key):
    selected_date = datetime.strptime(month_key, "%Y-%m")
    return {
        "key": month_key,
        "label": selected_date.strftime("%B %Y"),
        "name": selected_date.strftime("%B"),
        "number": selected_date.month,
        "year": selected_date.year,
        "start_date": selected_date.date().replace(day=1),
        "start_datetime": selected_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
    }


def get_current_standard_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = User.query.get(user_id)
    if not user:
        return None
    if user.is_admin:
        abort(403)
    return user


def reflect_personal_expense_table():
    metadata = MetaData()
    return Table("personal_expense", metadata, autoload_with=db.engine)


def resolve_column(table, candidates):
    normalized_columns = {normalize_name(column.name): column for column in table.columns}
    for candidate in candidates:
        column = normalized_columns.get(normalize_name(candidate))
        if column is not None:
            return column
    return None


def resolve_user_column(table):
    return resolve_column(table, ["user_id", "userid", "user"])


def resolve_payload_column(table):
    direct_match = resolve_column(
        table,
        [
            "expense_data",
            "personal_expense_data",
            "personal_expense_payload",
            "activity_data",
            "data",
            "payload",
            "questions",
            "drinking_questions",
        ],
    )
    if direct_match is not None:
        return direct_match

    for column in table.columns:
        normalized = normalize_name(column.name)
        if any(token in normalized for token in ["payload", "json", "data", "question"]):
            return column

    return None


def resolve_month_storage(table):
    return {
        "month_key": resolve_column(
            table,
            ["month_key", "expense_month_key", "selected_month", "period_key", "month_year"],
        ),
        "month_name": resolve_column(table, ["month_name"]),
        "month_number": resolve_column(table, ["month_number", "month_num"]),
        "year": resolve_column(table, ["year", "expense_year"]),
        "period_start": resolve_column(
            table,
            ["month_start", "period_start", "entry_date", "expense_date", "month_date"],
        ),
        "month": resolve_column(table, ["month"]),
    }


def resolve_timestamp_columns(table):
    return {
        "created_at": resolve_column(table, ["created_at", "created_on"]),
        "updated_at": resolve_column(table, ["updated_at", "updated_on", "modified_at"]),
    }


def resolve_field_columns(table):
    reserved_columns = {
        column.name
        for column in [
            resolve_user_column(table),
            resolve_payload_column(table),
            *resolve_month_storage(table).values(),
        ]
        if column is not None
    }
    field_columns = {}
    for field in FIELD_KEYS:
        column = resolve_column(table, FIELD_ALIASES[field])
        if column is not None and column.name not in reserved_columns:
            field_columns[field] = column
    return field_columns


def column_type_name(column):
    return column.type.__class__.__name__.lower()


def is_integer_like(column):
    return any(token in column_type_name(column) for token in ["integer", "smallint", "bigint"])


def is_datetime_like(column):
    return any(token in column_type_name(column) for token in ["datetime", "timestamp"])


def build_month_filters(storage_columns, context):
    filters = []

    if storage_columns["month_key"] is not None:
        filters.append(storage_columns["month_key"] == context["key"])
    if storage_columns["month_name"] is not None:
        filters.append(storage_columns["month_name"] == context["name"])
    if storage_columns["month_number"] is not None:
        filters.append(storage_columns["month_number"] == context["number"])
    if storage_columns["year"] is not None:
        filters.append(storage_columns["year"] == context["year"])
    if storage_columns["period_start"] is not None:
        period_value = context["start_datetime"] if is_datetime_like(storage_columns["period_start"]) else context["start_date"]
        filters.append(storage_columns["period_start"] == period_value)
    if storage_columns["month"] is not None:
        month_column = storage_columns["month"]
        if is_integer_like(month_column):
            filters.append(month_column == context["number"])
        else:
            filters.append(
                month_column.in_(
                    [
                        context["key"],
                        context["label"],
                        context["name"],
                        f"{context['number']:02d}",
                        str(context["number"]),
                    ]
                )
            )

    return filters


def build_month_values(storage_columns, context):
    values = {}

    if storage_columns["month_key"] is not None:
        values[storage_columns["month_key"].name] = context["key"]
    if storage_columns["month_name"] is not None:
        values[storage_columns["month_name"].name] = context["name"]
    if storage_columns["month_number"] is not None:
        values[storage_columns["month_number"].name] = context["number"]
    if storage_columns["year"] is not None:
        values[storage_columns["year"].name] = context["year"]
    if storage_columns["period_start"] is not None:
        values[storage_columns["period_start"].name] = (
            context["start_datetime"] if is_datetime_like(storage_columns["period_start"]) else context["start_date"]
        )
    if storage_columns["month"] is not None:
        values[storage_columns["month"].name] = context["number"] if is_integer_like(storage_columns["month"]) else context["key"]

    return values


def has_month_specific_storage(storage_columns):
    return any(column is not None for column in storage_columns.values())


def build_payload_document(payload, context):
    return {
        "month_key": context["key"],
        "month_label": context["label"],
        **payload,
    }


def serialize_payload(column, payload):
    try:
        python_type = column.type.python_type
    except (AttributeError, NotImplementedError):
        python_type = None
    if python_type is dict:
        return payload
    return json.dumps(payload)


def fetch_expense_row(table, user_id, context):
    user_column = resolve_user_column(table)
    if user_column is None:
        raise RuntimeError("The personal_expense table must include a user_id column.")

    storage_columns = resolve_month_storage(table)
    filters = [user_column == user_id]
    month_filters = build_month_filters(storage_columns, context)
    if month_filters:
        filters.extend(month_filters)

    statement = select(table).where(and_(*filters)).limit(1)
    return db.session.execute(statement).mappings().first()


def fetch_expense_snapshot_row(table, user_id):
    user_column = resolve_user_column(table)
    if user_column is None:
        raise RuntimeError("The personal_expense table must include a user_id column.")

    statement = select(table).where(user_column == user_id)
    timestamp_columns = resolve_timestamp_columns(table)

    if timestamp_columns["updated_at"] is not None:
        statement = statement.order_by(timestamp_columns["updated_at"].desc())
    elif timestamp_columns["created_at"] is not None:
        statement = statement.order_by(timestamp_columns["created_at"].desc())
    else:
        primary_keys = list(table.primary_key.columns)
        if primary_keys:
            statement = statement.order_by(primary_keys[0].desc())

    return db.session.execute(statement.limit(1)).mappings().first()


def extract_snapshot_document(stored_payload):
    if not isinstance(stored_payload, dict):
        return {}

    profile_payload = stored_payload.get("profile")
    if isinstance(profile_payload, dict):
        return profile_payload

    if any(field["key"] in stored_payload for field in FIELD_DEFINITIONS):
        return stored_payload

    months_map = stored_payload.get("months")
    if isinstance(months_map, dict) and months_map:
        latest_month_key = max(
            (key for key, value in months_map.items() if isinstance(value, dict)),
            default=None,
        )
        if latest_month_key:
            latest_payload = months_map.get(latest_month_key)
            if isinstance(latest_payload, dict):
                return latest_payload

    return {}


def read_payload_for_month(table, user_id, context):
    row = fetch_expense_row(table, user_id, context)
    payload = default_payload()

    if row is None:
        return row, payload

    payload_column = resolve_payload_column(table)
    storage_columns = resolve_month_storage(table)

    if payload_column is not None:
        stored_payload = parse_json_value(row.get(payload_column.name))
        if stored_payload:
            if not has_month_specific_storage(storage_columns):
                months_map = stored_payload.get("months")
                if isinstance(months_map, dict):
                    stored_payload = months_map.get(context["key"], {})
                elif context["key"] in stored_payload and isinstance(stored_payload[context["key"]], dict):
                    stored_payload = stored_payload[context["key"]]
            for field in FIELD_DEFINITIONS:
                if field["key"] in stored_payload:
                    payload[field["key"]] = to_float(stored_payload[field["key"]])

    field_columns = resolve_field_columns(table)
    for field_key, column in field_columns.items():
        payload[field_key] = to_float(row.get(column.name))

    return row, payload


def read_expense_snapshot(table, user_id):
    row = fetch_expense_snapshot_row(table, user_id)
    payload = default_payload()

    if row is None:
        return row, payload

    payload_column = resolve_payload_column(table)
    if payload_column is not None:
        stored_payload = extract_snapshot_document(parse_json_value(row.get(payload_column.name)))
        for field in FIELD_DEFINITIONS:
            if field["key"] in stored_payload:
                payload[field["key"]] = to_float(stored_payload[field["key"]])

    field_columns = resolve_field_columns(table)
    for field_key, column in field_columns.items():
        payload[field_key] = to_float(row.get(column.name))

    return row, payload


def save_payload_for_month(table, user_id, context, payload):
    existing_row, existing_payload = read_payload_for_month(table, user_id, context)

    user_column = resolve_user_column(table)
    storage_columns = resolve_month_storage(table)
    payload_column = resolve_payload_column(table)
    field_columns = resolve_field_columns(table)
    timestamp_columns = resolve_timestamp_columns(table)

    values = {user_column.name: user_id}
    values.update(build_month_values(storage_columns, context))

    for field_key, column in field_columns.items():
        values[column.name] = payload[field_key]

    now = datetime.utcnow()
    if timestamp_columns["updated_at"] is not None:
        values[timestamp_columns["updated_at"].name] = now

    if payload_column is not None:
        payload_document = build_payload_document(payload, context)

        if not has_month_specific_storage(storage_columns):
            merged_document = {}
            if existing_row is not None:
                raw_existing_payload = parse_json_value(existing_row.get(payload_column.name))
                if isinstance(raw_existing_payload, dict):
                    merged_document = raw_existing_payload

            months_map = merged_document.get("months")
            if not isinstance(months_map, dict):
                months_map = {}

            months_map[context["key"]] = payload_document
            merged_document["months"] = months_map
            values[payload_column.name] = serialize_payload(payload_column, merged_document)
        else:
            values[payload_column.name] = serialize_payload(payload_column, payload_document)

    try:
        if existing_row is None:
            if timestamp_columns["created_at"] is not None:
                values[timestamp_columns["created_at"].name] = now
            db.session.execute(insert(table).values(**values))
        else:
            primary_key_filters = [
                column == existing_row[column.name] for column in table.primary_key.columns
            ]
            update_filters = primary_key_filters or [user_column == user_id]
            db.session.execute(update(table).where(and_(*update_filters)).values(**values))

        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise RuntimeError("Unable to save personal expense data.") from exc


def save_expense_snapshot(table, user_id, payload):
    existing_row, existing_payload = read_expense_snapshot(table, user_id)

    user_column = resolve_user_column(table)
    payload_column = resolve_payload_column(table)
    field_columns = resolve_field_columns(table)
    timestamp_columns = resolve_timestamp_columns(table)

    values = {user_column.name: user_id}

    if existing_row is None:
        values.update(build_month_values(resolve_month_storage(table), month_context(current_month_key())))

    for field_key, column in field_columns.items():
        values[column.name] = payload[field_key]

    now = datetime.utcnow()
    if timestamp_columns["updated_at"] is not None:
        values[timestamp_columns["updated_at"].name] = now

    if payload_column is not None:
        merged_document = {}
        if existing_row is not None:
            raw_existing_payload = parse_json_value(existing_row.get(payload_column.name))
            if isinstance(raw_existing_payload, dict):
                merged_document = raw_existing_payload

        merged_document["profile"] = {
            **existing_payload,
            **payload,
        }
        values[payload_column.name] = serialize_payload(payload_column, merged_document)

    try:
        if existing_row is None:
            if timestamp_columns["created_at"] is not None:
                values[timestamp_columns["created_at"].name] = now
            db.session.execute(insert(table).values(**values))
        else:
            primary_key_filters = [
                column == existing_row[column.name] for column in table.primary_key.columns
            ]
            update_filters = primary_key_filters or [user_column == user_id]
            db.session.execute(update(table).where(and_(*update_filters)).values(**values))

        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise RuntimeError("Unable to save personal expense data.") from exc


def calculate_totals(payload):
    income = payload["income"]
    savings = payload["savings"]
    expense_total = sum(payload[field["key"]] for field in EXPENSE_FIELDS if field["key"] != "savings")
    allocation_total = sum(payload[field["key"]] for field in EXPENSE_FIELDS)
    remaining = income - allocation_total
    return {
        "income": income,
        "expense_total": expense_total,
        "savings": savings,
        "allocation_total": allocation_total,
        "remaining": remaining,
    }


@personal_expense_bp.route("/personal-expense", methods=["GET", "POST"])
def personal_expense():
    user = get_current_standard_user()
    if not user:
        return redirect(url_for("auth.login"))

    status = request.args.get("status")
    error_message = None

    try:
        table = reflect_personal_expense_table()
    except NoSuchTableError:
        table = None
        error_message = "The personal_expense table was not found in the database."
    except SQLAlchemyError:
        table = None
        error_message = "The personal expense page could not connect to the database."

    payload = default_payload()

    if request.method == "POST" and table is not None:
        payload = {}
        for field in FIELD_DEFINITIONS:
            amount, field_error = parse_decimal(request.form.get(field["key"]), field["label"])
            if field_error:
                error_message = field_error
                break
            payload[field["key"]] = amount

        if error_message is None:
            try:
                save_expense_snapshot(table, user.id, payload)
                return redirect(url_for("personal_expense.personal_expense", status="saved"))
            except RuntimeError as exc:
                error_message = str(exc)

    if table is not None and request.method == "GET":
        try:
            _, payload = read_expense_snapshot(table, user.id)
        except RuntimeError as exc:
            error_message = str(exc)

    totals = calculate_totals(payload)

    return render_template(
        "personal_expense.html",
        categories=EXPENSE_FIELDS,
        field_definitions=FIELD_DEFINITIONS,
        payload=payload,
        totals=totals,
        status=status,
        error_message=error_message,
    )


@personal_expense_bp.route("/personal-expense/download")
def download_personal_expense_csv():
    user = get_current_standard_user()
    if not user:
        return redirect(url_for("auth.login"))

    try:
        table = reflect_personal_expense_table()
    except (NoSuchTableError, SQLAlchemyError):
        return redirect(url_for("personal_expense.personal_expense"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Category", "Amount"])

    try:
        _, payload = read_expense_snapshot(table, user.id)
    except RuntimeError:
        return redirect(url_for("personal_expense.personal_expense"))

    for field in FIELD_DEFINITIONS:
        writer.writerow([field["label"], f"{payload[field['key']]:.2f}"])

    filename = "personal_expense_profile.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
