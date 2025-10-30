"""
Test Firecrawl API Credit Check
Purpose: Verify we can get remaining credits
Endpoint: GET /v2/team/credit-usage
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')

def test_firecrawl_credits_endpoint():
    """Test Firecrawl credit usage endpoint"""

    print("🧪 Testing Firecrawl Credits Endpoint")
    print("=" * 60)

    if not FIRECRAWL_API_KEY:
        print("❌ ERROR: FIRECRAWL_API_KEY not found in environment")
        print("   Set it in .env file: FIRECRAWL_API_KEY=your_key_here")
        return False

    try:
        # Call Firecrawl credit-usage endpoint
        url = "https://api.firecrawl.dev/v2/team/credit-usage"
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }

        print(f"📡 Calling: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ ERROR: {response.text}")
            return False

        data = response.json()

        # Extract credit info
        if not data.get('success'):
            print(f"❌ API returned success=false: {data}")
            return False

        credit_data = data.get('data', {})
        remaining = credit_data.get('remainingCredits', 0)
        plan_total = credit_data.get('planCredits', 0)
        billing_start = credit_data.get('billingPeriodStart', 'Unknown')
        billing_end = credit_data.get('billingPeriodEnd', 'Unknown')

        # Calculate usage percentage
        used = plan_total - remaining
        usage_pct = (used / plan_total * 100) if plan_total > 0 else 0

        print("\n✅ SUCCESS - Firecrawl Credits Retrieved!")
        print("=" * 60)
        print(f"💰 Remaining Credits: {remaining:,}")
        print(f"📦 Plan Total: {plan_total:,}")
        print(f"📊 Used: {used:,} ({usage_pct:.1f}%)")
        print(f"🔄 Billing Period: {billing_start} to {billing_end}")

        # Check thresholds
        if remaining < 500:
            print("\n🔴 CRITICAL: Firecrawl credits below 500!")
        elif remaining < 1000:
            print("\n🚨 WARNING: Firecrawl credits below 1,000!")
        else:
            print(f"\n🟢 Healthy: {remaining:,} credits remaining")

        print("=" * 60)

        # Return data for automation use
        return {
            'success': True,
            'remaining_credits': remaining,
            'plan_credits': plan_total,
            'used_credits': used,
            'usage_percentage': usage_pct,
            'billing_period_start': billing_start,
            'billing_period_end': billing_end
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    result = test_firecrawl_credits_endpoint()
    if result:
        print(f"\n✅ Test PASSED - Credit data retrieved successfully")
        exit(0)
    else:
        print(f"\n❌ Test FAILED - Could not retrieve credits")
        exit(1)
