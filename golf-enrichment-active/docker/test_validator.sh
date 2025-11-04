#!/bin/bash

# Golf Enrichment V2 Validator - Docker Test Script
# Purpose: Test Render validator service in Docker before production deployment
# Usage: ./test_validator.sh

set -e  # Exit on error

echo "========================================="
echo "Golf V2 Validator - Docker Test Suite"
echo "========================================="
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "ERROR: .env file not found"
    echo "Create a .env file with:"
    echo "  SUPABASE_URL=https://your-project.supabase.co"
    echo "  SUPABASE_SERVICE_KEY=your-service-key"
    echo ""
    echo "Optional (for enrichment tests):"
    echo "  APOLLO_API_KEY=your-apollo-key"
    echo "  HUNTER_API_KEY=your-hunter-key"
    echo "  CLICKUP_API_TOKEN=your-clickup-token"
    exit 1
fi

# Load environment variables
source .env

echo "Step 1: Building Docker images..."
docker-compose --env-file .env -f docker-compose.validator.yml build

echo ""
echo "Step 2: Starting services..."
docker-compose --env-file .env -f docker-compose.validator.yml up -d validator

echo ""
echo "Step 3: Waiting for validator to be ready..."
timeout=30
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo "✅ Validator is healthy!"
        curl -s http://localhost:8000/health | python3 -m json.tool
        break
    fi
    echo "Waiting... ($elapsed/$timeout seconds)"
    sleep 3
    elapsed=$((elapsed + 3))
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ Validator failed to become healthy"
    docker-compose --env-file .env -f docker-compose.validator.yml logs validator
    docker-compose --env-file .env -f docker-compose.validator.yml down
    exit 1
fi

echo ""
echo "Step 4: Running test suite..."
docker-compose --env-file .env -f docker-compose.validator.yml run --rm test-runner

echo ""
echo "Step 5: Collecting results..."
docker-compose --env-file .env -f docker-compose.validator.yml cp test-runner:/app/results ./test_results

echo ""
echo "Step 6: Cleaning up..."
docker-compose --env-file .env -f docker-compose.validator.yml down

echo ""
echo "========================================="
echo "Test Results:"
echo "========================================="
if [ -f ./test_results/summary.txt ]; then
    cat ./test_results/summary.txt
else
    echo "⚠️  No summary file found"
fi

echo ""
echo "Full results available in: ./test_results/"
echo ""
echo "Done!"
