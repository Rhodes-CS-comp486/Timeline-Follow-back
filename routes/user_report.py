from flask import Blueprint, render_template, send_file, request, session, redirect, url_for
from csv_formatting.csv_creator import generate_user_csv_report, build_report_dataset
from database.db_initialization import StudyCode, User
from config.config_helper import get_header_label_map

user_report_bp = Blueprint('user_report', __name__)


def get_report_filters():
    return {
        "start_date": request.args.get('start_date', ''),
        "end_date": request.args.get('end_date', ''),
        "report_type": request.args.get('report_type', ''),
        "num_drinks": request.args.get('num_drinks', ''),
    }


def get_user_study_schema(user_id):
    user = User.query.get(user_id)
    if not user or not user.study_group_code:
        return None
    study = StudyCode.query.filter_by(code=user.study_group_code).first()
    if not study or not study.questions:
        return None
    if study.questions.get('drinking') or study.questions.get('gambling'):
        return study.questions
    return None


@user_report_bp.route('/report')
def report():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    filters = get_report_filters()
    show_table = str(request.args.get('show_table', '')).lower() in {"1", "true", "yes", "on"}

    report_headers = []
    report_rows = []
    study_schema = get_user_study_schema(user_id)
    if show_table:
        report_headers, report_rows = build_report_dataset(
            user_id=user_id,
            start_date=filters["start_date"],
            end_date=filters["end_date"],
            report_type=filters["report_type"] or None,
            num_drinks=filters["num_drinks"],
            schema=study_schema,
        )

    label_map = get_header_label_map(study_schema)
    report_header_labels = [
        label_map.get(h, h.replace('_', ' ').title()) for h in report_headers
    ]

    return render_template(
        'user_report.html',
        report_headers=report_headers,
        report_header_labels=report_header_labels,
        report_rows=report_rows,
        show_table=show_table,
        filters=filters,
    )


@user_report_bp.route('/download_report')
def download_report():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    filters = get_report_filters()

    file_path = generate_user_csv_report(
        user_id,
        filters["start_date"],
        filters["end_date"],
        filters["report_type"] or None,
        filters["num_drinks"],
        schema=get_user_study_schema(user_id),
    )
    return send_file(file_path, as_attachment=True)
