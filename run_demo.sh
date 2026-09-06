#!/bin/sh
# Smoke test: run every fixture issue through the pipeline (in --mock mode,
# so it works offline) and compare the classify verdict against
# fixtures/issues/expected.json.
set -e

cd "$(dirname "$0")"

ISSUES_DIR="fixtures/issues"
EXPECTED_FILE="$ISSUES_DIR/expected.json"

PASS_COUNT=0
FAIL_COUNT=0

for issue_file in "$ISSUES_DIR"/*.md; do
    issue_id=$(basename "$issue_file" .md)

    python3 -m slopshield run "$issue_file" --mock >/tmp/slopshield_demo_output.log 2>&1 || true

    actual=$(python3 -c "import json; print(json.load(open('out/$issue_id/verdict.json'))['verdict'])" 2>/dev/null || echo "ERROR")
    expected=$(python3 -c "import json; print(json.load(open('$EXPECTED_FILE'))['$issue_id'])" 2>/dev/null || echo "MISSING")

    if [ "$actual" = "$expected" ]; then
        echo "PASS  $issue_id (verdict=$actual)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "FAIL  $issue_id (expected=$expected, actual=$actual)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        cat /tmp/slopshield_demo_output.log
    fi
done

echo ""
echo "Summary: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
