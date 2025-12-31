# Database Migrations

This directory contains database migration scripts for the scoring engine.

## Running Migrations

### Option 1: SQL Script (Manual)

Run the SQL migration script directly on your database:

```bash
# For MySQL
mysql -u your_user -p your_database < migrations/001_add_file_storage_columns.sql

# For PostgreSQL
psql -U your_user -d your_database -f migrations/001_add_file_storage_columns.sql
```

### Option 2: Python Script (Automated)

Run the Python migration script:

```bash
# Run migration
python migrations/001_add_file_storage_columns.py

# Rollback migration (if needed)
python migrations/001_add_file_storage_columns.py rollback
```

## Migration 001: Add File Storage Columns

**Date:** 2025-12-31

**Description:**
Adds support for storing large comments and check outputs in files instead of truncating them in the database.

**Changes:**
- Adds `file_path` and `preview` columns to `comment` table
- Adds `output_file_path` column to `checks` table
- Creates indexes for better query performance

**Backward Compatibility:**
This migration is backward compatible. Existing comments and checks will continue to work without modification. New large comments/outputs will automatically use file storage.

## File Storage Configuration

After running the migration, ensure the `upload_folder` is configured in `engine.conf`:

```ini
[OPTIONS]
upload_folder = /var/uploads
```

Or set via environment variable:

```bash
export SCORINGENGINE_UPLOAD_FOLDER=/var/uploads
```

The file storage system will create subdirectories:
- `{upload_folder}/comments/{inject_id}/{team_name}/{comment_id}.txt`
- `{upload_folder}/checks/{round_id}/{service_id}_{check_id}.txt`

## Thresholds

File storage is automatically used when:
- Comments exceed 10,000 characters (10KB)
- Check outputs exceed 5,000 characters (5KB)

These thresholds can be adjusted in `scoring_engine/file_storage.py`:
- `COMMENT_FILE_STORAGE_THRESHOLD`
- `CHECK_OUTPUT_FILE_STORAGE_THRESHOLD`
