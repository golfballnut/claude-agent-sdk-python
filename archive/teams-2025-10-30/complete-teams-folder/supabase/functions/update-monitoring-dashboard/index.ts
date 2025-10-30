// Edge Function: update-monitoring-dashboard
// Purpose: Update ClickUp monitoring tasks with service health data
// Called by: check-all-services edge function
// Creates: Alert tasks when thresholds breached

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

const CLICKUP_API_KEY = Deno.env.get('CLICKUP_API_KEY')
const MONITORING_LIST_ID = '901413319288' // Service Health Dashboard
const ALERT_LIST_ID = '901409749476' // Your personal list for alerts

// Map service names to task IDs (will be set after first run)
const TASK_IDS = {
  hunter_io: '86b778jwa',
  firecrawl: '86b778jw9',
  supabase: '86b778jw8',
  render: '86b778jwe',
  anthropic: '86b778jwg',
  perplexity: '86b778jwf',
  clickup: '86b778jwm',
  jina: '86b778jwj',
  brightdata: '86b778jwk'
}

serve(async (req) => {
  try {
    const { services } = await req.json()

    console.log(`📊 Updating dashboard for ${services.length} services...`)

    const updates = []
    const alerts = []

    for (const service of services) {
      const taskId = TASK_IDS[service.service]
      if (!taskId) {
        console.log(`   ⚠️  No task ID for ${service.service}`)
        continue
      }

      // Build description based on service
      let description = `**Last Checked:** ${service.checked_at}\n**Status:** ${getStatusEmoji(service.status)}\n\n`

      if (service.service === 'hunter_io') {
        description += `**Searches:** ${service.data.searches_available || 'N/A'}\n`
        description += `**Verifications:** ${service.data.verifications_available || 'N/A'}\n`
        description += `**Reset:** ${service.data.reset_date || 'N/A'}`

        // Check threshold
        if (service.data.searches_available < 50) {
          alerts.push({
            name: `🚨 CRITICAL: Hunter.io Low - ${service.data.searches_available} searches left`,
            service: 'hunter_io',
            severity: 'critical',
            value: service.data.searches_available
          })
        }
      } else if (service.service === 'firecrawl') {
        description += `**Credits:** ${service.data.remaining_credits || 'N/A'} / ${service.data.plan_credits || 'N/A'}\n`
        description += `**Usage:** ${service.data.usage_percent || 'N/A'}%\n`
        description += `**Billing End:** ${service.data.billing_end || 'N/A'}`

        // Check threshold
        if (service.data.remaining_credits < 500) {
          alerts.push({
            name: `🚨 CRITICAL: Firecrawl Low - ${service.data.remaining_credits} credits left`,
            service: 'firecrawl',
            severity: 'critical',
            value: service.data.remaining_credits
          })
        }
      } else if (service.service === 'supabase') {
        description += `**Size:** ${service.data.database_size_mb} MB\n`
        description += `**Connections:** ${service.data.total_connections}`
      } else {
        description += `**Data:** ${JSON.stringify(service.data, null, 2)}`
      }

      // Update ClickUp task
      try {
        const updateResponse = await fetch(
          `https://api.clickup.com/api/v2/task/${taskId}`,
          {
            method: 'PUT',
            headers: {
              'Authorization': CLICKUP_API_KEY!,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description })
          }
        )

        if (updateResponse.ok) {
          updates.push(service.service)
          console.log(`   ✅ Updated ${service.service}`)
        } else {
          console.error(`   ❌ Failed to update ${service.service}: ${updateResponse.status}`)
        }
      } catch (e) {
        console.error(`   ❌ Error updating ${service.service}: ${e.message}`)
      }
    }

    // Create alert tasks for critical services
    for (const alert of alerts) {
      console.log(`🚨 Creating alert for ${alert.service}...`)

      const alertTask = {
        name: alert.name,
        description: `**Service:** ${alert.service}
**Severity:** ${alert.severity}
**Value:** ${alert.value}
**Detected:** ${timestamp}

**Action Required:**
1. Check service dashboard
2. Top up credits if needed
3. Investigate if unexpected

**Service Status:** https://app.clickup.com/t/${TASK_IDS[alert.service]}`,
        priority: alert.severity === 'critical' ? 1 : 2,
        tags: ['service-alert', 'auto-created', alert.severity]
      }

      try {
        const alertResponse = await fetch(
          `https://api.clickup.com/api/v2/list/${ALERT_LIST_ID}/task`,
          {
            method: 'POST',
            headers: {
              'Authorization': CLICKUP_API_KEY!,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(alertTask)
          }
        )

        if (alertResponse.ok) {
          const alertData = await alertResponse.json()
          console.log(`   ✅ Alert created: ${alertData.id}`)
        }
      } catch (e) {
        console.error(`   ❌ Failed to create alert: ${e.message}`)
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        checked_at: timestamp,
        updated_tasks: updates.length,
        alerts_created: alerts.length,
        services_checked: services.length
      }),
      { headers: { 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('❌ Error updating dashboard:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})

function getStatusEmoji(status: string): string {
  switch (status) {
    case 'healthy': return '🟢 Healthy'
    case 'warning': return '🟡 Warning'
    case 'critical': return '🔴 Critical'
    default: return '⚪ Unknown'
  }
}
