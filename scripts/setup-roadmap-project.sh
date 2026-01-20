#!/bin/bash
# Setup script for GitHub Project board with Phase 1 roadmap issues
# Prerequisites: gh CLI installed and authenticated (gh auth login)

set -e

REPO="scoringengine/scoringengine"

echo "Creating GitHub issues for Phase 1 roadmap items..."

# Database & Data Management
gh issue create --repo "$REPO" \
  --title "Implement database migrations with Alembic" \
  --label "enhancement,database" \
  --body "$(cat <<'EOF'
## Overview
Add database migration support using Alembic/Flask-Migrate to enable schema changes without data loss.

## Tasks
- [ ] Add Flask-Migrate integration
- [ ] Create initial migration from current schema
- [ ] Document migration workflow for production deployments
- [ ] Test migration process with existing databases

## Acceptance Criteria
- Schema changes can be applied incrementally
- Rollback capability for failed migrations
- Clear documentation for operators

## References
- ROADMAP.md Phase 1: Database & Data Management
EOF
)"

gh issue create --repo "$REPO" \
  --title "Optimize database query performance" \
  --label "enhancement,performance,database" \
  --body "$(cat <<'EOF'
## Overview
Address remaining database query performance issues identified in the codebase.

## Tasks
- [ ] Audit and fix remaining N+1 query issues in API endpoints
- [ ] Implement query result caching for expensive operations
- [ ] Add database query logging for performance monitoring
- [ ] Review and optimize team ranking calculations

## Areas to Review
- `scoring_engine/web/views/api/` - Multiple endpoints have query issues
- Team ranking calculation queries
- Stats API subquery optimization

## References
- ROADMAP.md Phase 1: Database & Data Management
- Related PRs: #1052, #1053, #1054, #1055
EOF
)"

# Code Quality & Testing
gh issue create --repo "$REPO" \
  --title "Increase test coverage to 90%+" \
  --label "enhancement,testing" \
  --body "$(cat <<'EOF'
## Overview
Improve test coverage across the codebase to ensure reliability and catch regressions.

## Tasks
- [ ] Add missing unit tests for web views
- [ ] Expand model test coverage
- [ ] Add API endpoint integration tests
- [ ] Document testing best practices
- [ ] Set up coverage thresholds in CI

## Current State
- Some web views lack test coverage
- API endpoints need integration tests
- Test patterns need documentation

## References
- ROADMAP.md Phase 1: Code Quality & Testing
- Related PR: #1059
EOF
)"

gh issue create --repo "$REPO" \
  --title "Clean up technical debt" \
  --label "enhancement,tech-debt" \
  --body "$(cat <<'EOF'
## Overview
Address known technical debt items identified in the codebase.

## Tasks
- [ ] Remove development hacks in agent API caching (use real Flask-Caching)
- [ ] Fix type handling for JavaScript select values in admin API
- [ ] Implement proper validation for inject comment length (25K limit)
- [ ] Resolve HTML embedding in API responses
- [ ] Fix hacky datetime initialization in competition.py

## Files to Review
- `scoring_engine/web/views/api/agent.py` - Cache hack
- `scoring_engine/web/views/api/admin.py` - Type handling
- `scoring_engine/web/views/api/injects.py` - Comment validation
- `scoring_engine/web/views/api/overview.py` - HTML in API responses
- `scoring_engine/competition.py` - Datetime initialization

## References
- ROADMAP.md Phase 1: Code Quality & Testing
EOF
)"

# Documentation
gh issue create --repo "$REPO" \
  --title "Create operations guide" \
  --label "documentation" \
  --body "$(cat <<'EOF'
## Overview
Create comprehensive operations documentation for competition administrators.

## Tasks
- [ ] Performance tuning recommendations
- [ ] Backup and disaster recovery procedures
- [ ] Troubleshooting common issues guide
- [ ] Monitoring and alerting setup guide

## Deliverables
- `docs/source/operations/` directory with RST files
- Integration with existing Sphinx documentation

## References
- ROADMAP.md Phase 1: Documentation
EOF
)"

gh issue create --repo "$REPO" \
  --title "Improve check documentation" \
  --label "documentation" \
  --body "$(cat <<'EOF'
## Overview
Improve documentation for all service checks to help competition designers.

## Tasks
- [ ] Document all 31 check types with examples
- [ ] Provide competition.yaml templates for common scenarios
- [ ] Create check development tutorial
- [ ] Add troubleshooting tips per check type

## Deliverables
- Updated `docs/source/checks/` with complete documentation
- Example competition.yaml files in `configs/`
- Check development guide

## References
- ROADMAP.md Phase 1: Documentation
EOF
)"

echo ""
echo "Issues created successfully!"
echo ""
echo "Creating GitHub Project board..."

# Create project board
PROJECT_URL=$(gh project create --owner scoringengine --title "Scoring Engine Roadmap" --format json | jq -r '.url')

echo "Project created: $PROJECT_URL"
echo ""
echo "To add issues to the project, run:"
echo "  gh project item-add <PROJECT_NUMBER> --owner scoringengine --url <ISSUE_URL>"
echo ""
echo "Or manually add them via the GitHub web interface."
