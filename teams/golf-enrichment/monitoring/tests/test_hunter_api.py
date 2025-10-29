"""
Test Hunter.io API Balance Check
Purpose: Verify we can get account balance and remaining credits
Endpoint: GET /v2/account
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')

def test_hunter_account_endpoint():
    """Test Hunter.io account endpoint to get balance"""

    print("🧪 Testing Hunter.io Account Endpoint")
    print("=" * 60)

    if not HUNTER_API_KEY:
        print("❌ ERROR: HUNTER_API_KEY not found in environment")
        print("   Set it in .env file: HUNTER_API_KEY=your_key_here")
        return False

    try:
        # Call Hunter.io account endpoint
        url = f"https://api.hunter.io/v2/account?api_key={HUNTER_API_KEY}"

        print(f"📡 Calling: {url[:50]}...")
        response = requests.get(url, timeout=10)

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ ERROR: {response.text}")
            return False

        data = response.json()

        # Extract balance info
        account = data.get('data', {})
        requests_data = account.get('requests', {})
        searches = requests_data.get('searches', {})
        verifications = requests_data.get('verifications', {})

        print("\n✅ SUCCESS - Hunter.io Balance Retrieved!")
        print("=" * 60)
        print(f"📧 Account: {account.get('email', 'Unknown')}")
        print(f"📦 Plan: {account.get('plan_name', 'Unknown')}")
        print(f"🔄 Reset Date: {account.get('reset_date', 'Unknown')}")
        print("\n📊 Searches:")
        print(f"   Used: {searches.get('used', 0)}")
        print(f"   Available: {searches.get('available', 0)}")
        print(f"   Total Limit: {searches.get('used', 0) + searches.get('available', 0)}")
        print("\n✓ Verifications:")
        print(f"   Used: {verifications.get('used', 0)}")
        print(f"   Available: {verifications.get('available', 0)}")
        print(f"   Total Limit: {verifications.get('used', 0) + verifications.get('available', 0)}")

        # Check thresholds
        searches_remaining = searches.get('available', 0)
        if searches_remaining < 100:
            print("\n🚨 WARNING: Hunter.io searches below 100!")
        elif searches_remaining < 50:
            print("\n🔴 CRITICAL: Hunter.io searches below 50!")
        else:
            print("\n🟢 Healthy: Plenty of searches remaining")

        print("=" * 60)

        # Return data for automation use
        return {
            'success': True,
            'searches_available': searches.get('available', 0),
            'searches_used': searches.get('used', 0),
            'verifications_available': verifications.get('available', 0),
            'verifications_used': verifications.get('used', 0),
            'reset_date': account.get('reset_date'),
            'plan_name': account.get('plan_name')
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    result = test_hunter_account_endpoint()
    if result:
        print(f"\n✅ Test PASSED - Balance data retrieved successfully")
        exit(0)
    else:
        print(f"\n❌ Test FAILED - Could not retrieve balance")
        exit(1)
