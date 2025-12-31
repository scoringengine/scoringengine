"""Helper module for storing and retrieving large text content in files.

This module provides functions to save large comments and check outputs to disk
instead of the database, with integrated caching for optimal performance.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple

from scoring_engine.cache import cache
from scoring_engine.config import config


logger = logging.getLogger(__name__)


# Cache timeout for file content (1 hour)
FILE_CONTENT_CACHE_TIMEOUT = 3600

# Thresholds for when to use file storage vs database
COMMENT_FILE_STORAGE_THRESHOLD = 10000  # Store comments >10KB in files
CHECK_OUTPUT_FILE_STORAGE_THRESHOLD = 5000  # Store check outputs >5KB in files

# Preview lengths stored in database for quick access
COMMENT_PREVIEW_LENGTH = 500
CHECK_OUTPUT_PREVIEW_LENGTH = 2000


def _ensure_directory(directory_path: str) -> None:
    """Ensure a directory exists, creating it if necessary.

    Parameters
    ----------
    directory_path : str
        Path to the directory to create
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def _get_cache_key(entity_type: str, entity_id: int, team_id: Optional[int] = None) -> str:
    """Generate a cache key for file content.

    Parameters
    ----------
    entity_type : str
        Type of entity ('comment' or 'check')
    entity_id : int
        ID of the entity
    team_id : int, optional
        Team ID for team-specific caching

    Returns
    -------
    str
        Cache key
    """
    if team_id:
        return f"file_content_{entity_type}_{entity_id}_{team_id}"
    return f"file_content_{entity_type}_{entity_id}"


def save_comment_to_file(comment_id: int, inject_id: int, team_name: str, content: str) -> Tuple[str, str]:
    """Save a comment to a file and return the file path and preview.

    Parameters
    ----------
    comment_id : int
        ID of the comment
    inject_id : int
        ID of the inject this comment belongs to
    team_name : str
        Name of the team
    content : str
        Full comment text

    Returns
    -------
    tuple
        (file_path, preview) where file_path is the relative path and preview is the first N chars
    """
    # Create directory structure: {upload_folder}/comments/{inject_id}/{team_name}/
    directory = os.path.join(config.upload_folder, "comments", str(inject_id), team_name)
    _ensure_directory(directory)

    # File path: {directory}/{comment_id}.txt
    filename = f"{comment_id}.txt"
    file_path = os.path.join(directory, filename)

    # Write content to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved comment {comment_id} to file: {file_path}")
    except Exception as e:
        logger.error(f"Error saving comment {comment_id} to file: {e}")
        raise

    # Generate preview
    preview = content[:COMMENT_PREVIEW_LENGTH] if len(content) > COMMENT_PREVIEW_LENGTH else content

    # Return relative path from upload_folder
    relative_path = os.path.join("comments", str(inject_id), team_name, filename)

    return relative_path, preview


def save_check_output_to_file(check_id: int, round_id: int, service_id: int, output: str) -> Tuple[str, str]:
    """Save check output to a file and return the file path and preview.

    Parameters
    ----------
    check_id : int
        ID of the check
    round_id : int
        ID of the round
    service_id : int
        ID of the service
    output : str
        Full check output

    Returns
    -------
    tuple
        (file_path, preview) where file_path is the relative path and preview is the first N chars
    """
    # Create directory structure: {upload_folder}/checks/{round_id}/
    directory = os.path.join(config.upload_folder, "checks", str(round_id))
    _ensure_directory(directory)

    # File path: {directory}/{service_id}_{check_id}.txt
    filename = f"{service_id}_{check_id}.txt"
    file_path = os.path.join(directory, filename)

    # Write content to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"Saved check output {check_id} to file: {file_path}")
    except Exception as e:
        logger.error(f"Error saving check output {check_id} to file: {e}")
        raise

    # Generate preview (keep first N chars in DB for quick display)
    preview = output[:CHECK_OUTPUT_PREVIEW_LENGTH] if len(output) > CHECK_OUTPUT_PREVIEW_LENGTH else output

    # Return relative path from upload_folder
    relative_path = os.path.join("checks", str(round_id), filename)

    return relative_path, preview


