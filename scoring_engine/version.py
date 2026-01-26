import os
import subprocess

from scoring_engine.config import config

# Base version - updated by bump-my-version
BASE_VERSION = "1.2.0"


def get_git_info():
    """
    Get git commit hash and tag information.
    Returns tuple of (commit_hash, is_tagged_release, tag_name).
    """
    commit_hash = None
    is_tagged_release = False
    tag_name = None

    # First check environment variable (set by Makefile/Docker)
    if "SCORINGENGINE_VERSION" in os.environ:
        env_version = os.environ["SCORINGENGINE_VERSION"]
        # If it looks like a version tag (v1.2.0), it's a release
        if env_version.startswith("v") and "." in env_version:
            is_tagged_release = True
            tag_name = env_version
        else:
            # Otherwise treat as commit hash
            commit_hash = env_version
        return commit_hash, is_tagged_release, tag_name

    # Try to get git info directly
    try:
        # Get current commit hash
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            commit_hash = result.stdout.strip()

        # Check if current commit has a version tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            if tag.startswith("v") and "." in tag:
                is_tagged_release = True
                tag_name = tag
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, Exception):
        # Git not available, not in a git repo, or running in restricted environment
        # (e.g., Celery worker with soft time limits)
        pass

    return commit_hash, is_tagged_release, tag_name


def get_version_info():
    """
    Get comprehensive version information.
    Returns dict with version details.
    """
    commit_hash, is_tagged_release, tag_name = get_git_info()

    info = {
        "base_version": BASE_VERSION,
        "commit": commit_hash,
        "is_release": is_tagged_release,
        "tag": tag_name,
        "is_dev": config.debug,
    }

    # Build the display version string
    if is_tagged_release:
        # Tagged release: just show version
        display = BASE_VERSION
    elif commit_hash:
        # Development build with commit: show version+commit
        display = f"{BASE_VERSION}+{commit_hash}"
    else:
        # No git info available: just show base version
        display = BASE_VERSION

    if config.debug:
        display += "-dev"

    info["display"] = display
    return info


def get_version():
    """Get the display version string for backwards compatibility."""
    return get_version_info()["display"]


# For backwards compatibility
version = get_version()
version_info = get_version_info()
