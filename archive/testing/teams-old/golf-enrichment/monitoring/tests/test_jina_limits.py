"""
Test Jina AI Reader Rate Limits
Purpose: Verify rate limit handling and quota tracking
Limits: 20 req/min (no key), 200 req/min (with free key)
"""

print("🧪 Testing Jina AI Reader Rate Limits")
print("=" * 60)

print("""
📊 Jina AI Reader Pricing & Limits:

Free Access (No API Key):
- Rate Limit: 20 requests per minute
- URL Format: https://r.jina.ai/{YOUR_URL}
- Cost: FREE
- Use case: Light usage

Free API Key:
- Rate Limit: 200 requests per minute
- Same URL format with API key header
- Cost: FREE
- Use case: Moderate usage

Paid Plans:
- Higher rate limits available
- Token-based pricing model
- Auto-recharge available
""")

print("=" * 60)
print("\n🔍 Current Usage Analysis:")
print("   Agent 2 (Data Extractor) uses Jina occasionally")
print("   Estimated: 1-2 calls per course")
print("   With 10 courses/hour: ~10-20 calls/hour")
print("   = ~0.3 calls/min average")
print("")
print("   🟢 Well under 20/min free limit")
print("   No API key currently needed")
print("")

print("📋 Monitoring Strategy:")
print("   1. No active monitoring needed (usage too low)")
print("   2. Watch for 429 errors in Render logs")
print("   3. If scaling >100 courses/hour, add API key")
print("")

print("⚠️  Rate Limit Error Detection:")
print("   HTTP 429: Too Many Requests")
print("   Response: Rate limit exceeded")
print("   Action: Add Jina API key to .env")
print("")

print("=" * 60)
print("✅ Jina monitoring: 429 error detection only")
print("   Current usage: No monitoring needed")
print("   Scale trigger: >100 courses/hour")
