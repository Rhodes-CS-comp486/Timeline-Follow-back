"""Pytest fixtures for database tests. Uses in-memory SQLite for isolation."""
import pytest
from flask import Flask

from database.db_initialization import db

'''
    To run all test cases use the following command:
            python -m pytest tests/ -v
'''

@pytest.fixture
def app():
    """Create a minimal Flask app with in-memory SQLite for testing."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["TESTING"] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_context(app):
    """Provide an active application context for tests."""
    with app.app_context():
        yield
