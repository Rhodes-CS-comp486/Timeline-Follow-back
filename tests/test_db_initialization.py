"""Tests for database setup and model initialization."""
from datetime import datetime

import pytest
from sqlalchemy import inspect

from database.db_initialization import (
    Base,
    CalendarEntry,
    Drinking,
    Gambling,
    User,
    db,
)


class TestDbSetup:
    """Tests for database initialization and table creation."""

    def test_base_class_exists(self):
        """Base DeclarativeBase class should exist."""
        assert Base is not None

    def test_db_instance_exists(self):
        """SQLAlchemy db instance should exist."""
        assert db is not None

    def test_tables_created_in_app_context(self, app):
        """All expected tables should be created when db.create_all() runs."""
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

        expected_tables = {"user", "calendar_entry", "gambling", "drinking"}
        for table in expected_tables:
            assert table in tables, f"Expected table '{table}' not found in {tables}"


class TestUserModel:
    """Tests for User model."""

    def test_user_model_columns(self):
        """User model should have expected columns."""
        mapper = User.__mapper__
        column_names = [c.key for c in mapper.columns]
        expected = ["id", "password", "is_admin", "email"]
        for col in expected:
            assert col in column_names, f"User missing column: {col}"

    def test_user_can_be_created(self, app_context, app):
        """User can be instantiated and persisted."""
        user = User(
                email="test@example.com",
                password="hashed",
                is_admin=False,
            )
        db.session.add(user)
        db.session.commit()
        assert user.id is not None
        assert user.email == "test@example.com"


class TestCalendarEntryModel:
    """Tests for CalendarEntry model."""

    def test_calendar_entry_model_columns(self):
        """CalendarEntry model should have expected columns."""
        mapper = CalendarEntry.__mapper__
        column_names = [c.key for c in mapper.columns]
        expected = ["id", "user_id", "entry_date", "entry_type"]
        for col in expected:
            assert col in column_names, f"CalendarEntry missing column: {col}"

    def test_calendar_entry_requires_user_id(self, app_context, app):
        """CalendarEntry should link to user via user_id FK."""
        entry = CalendarEntry(user_id=1, entry_date=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()
        assert entry.id is not None
        assert entry.user_id == 1


class TestGamblingModel:
    """Tests for Gambling model."""

    def test_gambling_model_columns(self):
        """Gambling model should have expected columns."""
        mapper = Gambling.__mapper__
        column_names = [c.key for c in mapper.columns]
        expected = ["id", "entry_id", "user_id", "gambling_questions"]
        for col in expected:
            assert col in column_names, f"Gambling missing column: {col}"

    def test_gambling_questions_stores_json(self, app_context, app):
        """Gambling.gambling_questions should accept dict/JSON."""
        user = User(
                email="g@example.com",
                password="x",
                is_admin=False,
            )
        db.session.add(user)
        db.session.commit()

        entry = CalendarEntry(user_id=user.id, entry_date=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()

        data = {"amount": 100, "location": "casino"}
        gambling = Gambling(
            user_id=user.id,
            entry_id=entry.id,
            gambling_questions=data,
        )
        db.session.add(gambling)
        db.session.commit()
        assert gambling.gambling_questions == data


class TestDrinkingModel:
    """Tests for Drinking model."""

    def test_drinking_model_columns(self):
        """Drinking model should have expected columns."""
        mapper = Drinking.__mapper__
        column_names = [c.key for c in mapper.columns]
        expected = ["id", "entry_id", "user_id", "drinking_questions"]
        for col in expected:
            assert col in column_names, f"Drinking missing column: {col}"
