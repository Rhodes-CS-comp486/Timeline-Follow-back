import re
import secrets
import string

from flask import Blueprint, render_template, send_file, request, redirect, url_for, session, jsonify
from csv_formatting.csv_creator import generate_user_csv_report, generate_all_users_csv, build_report_dataset
from database.db_initialization import User, StudyCode, db
from routes.auth import admin_required
from routes.insights import compute_insights
from database.db_helper import get_gambling_aggregates
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)


def get_report_filters():
    # Shared filters used by table view and CSV export.
    return {
        "start_date": request.args.get('start_date', ''),
        "end_date": request.args.get('end_date', ''),
        "report_type": request.args.get('report_type', ''),
        "num_drinks": request.args.get('num_drinks', ''),
        "all_user_id": request.args.get('all_user_id', type=int),
    }


def generate_study_code():
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))


def _researcher_user_ids():
    """Return IDs of all non-admin users enrolled in the current researcher's studies."""
    researcher_id = session.get('user_id')
    codes = [
        sc.code for sc in
        StudyCode.query.filter_by(researcher_id=researcher_id).with_entities(StudyCode.code).all()
    ]
    if not codes:
        return []
    return [
        u.id for u in
        User.query.filter(User.is_admin.is_(False), User.study_group_code.in_(codes)).all()
    ]


def _parse_questions_from_form():
    """Extract ordered question lists for drinking and gambling from request.form."""
    updated = {}
    for section in ('drinking', 'gambling'):
        section_questions = []
        i = 0
        while True:
            label = request.form.get(f'{section}_{i}_label', '').strip()
            if not label:
                break
            q_id = request.form.get(f'{section}_{i}_id', '').strip()
            if not q_id:
                q_id = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')
                existing_ids = [q['id'] for q in section_questions]
                base, n = q_id, 1
                while q_id in existing_ids:
                    q_id = f'{base}_{n}'
                    n += 1
            q_type = request.form.get(f'{section}_{i}_type', 'number').strip()
            placeholder = request.form.get(f'{section}_{i}_placeholder', '').strip()
            options_raw = request.form.get(f'{section}_{i}_options', '').strip()
            q = {'id': q_id, 'label': label, 'type': q_type}
            if placeholder:
                q['placeholder'] = placeholder
            if q_type == 'select' and options_raw:
                q['options'] = [o.strip() for o in options_raw.splitlines() if o.strip()]
            min_val = request.form.get(f'{section}_{i}_min', '').strip()
            max_val = request.form.get(f'{section}_{i}_max', '').strip()
            if min_val != '':
                q['min'] = float(min_val)
            if max_val != '':
                q['max'] = float(max_val)
            section_questions.append(q)
            i += 1
        updated[section] = section_questions
    return updated


# ── Researcher Panel ─────────────────────────────────────────────────────────

@admin_bp.route('/researcher_panel')
@admin_required
def researcher_panel():
    return render_template('researcher_panel.html')


# ── Study CRUD ───────────────────────────────────────────────────────────────

@admin_bp.route('/studies')
@admin_required
def list_studies():
    researcher_id = session.get('user_id')
    studies = (StudyCode.query
               .filter_by(researcher_id=researcher_id)
               .order_by(StudyCode.created_at.desc())
               .all())
    return jsonify([{'id': s.id, 'code': s.code, 'title': s.title} for s in studies])


@admin_bp.route('/create_study', methods=['POST'])
@admin_required
def create_study():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    researcher_id = session.get('user_id')
    code = generate_study_code()
    while StudyCode.query.filter_by(code=code).first():
        code = generate_study_code()

    study = StudyCode(
        code=code,
        title=title,
        researcher_id=researcher_id,
        questions={'drinking': [], 'gambling': []},
    )
    db.session.add(study)
    db.session.commit()
    return jsonify({'id': study.id, 'code': study.code, 'title': study.title}), 201


@admin_bp.route('/delete_study/<int:study_id>', methods=['DELETE'])
@admin_required
def delete_study(study_id):
    researcher_id = session.get('user_id')
    study = StudyCode.query.filter_by(id=study_id, researcher_id=researcher_id).first()
    if not study:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(study)
    db.session.commit()
    return jsonify({'ok': True})


@admin_bp.route('/studies/<int:study_id>/questions', methods=['GET', 'POST'])
@admin_required
def study_questions(study_id):
    researcher_id = session.get('user_id')
    study = StudyCode.query.filter_by(id=study_id, researcher_id=researcher_id).first()
    if not study:
        return jsonify({'error': 'Not found'}), 404

    if request.method == 'GET':
        return jsonify(study.questions)

    study.questions = _parse_questions_from_form()
    db.session.commit()
    return jsonify({'ok': True})


