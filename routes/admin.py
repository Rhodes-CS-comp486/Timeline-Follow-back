from flask import Blueprint, render_template, send_file, request
from csv_formatting.csv_creator import generate_user_csv_report, generate_all_users_csv
from database.db_initialization import User
from routes.auth import admin_required

admin_bp = Blueprint('admin', __name__)

# This function loads the report tab
# Parameters: N/A
# Returns: The rendered report.html file
@admin_bp.route('/report')
@admin_required
def report():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('report.html', users=users)

# This function downloads the csv file for all users
# Parameters: N/A
# Returns: cvs file to be downloaded sent to device
@admin_bp.route('/download_report_user')
@admin_required
def download_report_user():
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not user_id:
        return "Missing user_id", 400

    file_path = generate_user_csv_report(user_id, start_date, end_date)
    return send_file(file_path, as_attachment=True)

# This function downloads the csv file for a single users
# Parameters: N/A
# Returns: cvs file to be downloaded sent to device
@admin_bp.route('/download_report_full')
@admin_required
def download_report_full():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    file_path = generate_all_users_csv(start_date, end_date)
    return send_file(file_path, as_attachment=True)