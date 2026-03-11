#!/usr/bin/env bash
# setup_gradient.sh — Create DigitalOcean Gradient AI resources for PhoneAngel
#
# Prerequisites:
#   - doctl CLI installed and authenticated
#   - DO_API_TOKEN set in .env
#
# This script creates:
#   1. Three Gradient AI agents (prep, coach, proxy)
#   2. One knowledge base with phone scripts
#   3. Outputs the IDs to paste into .env

set -euo pipefail

echo "=== PhoneAngel — Gradient AI Setup ==="
echo ""

# Check doctl
if ! command -v doctl &> /dev/null; then
    echo "ERROR: doctl not found. Install: https://docs.digitalocean.com/reference/doctl/"
    exit 1
fi

echo "Step 1: Creating Knowledge Base..."
KB_RESPONSE=$(doctl genai knowledge-base create \
    --name "phoneangel-scripts" \
    --embedding-model "text-embedding-3-small" \
    --output json 2>/dev/null || echo "SKIP")

if [ "$KB_RESPONSE" != "SKIP" ]; then
    KB_ID=$(echo "$KB_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['uuid'])" 2>/dev/null || echo "")
    echo "  Knowledge Base ID: $KB_ID"
else
    echo "  Skipped (already exists or doctl not configured)"
    KB_ID=""
fi

echo ""
echo "Step 2: Creating Prep Agent..."
PREP_RESPONSE=$(doctl genai agent create \
    --name "phoneangel-prep" \
    --model "anthropic/claude-sonnet-4-20250514" \
    --instruction "You are PhoneAngel Call-Prep. You generate conversation flowcharts and scripts to help autistic adults prepare for phone calls. Always respond in JSON format." \
    --output json 2>/dev/null || echo "SKIP")

if [ "$PREP_RESPONSE" != "SKIP" ]; then
    PREP_ID=$(echo "$PREP_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['uuid'])" 2>/dev/null || echo "")
    echo "  Prep Agent ID: $PREP_ID"
else
    echo "  Skipped"
    PREP_ID=""
fi

echo ""
echo "Step 3: Creating Coach Agent..."
COACH_RESPONSE=$(doctl genai agent create \
    --name "phoneangel-coach" \
    --model "anthropic/claude-sonnet-4-20250514" \
    --instruction "You are PhoneAngel Live Coach. You provide real-time, short coaching prompts during phone calls. Keep all messages under 12 words. Respond in JSON arrays." \
    --output json 2>/dev/null || echo "SKIP")

if [ "$COACH_RESPONSE" != "SKIP" ]; then
    COACH_ID=$(echo "$COACH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['uuid'])" 2>/dev/null || echo "")
    echo "  Coach Agent ID: $COACH_ID"
else
    echo "  Skipped"
    COACH_ID=""
fi

echo ""
echo "Step 4: Creating Proxy Agent..."
PROXY_RESPONSE=$(doctl genai agent create \
    --name "phoneangel-proxy" \
    --model "anthropic/claude-sonnet-4-20250514" \
    --instruction "You are PhoneAngel Proxy Caller. You make phone calls on behalf of autistic users. Be polite, efficient, and stay within decision boundaries." \
    --output json 2>/dev/null || echo "SKIP")

if [ "$PROXY_RESPONSE" != "SKIP" ]; then
    PROXY_ID=$(echo "$PROXY_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['uuid'])" 2>/dev/null || echo "")
    echo "  Proxy Agent ID: $PROXY_ID"
else
    echo "  Skipped"
    PROXY_ID=""
fi

echo ""
echo "=== Add these to your .env file ==="
echo "GRADIENT_KB_ID=$KB_ID"
echo "GRADIENT_AGENT_PREP_ID=$PREP_ID"
echo "GRADIENT_AGENT_COACH_ID=$COACH_ID"
echo "GRADIENT_AGENT_PROXY_ID=$PROXY_ID"
echo ""
echo "Next steps:"
echo "  1. Upload knowledge_base/phone_scripts.md to KB via DO console"
echo "  2. Attach KB to all three agents"
echo "  3. Run: uv run uvicorn phoneangel.app:app --reload"
