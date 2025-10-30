#!/bin/bash
#
# Test Apollo Fixes on 5 Failed Courses
#
# Tests the Apollo orchestrator with:
# - Domain-first search
# - Hunter.io fallback
# - Fixed domain discovery
#
# Created: Oct 29, 2025
#

echo "================================================================================"
echo "Testing Apollo Fixes on 5 Previously Failed Courses"
echo "================================================================================"
echo ""
echo "Fixes being tested:"
echo "  ✅ Domain-first Apollo search"
echo "  ✅ Hunter.io fallback when Apollo returns 0"
echo "  ✅ Agent 1 runs when domain is missing"
echo ""

# Create results directory (relative to golf-enrichment root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESULTS_DIR="$SCRIPT_DIR/../../results/docker"
mkdir -p "$RESULTS_DIR"

# Define test courses (from apollo_failure_courses.json)
declare -a COURSES=(
  '{"course_name":"Cardinal Country Club","state_code":"NC","domain":"playcardinal.net"}'
  '{"course_name":"Carolina Club, The","state_code":"NC","domain":"thecarolinaclub.com"}'
  '{"course_name":"Carolina Colours Golf Club","state_code":"NC"}'
  '{"course_name":"Carolina, The","state_code":"NC","domain":"pinehurst.com"}'
  '{"course_name":"Carolina Plantation Golf Club","state_code":"NC"}'
)

declare -a NAMES=(
  "Cardinal Country Club"
  "Carolina Club, The"
  "Carolina Colours Golf Club"
  "Carolina, The"
  "Carolina Plantation Golf Club"
)

SUCCESS=0
FAILED=0
TOTAL=${#COURSES[@]}

echo "📊 Testing $TOTAL courses..."
echo ""

for i in "${!COURSES[@]}"; do
  COURSE_NUM=$((i+1))
  COURSE_JSON="${COURSES[$i]}"
  COURSE_NAME="${NAMES[$i]}"

  echo "=========================================="
  echo "[$COURSE_NUM/$TOTAL] Testing: $COURSE_NAME"
  echo "=========================================="

  # Add use_test_tables to request
  REQUEST=$(echo "$COURSE_JSON" | jq '. + {use_test_tables: true}')

  # Call API
  echo "🔄 Calling enrichment API..."
  RESPONSE=$(curl -s -X POST http://localhost:8001/enrich-course \
    -H "Content-Type: application/json" \
    -d "$REQUEST")

  # Save full response
  RESULT_FILE="$RESULTS_DIR/apollo_fix_course_${COURSE_NUM}.json"
  echo "$RESPONSE" | jq > "$RESULT_FILE"

  # Extract key metrics
  SUCCESS_FLAG=$(echo "$RESPONSE" | jq -r '.success')
  CONTACTS=$(echo "$RESPONSE" | jq -r '.summary.contacts | length // 0')
  COST=$(echo "$RESPONSE" | jq -r '.summary.total_cost // 0')
  SOURCE=$(echo "$RESPONSE" | jq -r '.summary.source // "unknown"')
  ERROR=$(echo "$RESPONSE" | jq -r '.error // "none"')

  echo "  Course: $COURSE_NAME"
  echo "  Success: $SUCCESS_FLAG"
  echo "  Contacts: $CONTACTS"
  echo "  Source: $SOURCE"
  echo "  Cost: \$$COST"

  if [ "$SUCCESS_FLAG" = "true" ]; then
    SUCCESS=$((SUCCESS+1))
    echo "  ✅ PASSED"
  else
    FAILED=$((FAILED+1))
    echo "  ❌ FAILED: $ERROR"
  fi

  echo "  📁 Results: $RESULT_FILE"
  echo ""

  # Rate limiting between tests
  if [ $COURSE_NUM -lt $TOTAL ]; then
    echo "⏸️  Waiting 10 seconds before next test..."
    echo ""
    sleep 10
  fi
done

# Calculate success rate
SUCCESS_RATE=$(echo "scale=1; $SUCCESS * 100 / $TOTAL" | bc)

echo "================================================================================"
echo "FINAL RESULTS"
echo "================================================================================"
echo ""
echo "📊 Summary:"
echo "  Total courses: $TOTAL"
echo "  Succeeded: $SUCCESS ($SUCCESS_RATE%)"
echo "  Failed: $FAILED"
echo ""

if (( $(echo "$SUCCESS_RATE >= 80" | bc -l) )); then
  echo "✅ TARGET MET: $SUCCESS_RATE% ≥ 80% goal"
  echo ""
  echo "🎯 Ready for production deployment!"
elif (( $(echo "$SUCCESS_RATE >= 60" | bc -l) )); then
  echo "⚠️  CLOSE: $SUCCESS_RATE% (need 80%+)"
  echo ""
  echo "💡 Recommendations:"
  echo "  - Review failed courses for patterns"
  echo "  - Consider additional fallback strategies"
else
  echo "❌ BELOW TARGET: $SUCCESS_RATE% < 60%"
  echo ""
  echo "🔍 Debug required:"
  echo "  - Check Docker logs: docker-compose -f docker-compose.apollo.yml logs"
  echo "  - Review failed course details in results/docker/"
fi

echo ""
echo "📂 All results saved to: $RESULTS_DIR/apollo_fix_course_*.json"
echo ""
echo "================================================================================"
