from flask import Blueprint, render_template, send_file, request
from csv_formatting.csv_creator import generate_user_csv_report, generate_all_users_csv, build_report_dataset
from database.db_initialization import User
from routes.auth import admin_required

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

# This function loads the report tab
# Parameters: N/A
# Returns: The rendered report.html file
@admin_bp.route('/report')
@admin_required
def report():
    users = User.query.filter_by(is_admin=False).all()
    filters = get_report_filters()
    # Load table rows only after explicit user action.
    show_table = str(request.args.get('show_table', '')).lower() in {"1", "true", "yes", "on"}

    report_headers = []
    report_rows = []
    if show_table:
        # Build on-screen rows from the same filter logic as CSV.
        report_headers, report_rows = build_report_dataset(
            user_id=filters["all_user_id"],
            start_date=filters["start_date"],
            end_date=filters["end_date"],
            report_type=filters["report_type"] or None,
            num_drinks=filters["num_drinks"],
        )

    return render_template(
        'report.html',
        users=users,
        report_headers=report_headers,
        report_rows=report_rows,
        show_table=show_table,
        filters=filters,
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
