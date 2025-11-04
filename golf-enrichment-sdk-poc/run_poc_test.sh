#!/bin/bash
#
# POC Test Runner for SDK Agent
# Loads environment variables and runs the test
#

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."

# Load environment variables from docker/.env
ENV_FILE="$PROJECT_ROOT/agenttesting/golf-enrichment/docker/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Environment file not found: $ENV_FILE"
    exit 1
fi

echo "📂 Loading environment from: $ENV_FILE"
export $(cat "$ENV_FILE" | grep -v '^#' | grep -v '^$' | xargs)

echo ""
echo "🧪 Starting SDK Agent POC Test"
echo "="*60
echo ""

# Run the test
cd "$SCRIPT_DIR"
python test_sdk_agent.py "$@"
