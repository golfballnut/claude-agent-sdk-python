"""
Test Anthropic Claude API Usage Tracking
Purpose: Research usage/cost API access and tracking options
Endpoint: Requires Admin API key (sk-ant-admin...)
"""

print("🧪 Testing Anthropic Claude Usage Tracking")
print("=" * 60)

print("""
📋 Anthropic API Tracking Options:

Option 1: Usage & Cost API (Requires Admin Key)
- Endpoint: POST /v1/organizations/usage_report/messages
- Endpoint: GET /v1/organizations/cost_report
- Requires: Admin API key (sk-ant-admin...)
- Access: Organization admins only
- Data: Token usage, costs by model/workspace

Option 2: Database Logging (Current Method ✅)
- Agent cost logged in: golf_courses.agent_cost_usd
- Per-agent tracking available
- Total cost per course tracked
- Already implemented!

Option 3: Console Dashboard (Manual)
- URL: https://console.anthropic.com/settings/billing
- View: Usage, costs, remaining credits
- Frequency: Weekly manual check

""")

print("\n📊 Current Anthropic Usage (from Database):")

query = '''
SELECT
  COUNT(*) as courses_enriched,
  SUM(agent_cost_usd) as total_cost,
  AVG(agent_cost_usd) as avg_cost_per_course,
  MAX(agent_cost_usd) as max_cost,
  MIN(agent_cost_usd) FILTER (WHERE agent_cost_usd > 0) as min_cost
FROM golf_courses
WHERE enrichment_status = 'completed'
  AND agent_cost_usd IS NOT NULL
  AND enrichment_completed_at > NOW() - INTERVAL '30 days'
'''

print("   Query available - run via Supabase to see costs")
print("")

print("✅ Recommendation:")
print("   Use database logging (already implemented)")
print("   Weekly summary in ClickUp task")
print("   No Admin API key needed")
print("")

print("📝 Weekly Summary Should Include:")
print("   - Total courses enriched")
print("   - Total Anthropic cost")
print("   - Average cost per course")
print("   - Cost trend (vs previous week)")
print("")

print("=" * 60)
print("✅ Anthropic usage tracking via database ✅")
print("   Admin API not required")
