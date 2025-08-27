# AGENTS

This file contains guidelines for navigating and working with the repository.

## Repository structure
- `scoring_engine/`: core application code for the scoring engine.
- `tests/`: automated tests for the project.
- `docs/`: documentation source files.
- `configs/`: configuration samples and templates.
- `bin/`: helper scripts and entry points.

## Conventions
- Use `rg` (ripgrep) for searching across the repository instead of `grep -R`.
- Keep code style consistent with existing files and run `pre-commit run --files <files>` on modified files before committing.
- Write tests for new functionality and bug fixes, placing them under `tests/` mirroring the module structure. When a change cannot be reasonably tested, note this in the pull request.

## Testing
- Run `pytest` to execute the test suite.
- Use `pytest <path>` to run a subset of tests when working on a specific area.

## Additional notes
- Ensure documentation updates accompany code changes when relevant.
- Commits should be scoped and descriptive.
