#!/bin/bash
# Test 5 failed courses with 0 PGA contacts in Docker
# These should trigger waterfall fallback (Agent 2 → 2.1 → 2.2)

echo "🔍 Testing 5 Failed Courses (0 PGA contacts) - Docker Waterfall Test"
echo "========================================================================"
echo ""

# Course data from screenshot
declare -a COURSES=(
    '{"course_id": 1040, "name": "Roanoke Country Club", "state": "NC"}'
    '{"course_id": 1041, "name": "Wil-Mar Golf Club", "state": "NC"}'
    '{"course_id": 1042, "name": "Scotfield Country Club", "state": "NC"}'
    '{"course_id": 1043, "name": "Golf Etc., Cary", "state": "NC"}'
    '{"course_id": 1044, "name": "Green Meadows Golf Course", "state": "NC"}'
)

SUCCESS=0
FAILED=0
RESULTS_FILE="docker_waterfall_test_results.txt"

echo "Test Results" > $RESULTS_FILE
echo "============" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

for course_json in "${COURSES[@]}"; do
    COURSE_ID=$(echo $course_json | jq -r '.course_id')
    COURSE_NAME=$(echo $course_json | jq -r '.name')
    STATE=$(echo $course_json | jq -r '.state')

    echo "Testing Course $COURSE_ID: $COURSE_NAME"
    echo "----------------------------------------"

    # Make API call
    RESPONSE=$(curl -s -X POST http://localhost:8000/enrich-course \
        -H "Content-Type: application/json" \
        -d "{\"course_id\": $COURSE_ID, \"course_name\": \"$COURSE_NAME\", \"state_code\": \"$STATE\", \"use_test_tables\": false}")

    # Check if successful
    STATUS=$(echo $RESPONSE | jq -r '.status // "error"')
    CONTACTS=$(echo $RESPONSE | jq -r '.data.staff | length // 0')
    SOURCE=$(echo $RESPONSE | jq -r '.data.contact_source // "unknown"')
    FALLBACKS=$(echo $RESPONSE | jq -r '.data.fallback_sources_attempted // [] | join(", ")')

    if [ "$STATUS" = "success" ] && [ "$CONTACTS" -gt 0 ]; then
        echo "✅ SUCCESS: $CONTACTS contacts found"
        echo "   Source: $SOURCE"
        if [ -n "$FALLBACKS" ] && [ "$FALLBACKS" != "null" ]; then
            echo "   Fallbacks attempted: $FALLBACKS"
        fi
        SUCCESS=$((SUCCESS + 1))

        echo "✅ $COURSE_NAME: $CONTACTS contacts from $SOURCE" >> $RESULTS_FILE
    else
        echo "❌ FAILED: No contacts found"
        ERROR=$(echo $RESPONSE | jq -r '.error // "Unknown error"')
        echo "   Error: $ERROR"
        FAILED=$((FAILED + 1))

        echo "❌ $COURSE_NAME: FAILED - $ERROR" >> $RESULTS_FILE
    fi

    echo ""
    sleep 2  # Brief pause between requests
done

echo "========================================================================"
echo "TEST SUMMARY"
echo "========================================================================"
echo "Success: $SUCCESS/5 courses"
echo "Failed:  $FAILED/5 courses"
echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""

# Print results file
cat $RESULTS_FILE

exit $FAILED
