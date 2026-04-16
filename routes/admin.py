from flask import Blueprint, render_template, send_file, request, redirect, url_for
from csv_formatting.csv_creator import generate_user_csv_report, generate_all_users_csv, build_report_dataset
from database.db_initialization import User
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

@admin_bp.route('/researcher_panel', methods=['GET', 'POST'])
@admin_required
def researcher_panel():
    import json, os, re
    questions_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'questions.json')

    if request.method == 'POST':
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
        with open(questions_path, 'w') as f:
            json.dump(updated, f, indent=2)
        return redirect(url_for('admin.researcher_panel', saved=1))

    with open(questions_path) as f:
        questions = json.load(f)
    saved = request.args.get('saved')
    return render_template('researcher_panel.html', questions=questions, saved=saved)


@admin_bp.route('/insights')
@admin_required
def insights():
    users = User.query.filter_by(is_admin=False).order_by(User.email).all()
    selected_user_id = request.args.get('user_id', type=int)
    selected_user = None
    insights_data = None

    if selected_user_id:
        selected_user = User.query.get(selected_user_id)
        if selected_user and not selected_user.is_admin:
            insights_data = compute_insights(selected_user_id)

    return render_template(
        'admin_insights.html',
        users=users,
        selected_user=selected_user,
        insights_data=insights_data,
    )


# This function loads the report tab
# Parameters: N/A
# Returns: The rendered report.html file
@admin_bp.route('/report')
@admin_required
def report():
    users = User.query.filter_by(is_admin=False).all()
    filters = get_report_filters()
    show_table = str(request.args.get('show_table', '')).lower() in {"1", "true", "yes", "on"}

    report_headers = []
    report_rows = []
    if show_table:
        report_headers, report_rows = build_report_dataset(
            user_id=filters["all_user_id"],
            start_date=filters["start_date"],
            end_date=filters["end_date"],
            report_type=filters["report_type"] or None,
            num_drinks=filters["num_drinks"],
        )

    aggregates = get_gambling_aggregates(
        start_date=filters["start_date"],
        end_date=filters["end_date"],
        user_id=filters["all_user_id"],
    )

    return render_template(
        'report.html',
        users=users,
        report_headers=report_headers,
        report_rows=report_rows,
        show_table=show_table,
        filters=filters,
        aggregates=aggregates,
        now=datetime.today(),
        timedelta=timedelta,
    )

# This function downloads the csv file for a single user
# Parameters: N/A
# Returns: cvs file to be downloaded sent to device
@admin_bp.route('/download_report_user')
@admin_required
def download_report_user():
    user_id = request.args.get('user_id', type=int)
    filters = get_report_filters()

    if not user_id:
        return "Missing user_id", 400

    file_path = generate_user_csv_report(
        user_id,
        filters["start_date"],
        filters["end_date"],
        filters["report_type"] or None,
        filters["num_drinks"],
    )
    return send_file(file_path, as_attachment=True)

# This function downloads the csv file for all users
# Parameters: N/A
# Returns: cvs file to be downloaded sent to device
@admin_bp.route('/download_report_full')
@admin_required
def download_report_full():
    filters = get_report_filters()

    # Use named args so user_ids maps to the correct parameter.
    file_path = generate_all_users_csv(
        start_date=filters["start_date"],
        end_date=filters["end_date"],
        report_type=filters["report_type"] or None,
        num_drinks=filters["num_drinks"],
        user_ids=[filters["all_user_id"]] if filters["all_user_id"] else None,
    )
    return send_file(file_path, as_attachment=True)
