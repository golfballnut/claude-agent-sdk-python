"""
Test Perplexity API Balance Monitoring
Purpose: Verify 401 error detection when credits depleted
Note: Perplexity has NO balance endpoint - we monitor via error detection
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

def test_perplexity_api_connection():
    """Test Perplexity API connection and document monitoring strategy"""

    print("🧪 Testing Perplexity API Connection")
    print("=" * 60)

    if not PERPLEXITY_API_KEY:
        print("❌ ERROR: PERPLEXITY_API_KEY not found in environment")
        print("   Set it in .env file: PERPLEXITY_API_KEY=your_key_here")
        return False

    print("⚠️  NOTE: Perplexity has NO balance endpoint")
    print("   Strategy: Monitor for 401 errors in production")
    print("")

    try:
        # Make a minimal test call to verify API key works
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }

        # Minimal test payload (very cheap - using sonar model)
        payload = {
            "model": "sonar",  # Same model used by Agent 5
            "messages": [
                {"role": "user", "content": "hi"}
            ],
            "max_tokens": 1
        }

        print(f"📡 Testing API key validity with minimal call...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code == 401:
            print("\n🔴 CRITICAL: API Key Invalid or Credits Depleted!")
            print("   Error: 401 Unauthorized")
            print("   Action: Check dashboard at https://www.perplexity.ai/settings/api")
            print("   OR: Top up credits")
            return False

        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS - Perplexity API Key Valid!")
            print("=" * 60)
            print("🔑 API Key: Active")
            print("💰 Credits: Unknown (no balance endpoint)")
            print("📊 Monitoring Strategy:")
            print("   1. Watch Render logs for 401 errors")
            print("   2. Manual dashboard check weekly")
            print("   3. Enable auto-top-up ($2 minimum)")
            print("\n💡 Manual Balance Check:")
            print("   URL: https://www.perplexity.ai/settings/api")
            print("=" * 60)

            return {
                'success': True,
                'api_key_valid': True,
                'has_balance_endpoint': False,
                'monitoring_method': '401_error_detection',
                'manual_check_url': 'https://www.perplexity.ai/settings/api'
            }

        print(f"⚠️  Unexpected status code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    result = test_perplexity_api_connection()
    if result:
        print(f"\n✅ Test PASSED - API connection verified")
        print(f"⚠️  Remember: No automated balance checks available")
        print(f"   Use manual dashboard checks + 401 error monitoring")
        exit(0)
    else:
        print(f"\n❌ Test FAILED - API issue detected")
        exit(1)
