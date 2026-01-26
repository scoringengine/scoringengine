#!/usr/bin/env python3
"""
Test script to verify session isolation with multiple concurrent users.
Tests that Flask-SQLAlchemy properly isolates sessions between requests.
"""

import requests
from requests.auth import HTTPBasicAuth
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import sys

# Disable SSL warnings for testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://localhost:8000"

class UserSession:
    """Represents a logged-in user session."""

    def __init__(self, username, password, session_id):
        self.username = username
        self.password = password
        self.session_id = session_id
        self.session = requests.Session()
        self.errors = []

    def login(self):
        """Log in and establish session."""
        try:
            # First get the login page to get CSRF token
            resp = self.session.get(f"{BASE_URL}/login", verify=False)
            if resp.status_code != 200:
                self.errors.append(f"[{self.username}] Failed to get login page: {resp.status_code}")
                return False

            # Try to log in (adjust fields based on your login form)
            data = {
                'username': self.username,
                'password': self.password,
            }
            resp = self.session.post(f"{BASE_URL}/login", data=data, verify=False, allow_redirects=False)

            if resp.status_code not in (200, 302):
                self.errors.append(f"[{self.username}] Login failed: {resp.status_code}")
                return False

            print(f"✓ [{self.username}] Logged in successfully (session {self.session_id})")
            return True
        except Exception as e:
            self.errors.append(f"[{self.username}] Login exception: {e}")
            return False

    def fetch_profile(self):
        """Fetch user profile data."""
        try:
            resp = self.session.get(f"{BASE_URL}/api/profile", verify=False)
            if resp.status_code == 200:
                data = resp.json()
                # Verify we got our own user data, not someone else's
                if 'username' in data and data['username'] != self.username:
                    self.errors.append(
                        f"[{self.username}] DATA LEAK! Got {data['username']}'s profile!"
                    )
                    return None
                print(f"✓ [{self.username}] Profile fetch OK: team={data.get('team', {}).get('name', 'Unknown')}")
                return data
            else:
                self.errors.append(f"[{self.username}] Profile fetch failed: {resp.status_code}")
                return None
        except Exception as e:
            self.errors.append(f"[{self.username}] Profile exception: {e}")
            return None

    def fetch_overview(self):
        """Fetch overview page."""
        try:
            resp = self.session.get(f"{BASE_URL}/api/overview", verify=False)
            if resp.status_code == 200:
                print(f"✓ [{self.username}] Overview fetch OK")
                return resp.json()
            else:
                self.errors.append(f"[{self.username}] Overview fetch failed: {resp.status_code}")
                return None
        except Exception as e:
            self.errors.append(f"[{self.username}] Overview exception: {e}")
            return None

    def perform_actions(self, num_iterations=5):
        """Perform multiple actions to test session stability."""
        if not self.login():
            return

        for i in range(num_iterations):
            time.sleep(0.1)  # Small delay between requests
            self.fetch_profile()
            time.sleep(0.1)
            self.fetch_overview()

        print(f"✓ [{self.username}] Completed {num_iterations} iterations")


def test_concurrent_users(users, num_iterations=5):
    """
    Test multiple users making concurrent requests.

    Args:
        users: List of (username, password) tuples
        num_iterations: Number of request cycles per user
    """
    print(f"\n{'='*60}")
    print(f"Testing {len(users)} concurrent users with {num_iterations} iterations each")
    print(f"{'='*60}\n")

    sessions = []
    for i, (username, password) in enumerate(users):
        sessions.append(UserSession(username, password, i+1))

    # Run all users concurrently
    with ThreadPoolExecutor(max_workers=len(users)) as executor:
        futures = [
            executor.submit(session.perform_actions, num_iterations)
            for session in sessions
        ]

        # Wait for all to complete
        for future in futures:
            future.result()

    # Check for errors
    print(f"\n{'='*60}")
    print("Results:")
    print(f"{'='*60}\n")

    total_errors = 0
    for session in sessions:
        if session.errors:
            print(f"✗ [{session.username}] Had {len(session.errors)} errors:")
            for error in session.errors:
                print(f"  - {error}")
            total_errors += len(session.errors)
        else:
            print(f"✓ [{session.username}] No errors")

    print(f"\n{'='*60}")
    if total_errors == 0:
        print("✓ ALL TESTS PASSED - No session isolation issues detected!")
    else:
        print(f"✗ TESTS FAILED - {total_errors} errors detected")
        sys.exit(1)
    print(f"{'='*60}\n")


def check_server():
    """Check if the server is running."""
    try:
        resp = requests.get(BASE_URL, verify=False, timeout=2)
        return True
    except:
        return False


if __name__ == "__main__":
    # Check if server is running
    if not check_server():
        print(f"✗ Server not reachable at {BASE_URL}")
        print("  Start the server with: python bin/web")
        sys.exit(1)

    print(f"✓ Server is reachable at {BASE_URL}")

    # Define test users (adjust these to match your setup)
    # You'll need to have these users already created in your database
    test_users = [
        ("team1_user", "password"),
        ("team2_user", "password"),
        ("team3_user", "password"),
    ]

    print("\nNOTE: Make sure these test users exist in your database:")
    for username, _ in test_users:
        print(f"  - {username}")

    input("\nPress Enter to start the test...")

    # Run the test
    test_concurrent_users(test_users, num_iterations=10)
