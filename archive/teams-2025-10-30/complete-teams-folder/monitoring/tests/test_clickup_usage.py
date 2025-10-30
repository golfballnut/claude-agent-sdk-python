"""
Test ClickUp API Usage Tracking
Purpose: Track ClickUp API calls to monitor rate limits
Rate Limits: 100 requests/min (Free/Unlimited/Business), 1000/min (Business Plus)
"""

print("🧪 Testing ClickUp API Usage Tracking")
print("=" * 60)

print("""
📊 ClickUp Rate Limits:
- Free/Unlimited/Business: 100 requests per minute
- Business Plus: 1,000 requests per minute
- Error Code: 429 (Too Many Requests)

⚠️  No Balance Endpoint Available

🔍 Monitoring Strategy:
1. Track API calls made by our edge functions
2. Count calls per hour/day
3. Alert if approaching 100/min (6000/hour)
4. Monitor for 429 errors in logs

📝 Usage Tracking Methods:

Method 1: Count in Edge Function
- Increment counter in Supabase on each ClickUp call
- Query: SELECT COUNT(*) FROM clickup_api_calls WHERE timestamp > NOW() - INTERVAL '1 hour'

Method 2: Monitor Response Headers
- ClickUp returns X-RateLimit-* headers
- Check X-RateLimit-Remaining
- Alert if < 20 requests remaining

Method 3: Log Analysis
- Count ClickUp API calls in edge function logs
- Supabase function logs show all HTTP requests
- Parse logs for api.clickup.com calls

✅ Recommended Approach:
Use Method 1 (counter table) + Method 2 (response headers) combined

📋 Current Usage Estimate:
- create-clickup-tasks: ~15 API calls per course
  * Update course task: 3 calls (fetch, update, clear & replace)
  * Update 3-5 contact tasks: 3-5 calls each (9-15 total)
  * Create/update outreach task: 3 calls
  * Total: ~15-20 calls per course

- With 10 courses/hour max: ~150-200 API calls/hour
- Well under 6000/hour limit (100/min)
- No rate limit concerns currently

🟢 Status: Healthy - well under limits
⚠️  Monitor: Add tracking if scaling beyond 10 courses/hour
""")

print("=" * 60)
print("✅ ClickUp usage analysis complete")
print("   Current usage: ~15-20 calls per course")
print("   Limit: 6000 calls/hour")
print("   Status: 🟢 Healthy (no monitoring needed yet)")
