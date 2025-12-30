import pytest
from datetime import datetime

from scoring_engine.models.notifications import Notification
from scoring_engine.models.team import Team

from tests.scoring_engine.unit_test import UnitTest


class TestNotification(UnitTest):

    def test_init_minimal(self):
        """Test creating a notification with minimal fields"""
        notification = Notification()
        assert notification.id is None
        assert notification.message is None
        assert notification.target is None
        # Default is applied by database on commit

    def test_init_with_message(self):
        """Test creating a notification with a message"""
        notification = Notification()
        notification.message = "System maintenance scheduled for tonight"
        notification.target = "all"
        assert notification.message == "System maintenance scheduled for tonight"
        assert notification.target == "all"
        # Default is applied by database on commit

    def test_simple_save(self):
        """Test saving a notification to the database"""
        notification = Notification()
        notification.message = "Test notification"
        notification.target = "all"
        self.session.add(notification)
        self.session.commit()
        assert notification.id is not None
        assert len(self.session.query(Notification).all()) == 1

    def test_default_is_read(self):
        """Test that is_read defaults to False after commit"""
        notification = Notification()
        notification.message = "Test"
        self.session.add(notification)
        self.session.commit()
        # Database applies default after commit
        assert notification.is_read is False

    def test_default_created_timestamp(self):
        """Test that created timestamp is automatically set"""
        notification = Notification()
        notification.message = "Test"
        self.session.add(notification)
        self.session.commit()
        assert notification.created is not None
        assert isinstance(notification.created, datetime)

    def test_mark_as_read(self):
        """Test marking a notification as read"""
        notification = Notification()
        notification.message = "Test notification"
        notification.target = "blue_team"
        self.session.add(notification)
        self.session.commit()

        assert notification.is_read is False
        notification.is_read = True
        self.session.commit()
        assert notification.is_read is True

    def test_notification_with_team(self):
        """Test creating a notification associated with a team"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        notification = Notification()
        notification.message = "Your service is down"
        notification.target = "team_specific"
        notification.team_id = team.id
        self.session.add(notification)
        self.session.commit()

        assert notification.team_id == team.id
        assert notification.id is not None

    def test_multiple_notifications(self):
        """Test creating multiple notifications"""
        notification1 = Notification()
        notification1.message = "First notification"
        notification1.target = "all"

        notification2 = Notification()
        notification2.message = "Second notification"
        notification2.target = "blue_team"

        notification3 = Notification()
        notification3.message = "Third notification"
        notification3.target = "white_team"

        self.session.add(notification1)
        self.session.add(notification2)
        self.session.add(notification3)
        self.session.commit()

        notifications = self.session.query(Notification).all()
        assert len(notifications) == 3

    def test_notification_ordering_by_created(self):
        """Test that notifications can be ordered by created timestamp"""
        notification1 = Notification()
        notification1.message = "First"
        notification1.target = "all"
        self.session.add(notification1)
        self.session.commit()

        notification2 = Notification()
        notification2.message = "Second"
        notification2.target = "all"
        self.session.add(notification2)
        self.session.commit()

        notifications = self.session.query(Notification).order_by(Notification.created).all()
        assert len(notifications) == 2
        assert notifications[0].message == "First"
        assert notifications[1].message == "Second"

    def test_filter_unread_notifications(self):
        """Test filtering unread notifications"""
        notification1 = Notification()
        notification1.message = "Unread notification"
        notification1.is_read = False
        self.session.add(notification1)

        notification2 = Notification()
        notification2.message = "Read notification"
        notification2.is_read = True
        self.session.add(notification2)

        self.session.commit()

        unread = self.session.query(Notification).filter_by(is_read=False).all()
        assert len(unread) == 1
        assert unread[0].message == "Unread notification"

    def test_unicode_message(self):
        """Test that notifications can contain unicode characters"""
        notification = Notification()
        notification.message = "Competition starts in 30 minutes! 🚀"
        notification.target = "all"
        self.session.add(notification)
        self.session.commit()

        retrieved = self.session.query(Notification).first()
        assert "🚀" in retrieved.message

    def test_long_message(self):
        """Test that notifications can contain long messages"""
        long_message = "This is a very long notification message. " * 50
        notification = Notification()
        notification.message = long_message
        notification.target = "all"
        self.session.add(notification)
        self.session.commit()

        retrieved = self.session.query(Notification).first()
        assert len(retrieved.message) > 100

    def test_target_types(self):
        """Test various target types for notifications"""
        targets = ["all", "blue_team", "white_team", "red_team", "team_1", "administrators"]

        for target in targets:
            notification = Notification()
            notification.message = f"Message for {target}"
            notification.target = target
            self.session.add(notification)

        self.session.commit()

        notifications = self.session.query(Notification).all()
        assert len(notifications) == len(targets)

        for notification in notifications:
            assert notification.target in targets

    def test_delete_notification(self):
        """Test deleting a notification"""
        notification = Notification()
        notification.message = "To be deleted"
        notification.target = "all"
        self.session.add(notification)
        self.session.commit()

        notification_id = notification.id
        assert self.session.query(Notification).filter_by(id=notification_id).first() is not None

        self.session.delete(notification)
        self.session.commit()

        assert self.session.query(Notification).filter_by(id=notification_id).first() is None

    def test_update_notification(self):
        """Test updating a notification message"""
        notification = Notification()
        notification.message = "Original message"
        notification.target = "all"
        self.session.add(notification)
        self.session.commit()

        notification.message = "Updated message"
        self.session.commit()

        retrieved = self.session.query(Notification).first()
        assert retrieved.message == "Updated message"