def load_comment_from_file(file_path: str, comment_id: int, team_id: Optional[int] = None) -> Optional[str]:
    """Load comment content from a file with caching.

    Parameters
    ----------
    file_path : str
        Relative path to the comment file
    comment_id : int
        ID of the comment
    team_id : int, optional
        Team ID for caching

    Returns
    -------
    str or None
        Comment content, or None if file doesn't exist
    """
    # Check cache first
    cache_key = _get_cache_key("comment", comment_id, team_id)
    cached_content = cache.get(cache_key)
    if cached_content is not None:
        return cached_content

    # Load from file
    full_path = os.path.join(config.upload_folder, file_path)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Cache the content
        cache.set(cache_key, content, timeout=FILE_CONTENT_CACHE_TIMEOUT)

        return content
    except FileNotFoundError:
        logger.warning(f"Comment file not found: {full_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading comment from file {full_path}: {e}")
        return None


def load_check_output_from_file(file_path: str, check_id: int) -> Optional[str]:
    """Load check output from a file with caching.

    Parameters
    ----------
    file_path : str
        Relative path to the check output file
    check_id : int
        ID of the check

    Returns
    -------
    str or None
        Check output content, or None if file doesn't exist
    """
    # Check cache first
    cache_key = _get_cache_key("check", check_id)
    cached_content = cache.get(cache_key)
    if cached_content is not None:
        return cached_content

    # Load from file
    full_path = os.path.join(config.upload_folder, file_path)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Cache the content
        cache.set(cache_key, content, timeout=FILE_CONTENT_CACHE_TIMEOUT)

        return content
    except FileNotFoundError:
        logger.warning(f"Check output file not found: {full_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading check output from file {full_path}: {e}")
        return None


def delete_comment_file(file_path: str, comment_id: int, team_id: Optional[int] = None) -> bool:
    """Delete a comment file and clear its cache.

    Parameters
    ----------
    file_path : str
        Relative path to the comment file
    comment_id : int
        ID of the comment
    team_id : int, optional
        Team ID for cache clearing

    Returns
    -------
    bool
        True if file was deleted, False otherwise
    """
    if not file_path:
        return False

    # Clear cache
    cache_key = _get_cache_key("comment", comment_id, team_id)
    cache.delete(cache_key)

    # Delete file
    full_path = os.path.join(config.upload_folder, file_path)

    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Deleted comment file: {full_path}")
            return True
    except Exception as e:
        logger.error(f"Error deleting comment file {full_path}: {e}")

    return False


def delete_check_output_file(file_path: str, check_id: int) -> bool:
    """Delete a check output file and clear its cache.

    Parameters
    ----------
    file_path : str
        Relative path to the check output file
    check_id : int
        ID of the check

    Returns
    -------
    bool
        True if file was deleted, False otherwise
    """
    if not file_path:
        return False

    # Clear cache
    cache_key = _get_cache_key("check", check_id)
    cache.delete(cache_key)

    # Delete file
    full_path = os.path.join(config.upload_folder, file_path)

    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Deleted check output file: {full_path}")
            return True
    except Exception as e:
        logger.error(f"Error deleting check output file {full_path}: {e}")

    return False


def should_use_file_storage_for_comment(content: str) -> bool:
    """Determine if a comment should be stored in a file.

    Parameters
    ----------
    content : str
        Comment content

    Returns
    -------
    bool
        True if content should be stored in file, False for database
    """
    return len(content) > COMMENT_FILE_STORAGE_THRESHOLD


def should_use_file_storage_for_check_output(output: str) -> bool:
    """Determine if check output should be stored in a file.

    Parameters
    ----------
    output : str
        Check output

    Returns
    -------
    bool
        True if output should be stored in file, False for database
    """
    return len(output) > CHECK_OUTPUT_FILE_STORAGE_THRESHOLD
