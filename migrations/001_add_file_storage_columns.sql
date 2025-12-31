-- Migration: Add file storage support for comments and check outputs
-- Date: 2025-12-31
-- Description: Adds columns to support storing large comments and check outputs in files
--              instead of truncating them in the database.

-- Add file_path and preview columns to comment table
ALTER TABLE comment ADD COLUMN file_path TEXT NULL;
ALTER TABLE comment ADD COLUMN preview TEXT NULL;

-- Add output_file_path column to checks table
ALTER TABLE checks ADD COLUMN output_file_path TEXT NULL;

-- Create indexes for better query performance
CREATE INDEX idx_comment_file_path ON comment(file_path);
CREATE INDEX idx_checks_output_file_path ON checks(output_file_path);
