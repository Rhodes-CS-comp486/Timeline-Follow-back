import json
from datetime import datetime, timedelta

from flask import Blueprint, redirect, render_template, session, url_for
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy import asc

from database.db_initialization import CalendarEntry, Drinking, Gambling, User, db

insights_bp = Blueprint("insights", __name__)


def _get_expense_snapshot(user_id):
    try:
        from routes.personal_expense import (
            calculate_totals,
            read_expense_snapshot,
            reflect_personal_expense_table,
        )

        table = reflect_personal_expense_table()
        _, payload = read_expense_snapshot(table, user_id)
        return payload, calculate_totals(payload)
    except (NoSuchTableError, Exception):
        return {}, {
            "income": 0.0,
            "expense_total": 0.0,
            "savings": 0.0,
            "allocation_total": 0.0,
            "remaining": 0.0,
        }


def _get_three_month_income(user_id):
    """Estimate 3 months of income using the saved expense profile, with old monthly data as fallback."""
    _, expense_totals = _get_expense_snapshot(user_id)
    monthly_income = expense_totals.get("income", 0.0)
    if monthly_income > 0:
        return monthly_income * 3

    try:
        from routes.personal_expense import (
            month_context,
            read_payload_for_month,
            reflect_personal_expense_table,
        )

        table = reflect_personal_expense_table()
    except (NoSuchTableError, Exception):
        return 0.0

    today = datetime.utcnow()
    total_income = 0.0

    for months_back in range(3):
        month = today.month - months_back
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        ctx = month_context(f"{year}-{month:02d}")
        _, payload = read_payload_for_month(table, user_id, ctx)
        total_income += payload.get("income", 0.0)

    return total_income


