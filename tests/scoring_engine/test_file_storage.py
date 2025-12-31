"""Tests for file storage functionality."""

import os
import tempfile
import shutil
from pathlib import Path

from scoring_engine import file_storage
from scoring_engine.models.check import Check
from scoring_engine.models.inject import Comment
from scoring_engine.models.round import Round
from scoring_engine.config import config

from tests.scoring_engine.helpers import generate_sample_model_tree
from tests.scoring_engine.unit_test import UnitTest


class TestFileStorage(UnitTest):
    """Test file storage functions."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create temporary upload folder for tests
        self.test_upload_folder = tempfile.mkdtemp()
        self.original_upload_folder = config.upload_folder
        config.upload_folder = self.test_upload_folder

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original upload folder
        config.upload_folder = self.original_upload_folder
        # Remove temporary folder
        if os.path.exists(self.test_upload_folder):
            shutil.rmtree(self.test_upload_folder)
        super().tearDown()

    def test_small_comment_stored_in_database(self):
        """Test that small comments are stored in the database."""
        small_comment = "This is a small comment"
        assert not file_storage.should_use_file_storage_for_comment(small_comment)

    def test_large_comment_uses_file_storage(self):
        """Test that large comments trigger file storage."""
        large_comment = "A" * (file_storage.COMMENT_FILE_STORAGE_THRESHOLD + 1)
        assert file_storage.should_use_file_storage_for_comment(large_comment)

    def test_save_and_load_comment(self):
        """Test saving and loading a comment from file."""
        comment_id = 123
        inject_id = 456
        team_name = "TestTeam"
        content = "This is a test comment that will be saved to a file" * 500

        # Save comment
        file_path, preview = file_storage.save_comment_to_file(
            comment_id, inject_id, team_name, content
        )

        # Verify file exists
        full_path = os.path.join(config.upload_folder, file_path)
        assert os.path.exists(full_path)

        # Verify preview is correct length
        assert len(preview) <= file_storage.COMMENT_PREVIEW_LENGTH

        # Load comment
        loaded_content = file_storage.load_comment_from_file(file_path, comment_id)
        assert loaded_content == content

    def test_small_check_output_stored_in_database(self):
        """Test that small check outputs are stored in the database."""
        small_output = "Success"
        assert not file_storage.should_use_file_storage_for_check_output(small_output)

    def test_large_check_output_uses_file_storage(self):
        """Test that large check outputs trigger file storage."""
        large_output = "B" * (file_storage.CHECK_OUTPUT_FILE_STORAGE_THRESHOLD + 1)
        assert file_storage.should_use_file_storage_for_check_output(large_output)

    def test_save_and_load_check_output(self):
        """Test saving and loading check output from file."""
        check_id = 789
        round_id = 10
        service_id = 20
        output = "This is check output\n" * 1000

        # Save output
        file_path, preview = file_storage.save_check_output_to_file(
            check_id, round_id, service_id, output
        )

        # Verify file exists
        full_path = os.path.join(config.upload_folder, file_path)
        assert os.path.exists(full_path)

        # Verify preview is correct length
        assert len(preview) <= file_storage.CHECK_OUTPUT_PREVIEW_LENGTH

        # Load output
        loaded_output = file_storage.load_check_output_from_file(file_path, check_id)
        assert loaded_output == output

    def test_delete_comment_file(self):
        """Test deleting a comment file."""
        comment_id = 111
        inject_id = 222
        team_name = "TeamA"
        content = "Comment to be deleted" * 100

        # Save comment
        file_path, _ = file_storage.save_comment_to_file(
            comment_id, inject_id, team_name, content
        )

        full_path = os.path.join(config.upload_folder, file_path)
        assert os.path.exists(full_path)

        # Delete comment file
        result = file_storage.delete_comment_file(file_path, comment_id)
        assert result is True
        assert not os.path.exists(full_path)

    def test_delete_check_output_file(self):
        """Test deleting a check output file."""
        check_id = 333
        round_id = 5
        service_id = 15
        output = "Output to be deleted\n" * 500

        # Save output
        file_path, _ = file_storage.save_check_output_to_file(
            check_id, round_id, service_id, output
        )

        full_path = os.path.join(config.upload_folder, file_path)
        assert os.path.exists(full_path)

        # Delete output file
        result = file_storage.delete_check_output_file(file_path, check_id)
        assert result is True
        assert not os.path.exists(full_path)


class TestCheckModelWithFileStorage(UnitTest):
    """Test Check model with file storage integration."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create temporary upload folder for tests
        self.test_upload_folder = tempfile.mkdtemp()
        self.original_upload_folder = config.upload_folder
        config.upload_folder = self.test_upload_folder

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original upload folder
        config.upload_folder = self.original_upload_folder
        # Remove temporary folder
        if os.path.exists(self.test_upload_folder):
            shutil.rmtree(self.test_upload_folder)
        super().tearDown()

    def test_check_small_output_in_database(self):
        """Test that small check outputs are stored in database."""
        service = generate_sample_model_tree('Service', self.session)
        round_obj = Round(number=1)
        self.session.add(round_obj)
        check = Check(round=round_obj, service=service)
        self.session.add(check)
        self.session.commit()

        small_output = "Success"
        check.finished(True, 'Test passed', small_output, 'test command')

        assert check.output_file_path is None
        assert not check.is_output_in_file
        assert check.output == small_output

    def test_check_large_output_in_file(self):
        """Test that large check outputs are stored in file."""
        service = generate_sample_model_tree('Service', self.session)
        round_obj = Round(number=1)
        self.session.add(round_obj)
        check = Check(round=round_obj, service=service)
        self.session.add(check)
        self.session.commit()

        large_output = "X" * (file_storage.CHECK_OUTPUT_FILE_STORAGE_THRESHOLD + 100)
        check.finished(True, 'Test passed', large_output, 'test command')

        assert check.output_file_path is not None
        assert check.is_output_in_file
        # Output should contain preview, not full output
        assert len(check.output) < len(large_output)
        # Full output should be retrievable
        full_output = check.get_full_output()
        # HTML escape adds characters, so we check the length is at least as long
        assert len(full_output) >= len(large_output)


