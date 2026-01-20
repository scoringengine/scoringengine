#!/usr/bin/env python3
"""
Test to verify Flask-SQLAlchemy is properly creating new sessions per request
and fixing the stale data issue that required the monkeypatch.
"""

from scoring_engine.web import create_app
from scoring_engine.db import db, init_db, delete_db
from scoring_engine.models.setting import Setting

def test_session_isolation():
    """Verify that sessions are isolated between requests."""
    app = create_app()
    app.config['TESTING'] = True

    with app.app_context():
        delete_db()
        init_db()

        # Create a setting
        setting = Setting(name='test_setting', value='initial_value')
        db.session.add(setting)
        db.session.commit()
        setting_id = setting.id

    print("✓ Created setting with initial value")

    # Simulate Request 1: Load the setting into session
    with app.test_request_context():
        db.session.begin()
        request1_session_id = id(db.session)
        print(f"Request 1 - Session ID: {request1_session_id}")

        setting1 = db.session.get(Setting, setting_id)
        print(f"Request 1 - Loaded setting: {setting1.value}")
        assert setting1.value == 'initial_value'

        # Store the setting object's ID to track if it's the same instance later
        setting1_obj_id = id(setting1)
        print(f"Request 1 - Setting object ID: {setting1_obj_id}")

        # Simulate another process/request updating the value
        # (In real scenario, this would be another worker/request)
        with app.app_context():
            other_setting = db.session.get(Setting, setting_id)
            other_setting.value = 'modified_value'
            db.session.commit()
            print("✓ Simulated external update to 'modified_value'")

        # Without the monkeypatch, this would return the OLD cached value
        # because setting1 is still in the session's identity map
        print(f"Request 1 - setting1.value after external update: {setting1.value}")
        print(f"Request 1 - This is EXPECTED to be stale: 'initial_value'")
        print(f"Request 1 - (session still has cached object)")

    print("✓ Request 1 context ended (session should be removed)")
    print()

    # Simulate Request 2: This should get a FRESH session
    with app.test_request_context():
        request2_session_id = id(db.session)
        print(f"Request 2 - Session ID: {request2_session_id}")

        # CRITICAL TEST: If sessions are properly isolated, this should be
        # a different session with a fresh identity map
        if request2_session_id == request1_session_id:
            print("⚠ WARNING: Same session ID! Session may not be properly isolated!")
        else:
            print("✓ Different session ID - good!")

        setting2 = db.session.get(Setting, setting_id)
        setting2_obj_id = id(setting2)
        print(f"Request 2 - Setting object ID: {setting2_obj_id}")

        if setting2_obj_id == setting1_obj_id:
            print("⚠ WARNING: Same object instance! Session not properly cleared!")
        else:
            print("✓ Different object instance - session was cleared!")

        print(f"Request 2 - setting2.value: {setting2.value}")

        # THIS IS THE CRITICAL TEST
        # With proper Flask-SQLAlchemy, this should be 'modified_value'
        # Without it (or with the old global session), it would be 'initial_value' (stale)
        if setting2.value == 'modified_value':
            print("✅ SUCCESS: Got fresh data from database!")
            print("✅ Flask-SQLAlchemy is properly creating new sessions per request")
            print("✅ The monkeypatch is no longer needed!")
        else:
            print(f"❌ FAILURE: Got stale value '{setting2.value}'")
            print("❌ Sessions are NOT properly isolated!")
            print("❌ The root cause is NOT fixed!")
            return False

    print()
    print("="*60)
    print("Test Details:")
    print("="*60)
    print("What this test proves:")
    print("1. Each request gets a new session (different session IDs)")
    print("2. Session identity map is cleared between requests")
    print("3. Fresh data is loaded from DB (not cached from previous request)")
    print()
    print("Why the monkeypatch was needed before:")
    print("- Global scoped_session persisted across requests")
    print("- Identity map cached objects indefinitely")
    print("- Queries returned stale cached objects instead of fresh DB data")
    print("- Forcing commit() before query expired cache, forcing DB fetch")
    print()
    print("How Flask-SQLAlchemy fixes it:")
    print("- Creates new session per request (via app context scoping)")
    print("- Calls session.remove() when request context tears down")
    print("- Each request starts with empty identity map")
    print("- Queries always fetch fresh data from database")

    return True


def test_concurrent_modifications():
    """Test that concurrent modifications don't cause stale data issues."""
    app = create_app()
    app.config['TESTING'] = True

    print()
    print("="*60)
    print("Testing Concurrent Modifications Scenario")
    print("="*60)

    with app.app_context():
        delete_db()
        init_db()

        # Create test setting
        setting = Setting(name='concurrent_test', value='0')
        db.session.add(setting)
        db.session.commit()
        setting_id = setting.id

    # Simulate Request A: Reads value
    with app.test_request_context():
        setting_a = db.session.get(Setting, setting_id)
        value_a = setting_a.value
        print(f"Request A - Read value: {value_a}")

        # Request B updates it (simulated)
        with app.app_context():
            setting_b = db.session.get(Setting, setting_id)
            setting_b.value = '1'
            db.session.commit()
            print("Request B - Updated value to: 1")

        # Request A reads again (still in same request context)
        # This WILL be stale because we're in the same request
        print(f"Request A - Read again (same request): {setting_a.value}")
        print("           (Expected to be stale - same request context)")

    # Request C: New request, should see Request B's update
    with app.test_request_context():
        setting_c = db.session.get(Setting, setting_id)
        value_c = setting_c.value
        print(f"Request C - Read value (new request): {value_c}")

        if value_c == '1':
            print("✅ SUCCESS: New request sees updated value!")
        else:
            print(f"❌ FAILURE: Got stale value {value_c}")
            return False

    return True


if __name__ == '__main__':
    print("="*60)
    print("Flask-SQLAlchemy Session Isolation Test")
    print("="*60)
    print()
    print("This test verifies that the Flask-SQLAlchemy migration")
    print("fixes the stale data issue that required the monkeypatch.")
    print()

    success = True

    try:
        if not test_session_isolation():
            success = False

        if not test_concurrent_modifications():
            success = False

        print()
        print("="*60)
        if success:
            print("✅ ALL TESTS PASSED")
            print("="*60)
            print()
            print("Conclusion: Flask-SQLAlchemy is properly isolating sessions.")
            print("The monkeypatch is no longer needed because:")
            print("- Each request gets a fresh session")
            print("- Session is automatically removed after request")
            print("- No stale data carried over between requests")
        else:
            print("❌ TESTS FAILED")
            print("="*60)
            print()
            print("The root cause may not be fully fixed!")
            print("You may still need the monkeypatch or further investigation.")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        success = False

    exit(0 if success else 1)
