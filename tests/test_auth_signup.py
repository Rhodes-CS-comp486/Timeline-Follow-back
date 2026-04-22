"""Tests for account creation role and study code behavior."""
from pathlib import Path

from jinja2 import FileSystemLoader

from database.db_initialization import StudyCode, User, db
from routes.auth import auth_bp
from routes.instructions import instructions_bp


def _register_auth(app):
    app.jinja_loader = FileSystemLoader(str(Path(__file__).resolve().parents[1] / "templates"))
    if 'calendar' not in app.view_functions:
        app.add_url_rule('/calendar.html', endpoint='calendar', view_func=lambda: '')
    if 'instructions' not in app.blueprints:
        app.register_blueprint(instructions_bp)
    if 'auth' not in app.blueprints:
        app.register_blueprint(auth_bp)


def test_participant_signup_stores_valid_study_code(app):
    """Participant accounts should be linked to the entered study code."""
    _register_auth(app)

    with app.app_context():
        researcher = User(
            username="researcher@test.com",
            password="hashed",
            is_admin=True,
        )
        db.session.add(researcher)
        db.session.commit()

        study = StudyCode(
            code="abc12345",
            title="Alcohol Study",
            researcher_id=researcher.id,
            questions={'drinking': [], 'gambling': []},
        )
        db.session.add(study)
        db.session.commit()

    response = app.test_client().post('/create-account', data={
        'username': 'participant@test.com',
        'account_type': 'participant',
        'study_code': 'abc12345',
        'password': 'Password1!',
        'confirm_password': 'Password1!',
    })

    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(username="participant@test.com").first()
        assert user is not None
        assert user.is_admin is False
        assert user.study_group_code == "abc12345"


def test_researcher_signup_creates_admin_without_study_code(app):
    """Researcher accounts should map to is_admin=True."""
    _register_auth(app)

    response = app.test_client().post('/create-account', data={
        'username': 'new-researcher@test.com',
        'account_type': 'researcher',
        'study_code': '',
        'password': 'Password1!',
        'confirm_password': 'Password1!',
    })

    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(username="new-researcher@test.com").first()
        assert user is not None
        assert user.is_admin is True
        assert user.study_group_code is None


def test_participant_signup_rejects_unknown_study_code(app):
    """Participant accounts require a study code that exists."""
    _register_auth(app)

    response = app.test_client().post('/create-account', data={
        'username': 'missing-code@test.com',
        'account_type': 'participant',
        'study_code': 'missing1',
        'password': 'Password1!',
        'confirm_password': 'Password1!',
    })

    assert response.status_code == 200
    assert b"Study code was not found." in response.data
    with app.app_context():
        assert User.query.filter_by(username="missing-code@test.com").first() is None
