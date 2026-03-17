from flask import Blueprint, render_template, send_file, request, session, redirect, url_for
from csv_formatting.csv_creator import generate_user_csv_report, build_report_dataset

user_report_bp = Blueprint('user_report', __name__)


def get_report_filters():
    return {
        "start_date": request.args.get('start_date', ''),
        "end_date": request.args.get('end_date', ''),
        "report_type": request.args.get('report_type', ''),
        "num_drinks": request.args.get('num_drinks', ''),
    }


@user_report_bp.route('/report')
def report():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    filters = get_report_filters()
    show_table = str(request.args.get('show_table', '')).lower() in {"1", "true", "yes", "on"}

    report_headers = []
    report_rows = []
    if show_table:
        report_headers, report_rows = build_report_dataset(
            user_id=user_id,
            start_date=filters["start_date"],
            end_date=filters["end_date"],
            report_type=filters["report_type"] or None,
            num_drinks=filters["num_drinks"],
        )

    return render_template(
        'user_report.html',
        report_headers=report_headers,
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
    )
    return send_file(file_path, as_attachment=True)
