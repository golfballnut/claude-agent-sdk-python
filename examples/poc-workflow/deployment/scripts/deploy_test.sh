#!/bin/bash
# Render deployment test script
# Usage: ./deployment/scripts/deploy_test.sh <render-url>

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if URL provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ No URL provided${NC}"
    echo "Usage: $0 <render-url>"
    echo "Example: $0 https://agent7-water-hazards.onrender.com"
    exit 1
fi

API_URL="$1"

echo "🌐 Testing Render Deployment"
echo "=============================="
echo "URL: $API_URL"
echo ""

# Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    curl "$API_URL/health" | jq '.'
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi
echo ""

# Test root endpoint
echo "📍 Testing root endpoint..."
curl "$API_URL/" | jq '.'
echo ""

# Test courses
echo "🌊 Testing water hazard counting..."
echo ""

echo "1/3 Richmond Country Club"
echo "-------------------------"
curl -X POST "$API_URL/count-hazards" \
  -H "Content-Type: application/json" \
  -d @deployment/test_data/richmond.json | jq '.'
echo ""

echo "2/3 Belmont Golf Course"
echo "----------------------"
curl -X POST "$API_URL/count-hazards" \
  -H "Content-Type: application/json" \
  -d @deployment/test_data/belmont.json | jq '.'
echo ""

echo "3/3 Stonehenge Golf & Country Club"
echo "----------------------------------"
curl -X POST "$API_URL/count-hazards" \
  -H "Content-Type: application/json" \
  -d @deployment/test_data/stonehenge.json | jq '.'
echo ""

echo "=============================="
echo -e "${GREEN}✅ Deployment tests complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review results above"
echo "2. Compare with local test results"
echo "3. If successful, proceed with full orchestrator deployment"