class TestCommentModelWithFileStorage(UnitTest):
    """Test Comment model with file storage integration."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create temporary upload folder for tests
        self.test_upload_folder = tempfile.mkdtemp()
        self.original_upload_folder = config.upload_folder
        config.upload_folder = self.test_upload_folder

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original upload folder
        config.upload_folder = self.original_upload_folder
        # Remove temporary folder
        if os.path.exists(self.test_upload_folder):
            shutil.rmtree(self.test_upload_folder)
        super().tearDown()

    def test_comment_get_full_comment_from_database(self):
        """Test getting full comment when stored in database."""
        inject = generate_sample_model_tree('Inject', self.session)
        user = inject.team.users[0]

        comment_text = "This is a regular comment"
        comment = Comment(comment_text, user, inject)
        self.session.add(comment)
        self.session.commit()

        assert comment.get_full_comment() == comment_text
        assert not comment.is_stored_in_file

    def test_comment_get_full_comment_from_file(self):
        """Test getting full comment when stored in file."""
        inject = generate_sample_model_tree('Inject', self.session)
        user = inject.team.users[0]

        large_comment = "A" * (file_storage.COMMENT_FILE_STORAGE_THRESHOLD + 100)

        # Simulate file storage
        comment = Comment("", user, inject)
        self.session.add(comment)
        self.session.flush()

        file_path, preview = file_storage.save_comment_to_file(
            comment.id, inject.id, user.team.name, large_comment
        )
        comment.comment = preview
        comment.file_path = file_path
        comment.preview = preview
        self.session.commit()

        assert comment.is_stored_in_file
        full_comment = comment.get_full_comment()
        assert full_comment == large_comment