# ── Insights ─────────────────────────────────────────────────────────────────

@admin_bp.route('/insights')
@admin_required
def insights():
    researcher_id = session.get('user_id')
    studies = (StudyCode.query
               .filter_by(researcher_id=researcher_id)
               .order_by(StudyCode.created_at.desc())
               .all())

    selected_study_id = request.args.get('study_id', type=int)
    selected_study = next((s for s in studies if s.id == selected_study_id), None)

    if selected_study:
        users = (User.query
                 .filter(User.is_admin.is_(False), User.study_group_code == selected_study.code)
                 .order_by(User.email)
                 .all())
        allowed_ids = {u.id for u in users}
    else:
        users = []
        allowed_ids = set()

    selected_user_id = request.args.get('user_id', type=int)
    selected_user = None
    insights_data = None

    if selected_user_id and selected_user_id in allowed_ids:
        selected_user = User.query.get(selected_user_id)
        if selected_user:
            insights_data = compute_insights(selected_user_id)

    return render_template(
        'admin_insights.html',
        users=users,
        selected_user=selected_user,
        insights_data=insights_data,
        studies=studies,
        selected_study=selected_study,
    )


# ── Reports ──────────────────────────────────────────────────────────────────

_EMPTY_AGGREGATES = {
    "user_count": 0, "total_intended": 0, "total_spent": 0,
    "total_hours": 0, "total_drinks": 0,
    "by_day": {d: 0 for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]},
}

@admin_bp.route('/report')
@admin_required
def report():
    researcher_id = session.get('user_id')
    studies = (StudyCode.query
               .filter_by(researcher_id=researcher_id)
               .order_by(StudyCode.created_at.desc())
               .all())

    selected_study_id = request.args.get('study_id', type=int)
    selected_study = next((s for s in studies if s.id == selected_study_id), None)

    if selected_study:
        users = (User.query
                 .filter(User.is_admin.is_(False), User.study_group_code == selected_study.code)
                 .all())
        allowed_ids = {u.id for u in users}
    else:
        users = []
        allowed_ids = set()

    filters = get_report_filters()
    show_table = str(request.args.get('show_table', '')).lower() in {"1", "true", "yes", "on"}

    scoped_user_id = filters["all_user_id"] if filters["all_user_id"] in allowed_ids else None

    report_headers = []
    report_rows = []
    if show_table and selected_study:
        report_headers, report_rows = build_report_dataset(
            user_id=scoped_user_id,
            user_ids=None if scoped_user_id else list(allowed_ids),
            start_date=filters["start_date"],
            end_date=filters["end_date"],
            report_type=filters["report_type"] or None,
            num_drinks=filters["num_drinks"],
        )

    aggregates = get_gambling_aggregates(
        start_date=filters["start_date"],
        end_date=filters["end_date"],
        user_id=scoped_user_id,
        user_ids=None if scoped_user_id else list(allowed_ids),
    ) if selected_study else _EMPTY_AGGREGATES

    return render_template(
        'report.html',
        users=users,
        report_headers=report_headers,
        report_rows=report_rows,
        show_table=show_table,
        filters=filters,
        aggregates=aggregates,
        now=datetime.today().date(),
        timedelta=timedelta,
        studies=studies,
        selected_study=selected_study,
    )


# ── CSV Downloads ────────────────────────────────────────────────────────────

@admin_bp.route('/download_report_user')
@admin_required
def download_report_user():
    allowed_ids = _researcher_user_ids()
    user_id = request.args.get('user_id', type=int)
    filters = get_report_filters()

    if not user_id or user_id not in allowed_ids:
        return "User not found or not in your studies", 400

    file_path = generate_user_csv_report(
        user_id,
        filters["start_date"],
        filters["end_date"],
        filters["report_type"] or None,
        filters["num_drinks"],
    )
    return send_file(file_path, as_attachment=True)


@admin_bp.route('/download_report_full')
@admin_required
def download_report_full():
    allowed_ids = _researcher_user_ids()
    filters = get_report_filters()

    scoped_user_id = filters["all_user_id"] if filters["all_user_id"] in allowed_ids else None

    file_path = generate_all_users_csv(
        start_date=filters["start_date"],
        end_date=filters["end_date"],
        report_type=filters["report_type"] or None,
        num_drinks=filters["num_drinks"],
        user_ids=[scoped_user_id] if scoped_user_id else allowed_ids,
    )
    return send_file(file_path, as_attachment=True)