def compute_insights(user_id):
    """Compute all insights data for a given user_id. Returns a dict of template variables."""
    three_months_ago = datetime.utcnow() - timedelta(days=91)
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = current_month_start
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_label = last_month_start.strftime("%B %Y")

    rows = (
        db.session.query(Gambling, CalendarEntry.entry_date)
        .join(CalendarEntry, Gambling.entry_id == CalendarEntry.id)
        .filter(
            Gambling.user_id == user_id,
            CalendarEntry.entry_date >= three_months_ago,
        )
        .order_by(asc(CalendarEntry.entry_date))
        .all()
    )

    total_sessions = len(rows)
    total_intended = 0.0
    total_wagered = 0.0
    total_hours = 0.0
    total_net_earned = 0.0
    sessions_over_intent = 0
    last_month_gambling_total = 0.0

    chart_labels = []
    chart_intended = []
    chart_wagered = []

    # month_key -> {label, sessions, intended, wagered, over_intent}
    monthly = {}

    for gambling, entry_date in rows:
        questions = gambling.gambling_questions or {}
        intended = float(questions.get("money_intended") or 0)
        wagered = float(questions.get("money_spent") or 0)
        total_intended += intended
        total_wagered += wagered
        total_hours += float(questions.get("time_spent") or 0)
        total_net_earned += float(questions.get("money_earned") or 0)
        if wagered > intended:
            sessions_over_intent += 1

        entry_moment = entry_date if isinstance(entry_date, datetime) else datetime.combine(entry_date, datetime.min.time())
        if last_month_start <= entry_moment < last_month_end:
            last_month_gambling_total += wagered

        chart_labels.append(entry_date.strftime("%b") + " " + str(entry_date.day))
        chart_intended.append(round(intended, 2))
        chart_wagered.append(round(wagered, 2))

        mk = entry_date.strftime("%Y-%m")
        if mk not in monthly:
            monthly[mk] = {
                "label": entry_date.strftime("%B %Y"),
                "sessions": 0,
                "intended": 0.0,
                "wagered": 0.0,
                "over_intent": 0,
            }
        monthly[mk]["sessions"] += 1
        monthly[mk]["intended"] += intended
        monthly[mk]["wagered"] += wagered
        if wagered > intended:
            monthly[mk]["over_intent"] += 1

    # sorted list for the template
    monthly_breakdown = [monthly[k] for k in sorted(monthly)]
    for m in monthly_breakdown:
        m["intended"] = round(m["intended"], 2)
        m["wagered"] = round(m["wagered"], 2)
        m["diff"] = round(m["wagered"] - m["intended"], 2)

    # monthly chart arrays (one bar pair per month)
    monthly_labels   = json.dumps([m["label"] for m in monthly_breakdown])
    monthly_intended = json.dumps([m["intended"] for m in monthly_breakdown])
    monthly_wagered  = json.dumps([m["wagered"] for m in monthly_breakdown])

    # ── Day-of-week breakdown ─────────────────────────────────────────────
    DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    dow_gambling = [{"day": d, "sessions": 0, "wagered": 0.0} for d in DOW_NAMES]
    for gambling, entry_date in rows:
        dow = entry_date.weekday()  # 0=Mon … 6=Sun
        questions = gambling.gambling_questions or {}
        dow_gambling[dow]["sessions"] += 1
        dow_gambling[dow]["wagered"] += float(questions.get("money_spent") or 0)

    dow_drinking_rows = (
        db.session.query(Drinking, CalendarEntry.entry_date)
        .join(CalendarEntry, Drinking.entry_id == CalendarEntry.id)
        .filter(
            Drinking.user_id == user_id,
            CalendarEntry.entry_date >= three_months_ago,
        )
        .all()
    )

    dow_drinking = [{"day": d, "sessions": 0, "drinks": 0.0} for d in DOW_NAMES]
    for drinking, entry_date in dow_drinking_rows:
        dow = entry_date.weekday()
        questions = drinking.drinking_questions or {}
        dow_drinking[dow]["sessions"] += 1
        dow_drinking[dow]["drinks"] += float(questions.get("num_drinks") or 0)

    # round wagered/drinks totals
    for d in dow_gambling:
        d["wagered"] = round(d["wagered"], 2)
    for d in dow_drinking:
        d["drinks"] = round(d["drinks"], 1)

    dow_labels             = json.dumps(DOW_NAMES)
    dow_gambling_sessions  = json.dumps([d["sessions"] for d in dow_gambling])
    dow_gambling_wagered   = json.dumps([d["wagered"]  for d in dow_gambling])
    dow_drinking_sessions  = json.dumps([d["sessions"] for d in dow_drinking])
    dow_drinking_drinks    = json.dumps([d["drinks"]   for d in dow_drinking])

    total_hours_rounded = round(total_hours, 1)
    total_days = int(total_hours_rounded // 24)
    remaining_hours = round(total_hours_rounded % 24, 1)

    total_losses = round(abs(total_net_earned), 2) if total_net_earned < 0 else 0.0

    # Projected losses (extrapolate 3-month loss rate)
    projected_1yr  = round(total_losses * 4)
    projected_5yr  = round(total_losses * 20)
    projected_10yr = round(total_losses * 40)
    projected_25yr = round(total_losses * 100)

    # Hourly comparison
    MIN_WAGE = 7.25
    min_wage_earnings = round(MIN_WAGE * total_hours_rounded, 2) if total_hours_rounded else 0.0
    loss_per_hour     = round(total_losses / total_hours_rounded, 2) if total_hours_rounded > 0 else 0.0

    excess_wagered = total_wagered - total_intended
    total_income = _get_three_month_income(user_id)
    _, expense_totals = _get_expense_snapshot(user_id)
    monthly_expense_total = round(expense_totals.get("expense_total", 0.0), 2)
    last_month_gambling_total = round(last_month_gambling_total, 2)
    expense_vs_gambling_has_data = monthly_expense_total > 0 or last_month_gambling_total > 0
    if monthly_expense_total > 0:
        expense_vs_gambling_pct = round((last_month_gambling_total / monthly_expense_total) * 100)
    else:
        expense_vs_gambling_pct = None

    if total_income > 0:
        intent_pct  = round((total_intended / total_income) * 100)
        risk_pct    = round((total_wagered  / total_income) * 100)
        loss_pct    = round((total_losses   / total_income) * 100) if total_losses > 0 else None
    else:
        intent_pct = None
        risk_pct   = None
        loss_pct   = None

    return dict(
        total_sessions=total_sessions,
        total_intended=total_intended,
        total_wagered=total_wagered,
        sessions_over_intent=sessions_over_intent,
        excess_wagered=excess_wagered,
        total_income=total_income,
        intent_pct=intent_pct,
        risk_pct=risk_pct,
        total_hours=total_hours_rounded,
        total_days=total_days,
        remaining_hours=remaining_hours,
        total_losses=total_losses,
        loss_pct=loss_pct,
        projected_1yr=projected_1yr,
        projected_5yr=projected_5yr,
        projected_10yr=projected_10yr,
        projected_25yr=projected_25yr,
        min_wage_earnings=min_wage_earnings,
        loss_per_hour=loss_per_hour,
        chart_labels=json.dumps(chart_labels),
        chart_intended=json.dumps(chart_intended),
        chart_wagered=json.dumps(chart_wagered),
        monthly_breakdown=monthly_breakdown,
        monthly_labels=monthly_labels,
        monthly_intended=monthly_intended,
        monthly_wagered=monthly_wagered,
        dow_gambling=dow_gambling,
        dow_drinking=dow_drinking,
        dow_labels=dow_labels,
        dow_gambling_sessions=dow_gambling_sessions,
        dow_gambling_wagered=dow_gambling_wagered,
        dow_drinking_sessions=dow_drinking_sessions,
        dow_drinking_drinks=dow_drinking_drinks,
        monthly_expense_total=monthly_expense_total,
        last_month_gambling_total=last_month_gambling_total,
        expense_vs_gambling_pct=expense_vs_gambling_pct,
        expense_vs_gambling_period_label=last_month_label,
        expense_vs_gambling_has_data=expense_vs_gambling_has_data,
        expense_vs_gambling_labels=json.dumps(["Expenses", "Gambling"]),
        expense_vs_gambling_values=json.dumps([monthly_expense_total, last_month_gambling_total]),
    )


@insights_bp.route("/insights")
def insights():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user or user.is_admin:
        return redirect(url_for("home"))

    return render_template("insights.html", **compute_insights(user_id))
