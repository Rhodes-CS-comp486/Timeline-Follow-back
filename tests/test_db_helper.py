"""Tests for database helper functions."""
from datetime import date, datetime

import pytest

from database.db_helper import (
    add_alcohol_entry,
    add_gambling_entry,
    commit_to_db,
    create_calendar_entry,
    create_user,
    get_calendar_entries_for_user,
)
from database.db_initialization import CalendarEntry, User, db


class TestCreateUser:
    """Tests for create_user helper."""

    def test_create_user_success(self, app_context, app):
        """create_user should create and persist a user."""
        with app.app_context():
            user = create_user(
                email="helper@test.com",
                first_name="Helper",
                last_name="User",
                password="secret",
                username="helperuser",
                is_admin=False,
            )
            assert user is not None
            assert user.id is not None
            assert user.email == "helper@test.com"
            assert user.username == "helperuser"

    def test_create_user_admin_flag(self, app_context, app):
        """create_user should respect is_admin parameter."""
        with app.app_context():
            admin = create_user(
                email="admin@test.com",
                first_name="Admin",
                last_name="User",
                password="secret",
                username="adminuser",
                is_admin=True,
            )
            assert admin is not None
            assert admin.is_admin is True


class TestCreateCalendarEntry:
    """Tests for create_calendar_entry helper."""

    def test_create_calendar_entry_success(self, app_context, app):
        """create_calendar_entry should create and persist an entry."""
        with app.app_context():
            user = create_user(
                email="cal@test.com",
                first_name="Cal",
                last_name="User",
                password="x",
                username="caluser",
            )
            assert user is not None

            entry = create_calendar_entry(user.id, datetime.utcnow())
            assert entry is not None
            assert entry.id is not None
            assert entry.user_id == user.id

    def test_create_calendar_entry_with_date_object(self, app_context, app):
        """create_calendar_entry should accept date object."""
        with app.app_context():
            user = create_user(
                email="cal2@test.com",
                first_name="Cal2",
                last_name="User",
                password="x",
                username="cal2user",
            )
            entry = create_calendar_entry(user.id, date(2025, 3, 20))
            assert entry is not None
            assert entry.user_id == user.id


class TestAddGamblingEntry:
    """Tests for add_gambling_entry helper."""

    def test_add_gambling_entry_success(self, app_context, app):
        """add_gambling_entry should create and persist a gambling entry."""
        with app.app_context():
            user = create_user(
                email="gamb@test.com",
                first_name="G",
                last_name="User",
                password="x",
                username="gambuser",
            )
            entry = create_calendar_entry(user.id, datetime.utcnow())
            activity_data = {"amount": 50, "type": "slots"}

            gambling = add_gambling_entry(user.id, entry.id, activity_data)
            assert gambling is not None
            assert gambling.id is not None
            assert gambling.gambling_questions == activity_data

    def test_add_gambling_entry_accepts_entry_object(self, app_context, app):
        """add_gambling_entry should accept entry object (with .id) or int."""
        with app.app_context():
            user = create_user(
                email="gamb2@test.com",
                first_name="G2",
                last_name="User",
                password="x",
                username="gamb2user",
            )
            entry = create_calendar_entry(user.id, datetime.utcnow())
            activity_data = {"amount": 10}

            gambling = add_gambling_entry(user.id, entry, activity_data)
            assert gambling is not None
            assert gambling.entry_id == entry.id


class TestAddAlcoholEntry:
    """Tests for add_alcohol_entry helper."""

    def test_add_alcohol_entry_success(self, app_context, app):
        """add_alcohol_entry should create and persist a drinking entry."""
        with app.app_context():
            user = create_user(
                email="drink@test.com",
                first_name="D",
                last_name="User",
                password="x",
                username="drinkuser",
            )
            entry = create_calendar_entry(user.id, datetime.utcnow())
            activity_data = {"drinks": 2, "type": "beer"}

            alcohol = add_alcohol_entry(user.id, entry.id, activity_data)
            assert alcohol is not None
            assert alcohol.id is not None
            assert alcohol.drinking_questions == activity_data

    def test_add_alcohol_entry_accepts_entry_object(self, app_context, app):
        """add_alcohol_entry should accept entry object or int."""
        with app.app_context():
            user = create_user(
                email="drink2@test.com",
                first_name="D2",
                last_name="User",
                password="x",
                username="drink2user",
            )
            entry = create_calendar_entry(user.id, datetime.utcnow())
            alcohol = add_alcohol_entry(user.id, entry, {"drinks": 1})
            assert alcohol is not None
            assert alcohol.entry_id == entry.id


class TestGetCalendarEntriesForUser:
    """Tests for get_calendar_entries_for_user helper."""

    def test_get_calendar_entries_empty(self, app_context, app):
        """get_calendar_entries_for_user returns empty list for user with no entries."""
        with app.app_context():
            user = create_user(
                email="empty@test.com",
                first_name="E",
                last_name="User",
                password="x",
                username="emptyuser",
            )
            entries = get_calendar_entries_for_user(user.id)
            assert entries == []

    def test_get_calendar_entries_returns_entries(self, app_context, app):
        """get_calendar_entries_for_user returns entries ordered by date."""
        with app.app_context():
            user = create_user(
                email="multi@test.com",
                first_name="M",
                last_name="User",
                password="x",
                username="multiuser",
            )
            create_calendar_entry(user.id, datetime(2025, 3, 1))
            create_calendar_entry(user.id, datetime(2025, 3, 15))
            create_calendar_entry(user.id, datetime(2025, 3, 10))

            entries = get_calendar_entries_for_user(user.id)
            assert len(entries) == 3
            dates = [e.entry_date for e in entries]
            assert dates == sorted(dates)

    def test_get_calendar_entries_filters_by_user(self, app_context, app):
        """get_calendar_entries_for_user only returns entries for that user."""
        with app.app_context():
            user1 = create_user(
                email="u1@test.com",
                first_name="U1",
                last_name="User",
                password="x",
                username="user1",
            )
            user2 = create_user(
                email="u2@test.com",
                first_name="U2",
                last_name="User",
                password="x",
                username="user2",
            )
            create_calendar_entry(user1.id, datetime.utcnow())
            create_calendar_entry(user2.id, datetime.utcnow())

            entries1 = get_calendar_entries_for_user(user1.id)
            entries2 = get_calendar_entries_for_user(user2.id)
            assert len(entries1) == 1
            assert len(entries2) == 1
            assert entries1[0].user_id == user1.id
            assert entries2[0].user_id == user2.id


class TestCommitToDb:
    """Tests for commit_to_db helper."""

    def test_commit_to_db_success(self, app_context, app):
        """commit_to_db should persist valid model and return it."""
        with app.app_context():
            user = User(
                email="commit@test.com",
                first_name="C",
                last_name="User",
                password="x",
                username="commituser",
                is_admin=False,
            )
            result = commit_to_db(user)
            assert result is not None
            assert result.id is not None

    def test_commit_to_db_rollback_on_error(self, app_context, app):
        """commit_to_db should rollback and return None on constraint violation."""
        with app.app_context():
            user1 = create_user(
                email="dup@test.com",
                first_name="Dup",
                last_name="User",
                password="x",
                username="dupuser",
            )
            assert user1 is not None

            # Duplicate username should fail (unique constraint)
            user2 = User(
                email="dup2@test.com",
                first_name="Dup2",
                last_name="User",
                password="x",
                username="dupuser",
                is_admin=False,
            )
            result = commit_to_db(user2)
            assert result is None
