#!/bin/bash
# Local Docker test script for Agent 7 POC
# Usage: ./deployment/scripts/local_test.sh

set -e  # Exit on error

echo "🐳 Agent 7 Local Docker Test"
echo "=============================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

# Check environment variables
if [ -z "$PERPLEXITY_API_KEY" ]; then
    echo -e "${RED}❌ PERPLEXITY_API_KEY not set${NC}"
    echo "   Set it with: export PERPLEXITY_API_KEY=your_key"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ ANTHROPIC_API_KEY not set${NC}"
    echo "   Set it with: export ANTHROPIC_API_KEY=your_key"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables set${NC}"
echo ""

# Navigate to project root
cd "$(dirname "$0")/../.."

echo "📁 Current directory: $(pwd)"
echo ""

# Build Docker image
echo "🔨 Building Docker image..."
docker build -f deployment/Dockerfile -t agent7-poc . || {
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Docker build successful${NC}"
echo ""

# Run container in background
echo "🚀 Starting container..."
CONTAINER_ID=$(docker run -d -p 8000:8000 \
  -e PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  agent7-poc)

echo -e "${GREEN}✓ Container started: ${CONTAINER_ID:0:12}${NC}"
echo ""

# Wait for container to be ready
echo "⏳ Waiting for container to be ready..."
sleep 5

# Check if container is running
if ! docker ps | grep -q $CONTAINER_ID; then
    echo -e "${RED}❌ Container failed to start${NC}"
    echo "Logs:"
    docker logs $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi

# Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi
echo ""

# Test water hazard counting
echo "🌊 Testing water hazard counting (Richmond CC)..."
echo ""
curl -X POST http://localhost:8000/count-hazards \
  -H "Content-Type: application/json" \
  -d @deployment/test_data/richmond.json | jq '.'
echo ""

# Show container logs
echo "📋 Container logs (last 20 lines):"
docker logs --tail 20 $CONTAINER_ID
echo ""

# Ask user if they want to stop the container
echo -e "${YELLOW}Container is running at http://localhost:8000${NC}"
echo "Press Ctrl+C to stop and cleanup, or"
read -p "Press Enter to stop the container now..."

# Cleanup
echo ""
echo "🧹 Cleaning up..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

echo "=============================="
echo "✅ Local test complete!"
echo ""
echo "Next steps:"
echo "1. Review the output above"
echo "2. If successful, deploy to Render"
echo "3. Follow instructions in deployment/README.md"
