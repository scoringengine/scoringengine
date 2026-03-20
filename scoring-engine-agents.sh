#!/usr/bin/env bash
# scoring-engine-agents.sh
# Multi-agent orchestration for the Scoring Engine project via Claude Code CLI
#
# Usage:
#   ./scoring-engine-agents.sh "Add LDAP service check support"
#   ./scoring-engine-agents.sh --phase architect "Add LDAP service check support"
#   ./scoring-engine-agents.sh --phase implement --design design.md
#   ./scoring-engine-agents.sh --phase review --design design.md
#
# Prerequisites:
#   - Claude Code CLI installed and authenticated
#   - Run from the scoringengine project root

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
ARTIFACTS_DIR="${PROJECT_ROOT}/.agents"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "${ARTIFACTS_DIR}"

# --- Defaults ---
PHASE="all"
DESIGN_FILE=""
REQUIREMENT=""

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --phase)
      PHASE="$2"
      shift 2
      ;;
    --design)
      DESIGN_FILE="$2"
      shift 2
      ;;
    *)
      REQUIREMENT="$*"
      break
      ;;
  esac
done

if [[ -z "$REQUIREMENT" && -z "$DESIGN_FILE" ]]; then
  echo "Usage: $0 [--phase architect|implement|review|all] [--design file.md] <requirement>"
  exit 1
fi

# ============================================================================
# PHASE 1: ARCHITECT
# ============================================================================
run_architect() {
  local req="$1"
  local output="${ARTIFACTS_DIR}/design_${TIMESTAMP}.md"

  echo "═══════════════════════════════════════════════════════════"
  echo "  PHASE 1: ARCHITECT"
  echo "  Requirement: ${req:0:80}..."
  echo "═══════════════════════════════════════════════════════════"

  claude -p "You are the Architect agent for the Scoring Engine CCDC project.

Read CLAUDE.md for full project context.

Analyze this requirement and produce a detailed design document.
Do NOT write any implementation code.

REQUIREMENT:
${req}

Your output MUST include these sections:

## 1. Affected Files
List every file that needs to change with specific functions/classes impacted.

## 2. Data Model Changes
New or modified SQLAlchemy models, migrations needed.

## 3. API/Route Changes
New or modified Flask routes, API endpoints, request/response schemas.

## 4. Check Changes
If service checks are affected, detail the check class changes.

## 5. Celery/Worker Impact
Changes to task scheduling, round execution, worker configuration.

## 6. Configuration Impact
Changes to engine.conf.inc, config_loader, or sample configs.

## 7. Cache Invalidation
Redis cache keys that need updating or busting.

## 8. Interface Contracts
Function signatures, return types, error handling approach.

## 9. Test Strategy
Tests to write or update, edge cases, fixtures needed.

## 10. Risk Assessment
What could break, backwards compatibility, migration path.

Be specific and reference existing patterns in the codebase." > "$output"

  echo ""
  echo "✓ Design document saved to: ${output}"
  echo ""

  # Return the path for chaining
  echo "$output"
}

# ============================================================================
# PHASE 2: IMPLEMENT
# ============================================================================
run_implement() {
  local design_file="$1"
  local design_content
  design_content=$(cat "$design_file")

  echo "═══════════════════════════════════════════════════════════"
  echo "  PHASE 2: IMPLEMENT"
  echo "  Design doc: ${design_file}"
  echo "═══════════════════════════════════════════════════════════"

  claude -p "You are an Implementer agent for the Scoring Engine CCDC project.

Read CLAUDE.md for full project context.

Here is the Architect's design document:

${design_content}

Implement ALL changes described in the design document.

Rules:
- Follow existing code patterns and style (check neighboring files first)
- Every new function/method must have a docstring
- Add type hints to all new function signatures
- Service check classes must inherit from the base check class
- SQLAlchemy models must include proper relationships and repr methods
- Flask routes must include proper error handling and return JSON for API endpoints
- All Celery tasks must be idempotent
- Run pre-commit on changed files
- Run pytest on related test files

When done, output:
1. List of all files created or modified
2. Summary of changes per file
3. Any concerns or deviations from the design doc
4. Any new dependencies added"

  echo ""
  echo "✓ Implementation complete"
  echo ""
}

# ============================================================================
# PHASE 3: REVIEW
# ============================================================================
run_review() {
  local design_file="$1"
  local design_content
  design_content=$(cat "$design_file")
  local output="${ARTIFACTS_DIR}/review_${TIMESTAMP}.md"

  echo "═══════════════════════════════════════════════════════════"
  echo "  PHASE 3: REVIEW"
  echo "  Design doc: ${design_file}"
  echo "═══════════════════════════════════════════════════════════"

  claude -p "You are the Reviewer agent for the Scoring Engine CCDC project.

Read CLAUDE.md for full project context.

Here is the Architect's design document:

${design_content}

Review the current state of the codebase against the design. Run these checks:

CODE QUALITY:
- Follows existing patterns in the codebase
- Type hints on all new function signatures
- Docstrings on all new functions/methods/classes
- No hardcoded values that should be configurable
- Proper error handling (no bare excepts)
- SQLAlchemy sessions properly managed
- Redis cache operations have proper TTLs

CORRECTNESS:
- Implementation matches the design doc
- Edge cases handled (empty data, missing config, network timeouts)
- Service checks handle connection failures gracefully
- Celery tasks are idempotent
- No race conditions in scoring / concurrent checks

SECURITY:
- No SQL injection vectors
- Auth enforced on new routes
- No credential exposure in logs or API responses
- Input validation on all user-facing endpoints

TESTING:
- Run: pytest
- Run: pre-commit run --all-files
- Verify new code has test coverage
- Write any missing tests

Output:
1. PASS/FAIL verdict with reasoning
2. Blocking issues vs non-blocking suggestions
3. Any tests you wrote
4. Specific fix instructions for blocking issues" > "$output"

  echo ""
  echo "✓ Review saved to: ${output}"
  cat "$output"
  echo ""
}

# ============================================================================
# ORCHESTRATE
# ============================================================================
case "$PHASE" in
  architect)
    run_architect "$REQUIREMENT"
    ;;
  implement)
    if [[ -z "$DESIGN_FILE" ]]; then
      echo "Error: --design <file> required for implement phase"
      exit 1
    fi
    run_implement "$DESIGN_FILE"
    ;;
  review)
    if [[ -z "$DESIGN_FILE" ]]; then
      echo "Error: --design <file> required for review phase"
      exit 1
    fi
    run_review "$DESIGN_FILE"
    ;;
  all)
    echo "Running full pipeline: Architect → Implement → Review"
    echo ""

    # Architect
    design_path=$(run_architect "$REQUIREMENT" | tail -1)

    # Implement
    run_implement "$design_path"

    # Review
    run_review "$design_path"

    echo "═══════════════════════════════════════════════════════════"
    echo "  PIPELINE COMPLETE"
    echo "  Design:  ${design_path}"
    echo "  Review:  ${ARTIFACTS_DIR}/review_${TIMESTAMP}.md"
    echo "═══════════════════════════════════════════════════════════"
    ;;
  *)
    echo "Unknown phase: $PHASE"
    echo "Valid phases: architect, implement, review, all"
    exit 1
    ;;
esac
