from sqlalchemy import Column, Integer, ForeignKey, Boolean, Text, DateTime, UnicodeText
from sqlalchemy.orm import relationship

from datetime import datetime
import pytz

import html

from scoring_engine.models.base import Base
from scoring_engine.config import config


class Check(Base):
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('rounds.id'))
    round = relationship('Round', back_populates='checks')
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship('Service')
    result = Column(Boolean)
    output = Column(UnicodeText, default="")
    output_file_path = Column(Text, nullable=True)  # Path to file if output is stored on disk
    reason = Column(Text, default="")
    command = Column(Text, default="")
    completed_timestamp = Column(DateTime)
    completed = Column(Boolean, default=False)

    def finished(self, result, reason, output, command):
        """Mark check as finished and store the output.

        If output is large, it will be stored in a file with a preview in the database.
        Otherwise, it's stored directly in the database.

        Parameters
        ----------
        result : bool
            Check result (True for success, False for failure)
        reason : str
            Reason for the check result
        output : str
            Check output (can be large)
        command : str
            Command that was executed
        """
        from scoring_engine.file_storage import (
            should_use_file_storage_for_check_output,
            save_check_output_to_file
        )

        self.result = result
        self.reason = reason
        self.command = command
        self.completed = True
        self.completed_timestamp = datetime.utcnow()

        # Decide whether to store in file or database
        if should_use_file_storage_for_check_output(output):
            # Store in file, keep preview in database
            file_path, preview = save_check_output_to_file(
                self.id, self.round_id, self.service_id, output
            )
            self.output_file_path = file_path
            self.output = html.escape(preview)
        else:
            # Store in database
            self.output = html.escape(output)
            self.output_file_path = None

    def get_full_output(self):
        """Get the full check output, loading from file if necessary.

        Returns
        -------
        str
            Full check output (HTML escaped)
        """
        if self.output_file_path:
            from scoring_engine.file_storage import load_check_output_from_file
            content = load_check_output_from_file(self.output_file_path, self.id)
            if content is not None:
                return html.escape(content)
        return self.output

    @property
    def is_output_in_file(self):
        """Check if output is stored in a file.

        Returns
        -------
        bool
            True if output is stored in file, False otherwise
        """
        return self.output_file_path is not None

    @property
    def local_completed_timestamp(self):
        completed_timezone_obj = pytz.timezone('UTC').localize(self.completed_timestamp)
        return completed_timezone_obj.astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z')
