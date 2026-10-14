#!/bin/bash
# UI Redesign Scope Guard
# Fails if changes touch frozen areas (API, data, core map)

set -e

CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || echo "")

if [ -z "$CHANGED_FILES" ]; then
  echo "✅ No staged changes to check"
  exit 0
fi

VIOLATIONS=""

# Check for API changes
if echo "$CHANGED_FILES" | grep -q "^api/"; then
  VIOLATIONS="$VIOLATIONS\n❌ API changes detected (frozen by steering file)"
fi

# Check for data changes
if echo "$CHANGED_FILES" | grep -q "^data/"; then
  VIOLATIONS="$VIOLATIONS\n❌ Data directory changes detected (frozen)"
fi

# Check for cache changes
if echo "$CHANGED_FILES" | grep -q "^cache/"; then
  VIOLATIONS="$VIOLATIONS\n❌ Cache changes detected (frozen)"
fi

# Check for API types
if echo "$CHANGED_FILES" | grep -q "api.*schemas.py"; then
  VIOLATIONS="$VIOLATIONS\n❌ API schema changes detected (frozen)"
fi

if [ -n "$VIOLATIONS" ]; then
  echo -e "\n🚫 UI SCOPE VIOLATION"
  echo -e "$VIOLATIONS"
  echo -e "\nThe UI redesign must not touch:"
  echo "  - api/ directory (routes, logic, schemas)"
  echo "  - data/ directory (fixtures)"
  echo "  - cache/ directory (computed results)"
  echo ""
  echo "If you need API changes, document them in docs/ui-open-questions.md"
  exit 1
fi

echo "✅ UI scope check passed"
exit 0
