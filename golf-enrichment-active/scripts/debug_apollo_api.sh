#!/bin/bash
#
# Apollo API Debug Script
# Tests different search strategies to find one that works correctly
#
# Usage: ./debug_apollo_api.sh <domain> <course_name> <state>
# Example: ./debug_apollo_api.sh deepspringscc.com "Deep Springs Country Club" NC

set -e

DOMAIN=${1:-"deepspringscc.com"}
COURSE_NAME=${2:-"Deep Springs Country Club"}
STATE=${3:-"NC"}

# Load API key from .env
if [ -f "../../.env" ]; then
    export $(grep -v '^#' ../../.env | xargs)
elif [ -f "../.env" ]; then
    export $(grep -v '^#' ../.env | xargs)
fi

if [ -z "$APOLLO_API_KEY" ]; then
    echo "❌ APOLLO_API_KEY not found in .env"
    exit 1
fi

echo "🔍 Apollo API Debug Tests"
echo "========================================================================"
echo "Domain: $DOMAIN"
echo "Course: $COURSE_NAME"
echo "State: $STATE"
echo "========================================================================"
echo ""

# Test 1: Current strategy (organization_domain)
echo "TEST 1: organization_domain (current strategy - BROKEN)"
echo "------------------------------------------------------------------------"
curl -s -X POST https://api.apollo.io/api/v1/people/search \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d "{
    \"organization_domain\": \"$DOMAIN\",
    \"person_titles\": [\"General Manager\"],
    \"page\": 1,
    \"per_page\": 3
  }" | jq '{
    total_people: .pagination.total_entries,
    people_found: (.people | length),
    people: .people | map({
      name: .name,
      title: .title,
      email: .email,
      organization: .organization.name,
      organization_domain: .organization.primary_domain,
      person_id: .id
    })
  }'
echo ""
echo ""

# Test 2: organization_name search
echo "TEST 2: q_organization_name (name-based search)"
echo "------------------------------------------------------------------------"
curl -s -X POST https://api.apollo.io/api/v1/people/search \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d "{
    \"q_organization_name\": \"$COURSE_NAME\",
    \"person_titles\": [\"General Manager\"],
    \"page\": 1,
    \"per_page\": 3
  }" | jq '{
    total_people: .pagination.total_entries,
    people_found: (.people | length),
    people: .people | map({
      name: .name,
      title: .title,
      email: .email,
      organization: .organization.name,
      organization_domain: .organization.primary_domain,
      person_id: .id
    })
  }'
echo ""
echo ""

# Test 3: Name + Location filter
echo "TEST 3: q_organization_name + organization_locations (name + state)"
echo "------------------------------------------------------------------------"
curl -s -X POST https://api.apollo.io/api/v1/people/search \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d "{
    \"q_organization_name\": \"$COURSE_NAME\",
    \"organization_locations\": [\"$STATE\"],
    \"person_titles\": [\"General Manager\"],
    \"page\": 1,
    \"per_page\": 3
  }" | jq '{
    total_people: .pagination.total_entries,
    people_found: (.people | length),
    people: .people | map({
      name: .name,
      title: .title,
      email: .email,
      organization: .organization.name,
      organization_domain: .organization.primary_domain,
      person_id: .id
    })
  }'
echo ""
echo ""

# Test 4: Two-step approach - Find organization first
echo "TEST 4: Two-step (find org by domain, then people)"
echo "------------------------------------------------------------------------"
echo "Step 1: Find organization..."
ORG_RESPONSE=$(curl -s -X POST https://api.apollo.io/api/v1/organizations/search \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d "{
    \"organization_domains\": [\"$DOMAIN\"],
    \"page\": 1,
    \"per_page\": 1
  }")

echo "$ORG_RESPONSE" | jq '{
  organizations_found: (.organizations | length),
  organization: .organizations[0] | {
    name: .name,
    domain: .primary_domain,
    id: .id
  }
}'

ORG_ID=$(echo "$ORG_RESPONSE" | jq -r '.organizations[0].id // empty')

if [ -n "$ORG_ID" ]; then
    echo ""
    echo "Step 2: Find people at organization $ORG_ID..."
    curl -s -X POST https://api.apollo.io/api/v1/people/search \
      -H "Content-Type: application/json" \
      -H "X-Api-Key: $APOLLO_API_KEY" \
      -d "{
        \"organization_ids\": [\"$ORG_ID\"],
        \"person_titles\": [\"General Manager\"],
        \"page\": 1,
        \"per_page\": 3
      }" | jq '{
        total_people: .pagination.total_entries,
        people_found: (.people | length),
        people: .people | map({
          name: .name,
          title: .title,
          email: .email,
          organization: .organization.name,
          person_id: .id
        })
      }'
else
    echo "❌ No organization found for domain: $DOMAIN"
fi

echo ""
echo ""

# Summary
echo "========================================================================"
echo "📊 SUMMARY"
echo "========================================================================"
echo ""
echo "Which test found correct contacts (email domain matches $DOMAIN)?"
echo ""
echo "Test 1 (organization_domain): Check results above"
echo "Test 2 (q_organization_name): Check results above"
echo "Test 3 (name + location): Check results above"
echo "Test 4 (two-step org search): Check results above"
echo ""
echo "Look for contacts where organization_domain = $DOMAIN"
echo ""
