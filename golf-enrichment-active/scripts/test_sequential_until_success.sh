#!/bin/bash
#
# Sequential Course Testing Until Target Success Rate
#
# Tests NC courses one at a time until we find enough successful enrichments.
# Stops early when target is reached to avoid unnecessary API costs.
#
# Target: 20 successful courses (for 80-90% success rate testing)
# Max tests: 50 courses
#
# Usage: ./test_sequential_until_success.sh
#

set -e

# Configuration
TARGET_SUCCESS=20
MAX_TESTS=50
API_URL="http://localhost:8001/enrich-course"
RESULTS_DIR="results/docker/sequential_test"
SUPABASE_PROJECT_ID="oadmysogtfopkbmrulmq"

# Counters
TESTED=0
SUCCESSFUL=0
FAILED=0

# Create results directory
mkdir -p "$RESULTS_DIR"

# Initialize summary file
SUMMARY_FILE="$RESULTS_DIR/summary.json"
echo "{\"started_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"courses\": []}" > "$SUMMARY_FILE"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================="
echo "Sequential NC Course Testing - Find $TARGET_SUCCESS Successful Courses"
echo "======================================================================="
echo ""
echo "Target: $TARGET_SUCCESS successful enrichments"
echo "Max tests: $MAX_TESTS courses"
echo "API: $API_URL"
echo ""

# Query Supabase for NC courses (get more than we need)
echo "Fetching NC courses from Supabase..."
COURSES_JSON=$(python3 << 'PYTHON_SCRIPT'
import os
import sys

# Add SDK to path
sys.path.insert(0, '/Users/stevemcmillian/llama-3-agents/Apps/projects/claude-agent-sdk-python/src')

try:
    from claude_agent_sdk._internal.mcp.client import MCPClient
    import json
    import asyncio

    async def get_courses():
        async with MCPClient() as client:
            # Get Supabase MCP tools
            tools = await client.list_tools()
            execute_sql = None
            for tool in tools:
                if tool.name == "mcp__supabase__execute_sql":
                    execute_sql = tool
                    break

            if not execute_sql:
                print("ERROR: Supabase MCP tool not found", file=sys.stderr)
                return []

            # Query for NC courses with websites
            query = """
                SELECT course_name, state_code, website, city
                FROM golf_courses
                WHERE state_code = 'NC'
                  AND website IS NOT NULL
                  AND website != ''
                  AND website NOT LIKE '%facebook%'
                ORDER BY course_name
                LIMIT 60
            """

            result = await client.call_tool(
                execute_sql.name,
                {"project_id": "oadmysogtfopkbmrulmq", "query": query}
            )

            # Parse result
            if result and len(result) > 0:
                import re
                # Extract JSON from result text
                text = result[0].text if hasattr(result[0], 'text') else str(result[0])
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    courses = json.loads(match.group(0))
                    return courses

            return []

    courses = asyncio.run(get_courses())
    print(json.dumps(courses))

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    print("[]")
PYTHON_SCRIPT
)

if [ "$COURSES_JSON" = "[]" ] || [ -z "$COURSES_JSON" ]; then
    echo "ERROR: Failed to fetch courses from Supabase"
    exit 1
fi

echo "Found $(echo "$COURSES_JSON" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))") courses in database"
echo ""

# Test each course sequentially
echo "Starting sequential testing..."
echo ""

echo "$COURSES_JSON" | python3 -c "
import sys
import json
courses = json.load(sys.stdin)
for i, course in enumerate(courses):
    print(f'{i}|{course[\"course_name\"]}|{course[\"website\"]}|{course.get(\"city\", \"\")}')
" | while IFS='|' read -r INDEX COURSE_NAME WEBSITE CITY; do

    # Check if we've hit our targets
    if [ $SUCCESSFUL -ge $TARGET_SUCCESS ]; then
        echo ""
        echo -e "${GREEN}✅ Target reached: $SUCCESSFUL/$TARGET_SUCCESS successful courses found!${NC}"
        break
    fi

    if [ $TESTED -ge $MAX_TESTS ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Max tests reached: $MAX_TESTS courses tested${NC}"
        break
    fi

    # Increment counter
    TESTED=$((TESTED + 1))

    # Extract domain from website
    DOMAIN=$(echo "$WEBSITE" | sed -E 's|https?://||' | sed -E 's|www\.||' | cut -d'/' -f1)

    # Print test header
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Test $TESTED/$MAX_TESTS: $COURSE_NAME"
    echo "Domain: $DOMAIN"
    echo "Progress: $SUCCESSFUL/$TARGET_SUCCESS successful | $FAILED failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Test course
    RESPONSE=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"course_name\": \"$COURSE_NAME\",
            \"state_code\": \"NC\",
            \"domain\": \"$DOMAIN\",
            \"use_test_tables\": true
        }")

    # Save result
    RESULT_FILE="$RESULTS_DIR/test_$(printf "%03d" $TESTED)_$(echo "$COURSE_NAME" | tr ' ' '_' | tr '[:upper:]' '[:lower:]').json"
    echo "$RESPONSE" | python3 -m json.tool > "$RESULT_FILE"

    # Parse result
    SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r.get('success', False))" 2>/dev/null || echo "False")
    CONTACTS=$(echo "$RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r.get('summary', {}).get('contacts_found', 0))" 2>/dev/null || echo "0")
    COST=$(echo "$RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r.get('summary', {}).get('total_cost_usd', 0))" 2>/dev/null || echo "0")
    SOURCE=$(echo "$RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); c=r.get('agent_results',{}).get('agent2_apollo',{}).get('contacts',[]); print(c[0].get('source', 'unknown') if len(c) > 0 else 'none')" 2>/dev/null || echo "unknown")
    ERROR=$(echo "$RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r.get('error', ''))" 2>/dev/null || echo "Parse error")

    # Update counters
    if [ "$SUCCESS" = "True" ]; then
        SUCCESSFUL=$((SUCCESSFUL + 1))
        echo -e "${GREEN}✅ SUCCESS${NC} - $CONTACTS contacts found | \$${COST} | Source: $SOURCE"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}❌ FAILED${NC} - $ERROR"
    fi

    echo ""

    # Rate limiting
    if [ $TESTED -lt $MAX_TESTS ] && [ $SUCCESSFUL -lt $TARGET_SUCCESS ]; then
        sleep 10
    fi
done

# Final summary
echo ""
echo "======================================================================="
echo "SEQUENTIAL TEST COMPLETE"
echo "======================================================================="
echo ""
echo "Results:"
echo "  Courses tested: $TESTED"
echo "  Successful: $SUCCESSFUL"
echo "  Failed: $FAILED"
echo ""

if [ $SUCCESSFUL -ge $TARGET_SUCCESS ]; then
    SUCCESS_RATE=$(echo "scale=1; $SUCCESSFUL * 100 / $TESTED" | bc)
    echo -e "${GREEN}✅ TARGET MET: $SUCCESSFUL/$TESTED courses successful ($SUCCESS_RATE%)${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review results in: $RESULTS_DIR/"
    echo "  2. Extract successful courses for final test set"
    echo "  3. Run batch test with these 20 courses"
else
    echo -e "${RED}❌ TARGET NOT MET: Only $SUCCESSFUL/$TARGET_SUCCESS courses successful${NC}"
    echo ""
    echo "Options:"
    echo "  1. Increase MAX_TESTS and re-run"
    echo "  2. Review failures and adjust strategy"
    echo "  3. Use different course selection criteria"
fi

echo ""
echo "Results saved to: $RESULTS_DIR/"
