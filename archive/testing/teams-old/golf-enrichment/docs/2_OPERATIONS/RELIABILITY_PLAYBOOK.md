# Reliability Playbook - Golf Course Enrichment System

**Purpose:** Operations guide for maintaining 99%+ uptime and data quality
**Audience:** Dev/ops team managing the enrichment pipeline
**Last Updated:** October 18, 2024

---

## 🎯 **System Health Targets**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Success Rate | > 95% | < 90% |
| Avg Cost per Course | < $0.25 | > $0.30 |
| Avg Duration | < 10 min | > 15 min |
| Error Rate | < 5% | > 10% |
| Webhook Delivery | > 98% | < 95% |
| ClickUp Sync | > 99% | < 95% |

---

## 🚨 **Error Scenarios & Recovery**

### **Error 1: Trigger Doesn't Fire**

**Symptom:**
- Manual UPDATE to `enrichment_status = 'pending'` doesn't start workflow
- Status remains 'pending' for > 5 minutes

**Diagnosis:**
```sql
-- Check if trigger exists
SELECT tgname, tgenabled
FROM pg_trigger
WHERE tgrelid = 'golf_courses'::regclass
  AND tgname = 'on_enrichment_requested';

-- Should return: on_enrichment_requested | O (enabled)
```

**Root Causes:**
1. Database trigger not created
2. http extension not enabled
3. Edge function URL wrong

**Recovery:**
```sql
-- 1. Enable http extension
CREATE EXTENSION IF NOT EXISTS http WITH SCHEMA extensions;

-- 2. Recreate trigger function
CREATE OR REPLACE FUNCTION call_trigger_agent_enrichment()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/trigger-agent-enrichment',
    headers := '{"Content-Type": "application/json"}'::jsonb,
    body := json_build_object('course_id', NEW.id)::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Recreate trigger
DROP TRIGGER IF EXISTS on_enrichment_requested ON golf_courses;
CREATE TRIGGER on_enrichment_requested
AFTER UPDATE OF enrichment_status ON golf_courses
FOR EACH ROW
WHEN (NEW.enrichment_status = 'pending')
EXECUTE FUNCTION call_trigger_agent_enrichment();

-- 4. Test
UPDATE golf_courses SET enrichment_status = 'pending' WHERE id = 'test-uuid';
```

---

### **Error 2: Render API Timeout**

**Symptom:**
- `enrichment_status = 'processing'` for > 15 minutes
- Agents should complete in 4-7 minutes

**Diagnosis:**
```sql
-- Find stuck courses
SELECT
  id,
  course_name,
  enrichment_status,
  enrichment_requested_at,
  EXTRACT(EPOCH FROM (NOW() - enrichment_requested_at)) / 60 as minutes_elapsed
FROM golf_courses
WHERE enrichment_status = 'processing'
  AND enrichment_requested_at < NOW() - INTERVAL '15 minutes';
```

**Root Causes:**
1. Render service crashed
2. Agents in infinite loop
3. Network issue
4. Too many contacts (10+) taking too long

**Recovery:**
```bash
# 1. Check Render service status
curl https://agent7-water-hazards.onrender.com/health

# 2. Check Render logs for errors
# (Use Render dashboard or MCP tools)

# 3. Mark course as error for manual review
```

```sql
UPDATE golf_courses
SET enrichment_status = 'error',
    enrichment_error = 'Timeout: exceeded 15 minutes'
WHERE enrichment_status = 'processing'
  AND enrichment_requested_at < NOW() - INTERVAL '15 minutes';
```

**Manual Retry:**
```sql
-- After fixing root cause, retry
UPDATE golf_courses
SET enrichment_status = 'pending',
    enrichment_error = NULL
WHERE id = 'stuck-course-uuid';
```

---

### **Error 3: Agents Fail Mid-Workflow**

**Symptom:**
- Webhook received with `success: false`
- `enrichment_status = 'error'`
- `enrichment_error` contains agent failure message

**Diagnosis:**
```sql
-- Find recent failures
SELECT id, course_name, enrichment_error, enrichment_requested_at
FROM golf_courses
WHERE enrichment_status = 'error'
  AND enrichment_requested_at > NOW() - INTERVAL '24 hours'
ORDER BY enrichment_requested_at DESC;
```

**Common Agent Failures:**
| Agent | Failure Reason | Fix |
|-------|----------------|-----|
| Agent 1 | Course not in VSGA directory | Skip or use different directory |
| Agent 2 | URL 404/403 | Verify URL, may need manual entry |
| Agent 3 | Hunter.io API limit | Wait for reset, use different key |
| Agent 5 | Perplexity timeout | Retry, use backup phone source |
| Agent 6 | Query parsing error | Review query format, retry |
| Agent 8 | Supabase write error | Check permissions, retry |

**Recovery:**
```sql
-- Retry failed enrichment
UPDATE golf_courses
SET enrichment_status = 'pending',
    enrichment_error = NULL,
    enrichment_requested_at = NOW()
WHERE id = 'failed-course-uuid';
```

---

### **Error 4: Webhook Not Received**

**Symptom:**
- Render logs show "Webhook sent successfully"
- But Supabase never updated (`enrichment_status` still 'processing')

**Diagnosis:**
```bash
# Check Supabase edge function logs
# (Use Supabase dashboard → Edge Functions → Logs)

# Check if edge function deployed
supabase functions list
```

**Root Causes:**
1. Edge function not deployed
2. Wrong webhook URL in Render
3. Authentication failure
4. Edge function crashed

**Recovery:**
```bash
# 1. Redeploy edge function
supabase functions deploy receive-agent-enrichment

# 2. Test webhook manually
curl -X POST 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/receive-agent-enrichment' \
  -H 'Content-Type: application/json' \
  -d '{"course_id": "test", "success": true, "contacts": []}'

# 3. If that works, get Render response and manually send webhook
```

---

### **Error 5: Duplicate Enrichment**

**Symptom:**
- Course enriched twice
- Duplicate contacts in database

**Diagnosis:**
```sql
-- Find duplicates
SELECT golf_course_id, name, COUNT(*)
FROM golf_course_contacts
GROUP BY golf_course_id, name
HAVING COUNT(*) > 1;
```

**Prevention:**
```sql
-- Add unique constraint
ALTER TABLE golf_course_contacts
ADD CONSTRAINT unique_contact_per_course
UNIQUE (golf_course_id, name);

-- Or check before triggering
SELECT enrichment_status FROM golf_courses WHERE id = 'uuid';
-- Only trigger if NULL or 'error'
```

**Recovery:**
```sql
-- Delete duplicates, keep most recent
DELETE FROM golf_course_contacts
WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (
      PARTITION BY golf_course_id, name
      ORDER BY enriched_at DESC
    ) as rn
    FROM golf_course_contacts
  ) t
  WHERE rn > 1
);
```

---

### **Error 6: ClickUp API Failure**

**Symptom:**
- Contacts inserted
- But `clickup_task_id` is NULL
- ClickUp task not visible

**Diagnosis:**
```sql
-- Contacts without ClickUp tasks
SELECT
  c.id, c.name, c.title, g.course_name, c.enriched_at
FROM golf_course_contacts c
JOIN golf_courses g ON c.golf_course_id = g.id
WHERE c.clickup_task_id IS NULL
  AND c.enriched_at IS NOT NULL
ORDER BY c.enriched_at DESC;
```

**Root Causes:**
1. ClickUp API key expired
2. List ID wrong/deleted
3. Custom field IDs changed
4. Rate limit hit

**Recovery:**
```bash
# 1. Verify ClickUp API key
curl -H "Authorization: YOUR_KEY" https://api.clickup.com/api/v2/team

# 2. Test create task manually
curl -X POST "https://api.clickup.com/api/v2/list/LIST_ID/task" \
  -H "Authorization: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Task"}'

# 3. If API works, retry failed contacts
```

```sql
-- Trigger ClickUp creation for failed contacts
-- Delete and re-insert (triggers ON INSERT again)
WITH failed_contacts AS (
  SELECT * FROM golf_course_contacts
  WHERE clickup_task_id IS NULL
    AND enriched_at > NOW() - INTERVAL '1 hour'
)
-- Manual approach: Call edge function for each
```

---

## 📊 **Monitoring Dashboard Queries**

### **1. Real-Time Status**

```sql
-- What's happening right now?
SELECT
  SUM(CASE WHEN enrichment_status = 'pending' THEN 1 ELSE 0 END) as pending,
  SUM(CASE WHEN enrichment_status = 'processing' THEN 1 ELSE 0 END) as processing,
  SUM(CASE WHEN enrichment_status = 'complete' THEN 1 ELSE 0 END) as complete,
  SUM(CASE WHEN enrichment_status = 'error' THEN 1 ELSE 0 END) as error,
  SUM(CASE WHEN enrichment_status IS NULL THEN 1 ELSE 0 END) as not_started
FROM golf_courses;
```

**Expected Output:**
```
pending | processing | complete | error | not_started
   2    |     3      |    450   |   5   |     250
```

**Alerts:**
- ⚠️ If `processing` > 10 → Possible bottleneck
- 🚨 If `error` > 5% of total → Investigation needed

---

### **2. Performance Metrics**

```sql
-- Last 100 completed enrichments
SELECT
  ROUND(AVG(agent_cost_usd), 4) as avg_cost,
  ROUND(MIN(agent_cost_usd), 4) as min_cost,
  ROUND(MAX(agent_cost_usd), 4) as max_cost,
  ROUND(AVG(EXTRACT(EPOCH FROM (enrichment_completed_at - enrichment_requested_at))), 1) as avg_seconds,
  COUNT(*) as sample_size
FROM golf_courses
WHERE enrichment_status = 'complete'
  AND enrichment_completed_at > NOW() - INTERVAL '7 days'
LIMIT 100;
```

**Expected:**
```
avg_cost | min_cost | max_cost | avg_seconds | sample_size
  0.1950 |   0.1761 |   0.2767 |       385.2 |         100
```

**Alerts:**
- ⚠️ If `avg_cost` > $0.25 → Optimization needed
- 🚨 If `max_cost` > $0.40 → Investigate outlier
- ⚠️ If `avg_seconds` > 600 → Performance degradation

---

### **3. Error Analysis**

```sql
-- Error patterns (last 7 days)
SELECT
  enrichment_error,
  COUNT(*) as occurrences,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM golf_courses WHERE enrichment_status = 'error'), 2) as percentage
FROM golf_courses
WHERE enrichment_status = 'error'
  AND enrichment_requested_at > NOW() - INTERVAL '7 days'
GROUP BY enrichment_error
ORDER BY occurrences DESC;
```

**Action Items:**
- If "Timeout" > 20% → Increase timeout or optimize agents
- If "Agent 1 failed" > 10% → Course discovery issue
- If "Hunter.io" > 15% → API key or rate limit problem

---

### **4. Contact Enrichment Quality**

```sql
-- Email/phone/LinkedIn success rates
SELECT
  ROUND(COUNT(*) FILTER (WHERE email IS NOT NULL) * 100.0 / COUNT(*), 2) as email_success_rate,
  ROUND(COUNT(*) FILTER (WHERE phone IS NOT NULL) * 100.0 / COUNT(*), 2) as phone_success_rate,
  ROUND(COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL) * 100.0 / COUNT(*), 2) as linkedin_success_rate,
  COUNT(*) as total_contacts
FROM golf_course_contacts
WHERE enriched_at > NOW() - INTERVAL '7 days';
```

**Expected:**
```
email_success | phone_success | linkedin_success | total_contacts
     50%      |      95%      |       25%        |      450
```

**Alerts:**
- ⚠️ If email_success < 40% → Hunter.io issue
- ⚠️ If phone_success < 80% → Perplexity issue
- ℹ️ LinkedIn = bonus, no alert needed

---

### **5. ClickUp Sync Health**

```sql
-- Contacts without ClickUp tasks
SELECT
  COUNT(*) FILTER (WHERE clickup_task_id IS NOT NULL) as synced,
  COUNT(*) FILTER (WHERE clickup_task_id IS NULL) as not_synced,
  ROUND(COUNT(*) FILTER (WHERE clickup_task_id IS NOT NULL) * 100.0 / COUNT(*), 2) as sync_rate
FROM golf_course_contacts
WHERE enriched_at > NOW() - INTERVAL '7 days';
```

**Expected:**
```
synced | not_synced | sync_rate
  445  |      5     |   98.89%
```

**Alerts:**
- 🚨 If sync_rate < 95% → ClickUp integration broken

---

## 🔧 **Recovery Procedures**

### **Procedure 1: Reset Stuck Processing**

**When:** Courses stuck in 'processing' for > 15 minutes

```sql
-- Step 1: Identify stuck courses
SELECT id, course_name,
       EXTRACT(EPOCH FROM (NOW() - enrichment_requested_at)) / 60 as minutes_stuck
FROM golf_courses
WHERE enrichment_status = 'processing'
  AND enrichment_requested_at < NOW() - INTERVAL '15 minutes';

-- Step 2: Mark as error
UPDATE golf_courses
SET enrichment_status = 'error',
    enrichment_error = 'Timeout: Processing exceeded 15 minutes. Check Render logs.'
WHERE enrichment_status = 'processing'
  AND enrichment_requested_at < NOW() - INTERVAL '15 minutes';

-- Step 3: Review Render logs
-- (Check for agent failures, API issues)

-- Step 4: Retry after fixing root cause
UPDATE golf_courses
SET enrichment_status = 'pending',
    enrichment_error = NULL
WHERE id IN (SELECT id FROM courses_to_retry);
```

---

### **Procedure 2: Bulk Retry Failed Courses**

**When:** Multiple courses failed (e.g., API outage)

```sql
-- Step 1: Review failures
SELECT id, course_name, enrichment_error, enrichment_requested_at
FROM golf_courses
WHERE enrichment_status = 'error'
  AND enrichment_requested_at > NOW() - INTERVAL '24 hours'
ORDER BY enrichment_requested_at DESC;

-- Step 2: Group by error type
SELECT enrichment_error, COUNT(*) as count
FROM golf_courses
WHERE enrichment_status = 'error'
GROUP BY enrichment_error;

-- Step 3: Selective retry (e.g., all "Timeout" errors)
UPDATE golf_courses
SET enrichment_status = 'pending',
    enrichment_error = NULL,
    enrichment_requested_at = NOW()
WHERE enrichment_status = 'error'
  AND enrichment_error LIKE 'Timeout%'
  AND enrichment_requested_at > NOW() - INTERVAL '24 hours';

-- Step 4: Monitor batch completion
SELECT enrichment_status, COUNT(*)
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '1 hour'
GROUP BY enrichment_status;
```

---

### **Procedure 3: Manual Data Entry (Bypass Agents)**

**When:** Agents completely fail but data available externally

```sql
-- Step 1: Mark enrichment as manual
UPDATE golf_courses
SET enrichment_status = 'manual_entry',
    enrichment_error = 'Manually entered - agents unavailable'
WHERE id = 'course-uuid';

-- Step 2: Insert contacts manually
INSERT INTO golf_course_contacts (
  golf_course_id, name, title, email, phone, linkedin_url, segment
) VALUES
  ('course-uuid', 'John Doe', 'GM', 'jdoe@example.com', '123-456-7890', NULL, 'high-end');

-- Step 3: Mark as complete
UPDATE golf_courses
SET enrichment_status = 'complete',
    enrichment_completed_at = NOW()
WHERE id = 'course-uuid';
```

---

### **Procedure 4: Reprocess Contact for ClickUp**

**When:** Contact inserted but ClickUp task missing

```sql
-- Option A: Delete and re-insert (triggers ON INSERT again)
WITH contact_backup AS (
  SELECT * FROM golf_course_contacts WHERE id = 'contact-uuid'
)
DELETE FROM golf_course_contacts WHERE id = 'contact-uuid';

INSERT INTO golf_course_contacts
SELECT * FROM contact_backup;

-- Option B: Manually call edge function
-- (Use Supabase dashboard → Edge Functions → Test)
```

---

### **Procedure 5: Emergency Stop**

**When:** Costs spiraling, need to stop all enrichments

```bash
# Option 1: Suspend Render service (stops all new requests)
# Render Dashboard → Service → Suspend

# Option 2: Disable database trigger
```

```sql
ALTER TABLE golf_courses DISABLE TRIGGER on_enrichment_requested;

-- To re-enable:
ALTER TABLE golf_courses ENABLE TRIGGER on_enrichment_requested;
```

---

## 📈 **Daily Health Check (5 minutes)**

### **Morning Routine:**

```sql
-- 1. Check overnight processing
SELECT
  DATE(enrichment_requested_at) as date,
  COUNT(*) as attempted,
  COUNT(*) FILTER (WHERE enrichment_status = 'complete') as succeeded,
  COUNT(*) FILTER (WHERE enrichment_status = 'error') as failed,
  SUM(agent_cost_usd) as total_cost
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE(enrichment_requested_at);

-- 2. Check for stuck processing
SELECT COUNT(*)
FROM golf_courses
WHERE enrichment_status = 'processing'
  AND enrichment_requested_at < NOW() - INTERVAL '15 minutes';
-- If > 0: Run Procedure 1 (Reset Stuck Processing)

-- 3. Check error rate
SELECT
  ROUND(
    COUNT(*) FILTER (WHERE enrichment_status = 'error') * 100.0 /
    COUNT(*) FILTER (WHERE enrichment_requested_at IS NOT NULL),
    2
  ) as error_rate_percent
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '7 days';
-- If > 10%: Investigate root causes

-- 4. Check ClickUp sync
SELECT COUNT(*)
FROM golf_course_contacts
WHERE enriched_at > NOW() - INTERVAL '24 hours'
  AND clickup_task_id IS NULL;
-- If > 5: Run Procedure 4 (Reprocess for ClickUp)

-- 5. Check cost
SELECT SUM(agent_cost_usd)
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '24 hours';
-- If > $50/day: Cost optimization needed
```

---

## 🔔 **Alerting Rules**

### **Critical Alerts (Immediate Action):**

```sql
-- Alert 1: Error rate > 10%
CREATE VIEW alert_high_error_rate AS
SELECT 'High Error Rate' as alert,
       COUNT(*) FILTER (WHERE enrichment_status = 'error') as errors,
       COUNT(*) as total,
       ROUND(COUNT(*) FILTER (WHERE enrichment_status = 'error') * 100.0 / COUNT(*), 2) as error_rate
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '24 hours'
HAVING COUNT(*) FILTER (WHERE enrichment_status = 'error') * 100.0 / COUNT(*) > 10;

-- Alert 2: Multiple stuck in processing
CREATE VIEW alert_stuck_processing AS
SELECT 'Stuck Processing' as alert,
       COUNT(*) as stuck_count,
       array_agg(course_name) as stuck_courses
FROM golf_courses
WHERE enrichment_status = 'processing'
  AND enrichment_requested_at < NOW() - INTERVAL '15 minutes'
HAVING COUNT(*) > 3;

-- Alert 3: Cost exceeds budget
CREATE VIEW alert_cost_overrun AS
SELECT 'Daily Cost Overrun' as alert,
       DATE(enrichment_requested_at) as date,
       SUM(agent_cost_usd) as daily_cost
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '24 hours'
  AND enrichment_status = 'complete'
GROUP BY DATE(enrichment_requested_at)
HAVING SUM(agent_cost_usd) > 50; -- Alert if > $50/day

-- Check alerts
SELECT * FROM alert_high_error_rate
UNION ALL
SELECT * FROM alert_stuck_processing
UNION ALL
SELECT * FROM alert_cost_overrun;
```

### **Warning Alerts (Monitor):**

- Avg cost > $0.25/course
- Avg duration > 10 minutes
- ClickUp sync < 98%
- Email success < 40%

---

## 🛡️ **Data Integrity Checks**

### **Check 1: Orphaned Contacts**

```sql
-- Contacts without valid course
SELECT c.id, c.name, c.golf_course_id
FROM golf_course_contacts c
LEFT JOIN golf_courses g ON c.golf_course_id = g.id
WHERE g.id IS NULL;

-- Should return 0 rows
```

### **Check 2: Enrichment Without Completion**

```sql
-- Courses marked complete but no contacts
SELECT g.id, g.course_name, g.enrichment_completed_at
FROM golf_courses g
LEFT JOIN golf_course_contacts c ON g.id = c.golf_course_id
WHERE g.enrichment_status = 'complete'
  AND c.id IS NULL;

-- Investigate: Why no contacts found?
```

### **Check 3: Cost Outliers**

```sql
-- Courses with unusually high costs
SELECT id, course_name, agent_cost_usd,
       (SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id) as contact_count
FROM golf_courses
WHERE agent_cost_usd > 0.40 -- Alert if > 2x target cost
ORDER BY agent_cost_usd DESC
LIMIT 10;

-- Investigate: Why so expensive? Too many contacts?
```

---

## 🔄 **Retry Strategies**

### **Automatic Retry (With Backoff):**

```sql
-- Add retry tracking
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0;

-- Retry function with exponential backoff
CREATE OR REPLACE FUNCTION auto_retry_failed()
RETURNS void AS $$
BEGIN
  UPDATE golf_courses
  SET enrichment_status = 'pending',
      enrichment_requested_at = NOW(),
      retry_count = retry_count + 1
  WHERE enrichment_status = 'error'
    AND retry_count < 3
    AND enrichment_requested_at < NOW() - (INTERVAL '1 hour' * POWER(2, retry_count));
    -- Backoff: 1 hour, 2 hours, 4 hours
END;
$$ LANGUAGE plpgsql;

-- Cron job (run every hour)
SELECT cron.schedule('auto-retry-failed', '0 * * * *', 'SELECT auto_retry_failed();');
```

### **Manual Retry (Selective):**

```sql
-- Retry specific course
UPDATE golf_courses
SET enrichment_status = 'pending',
    enrichment_error = NULL,
    retry_count = 0
WHERE id = 'course-uuid';

-- Bulk retry by error type
UPDATE golf_courses
SET enrichment_status = 'pending',
    enrichment_error = NULL
WHERE enrichment_status = 'error'
  AND enrichment_error LIKE 'Render API returned 503%' -- Service unavailable
  AND retry_count < 3;
```

---

## 📋 **Operational Checklists**

### **Weekly Review (30 minutes):**

- [ ] Review all errors from past week
- [ ] Analyze cost trends
- [ ] Check enrichment quality (email/phone success rates)
- [ ] Review ClickUp sync failures
- [ ] Update optimization strategies

### **Monthly Review (2 hours):**

- [ ] Full cost analysis (actual vs projected)
- [ ] Success rate by segment (high-end vs budget)
- [ ] Contact data freshness audit
- [ ] ClickUp usage analysis (sales team feedback)
- [ ] Agent performance tuning
- [ ] Schema optimization (add indexes if needed)

---

## 🚨 **Emergency Procedures**

### **Scenario: Render Service Down**

```bash
# 1. Check service status
curl https://agent7-water-hazards.onrender.com/health

# 2. Check Render dashboard
# https://dashboard.render.com/web/srv-d3peu3t6ubrc73f438m0

# 3. View logs for errors

# 4. If crashed, redeploy
# (Usually auto-restarts, but can force via dashboard)

# 5. Disable trigger while down (prevent error spam)
ALTER TABLE golf_courses DISABLE TRIGGER on_enrichment_requested;

# 6. After recovery, retry failed courses
UPDATE golf_courses
SET enrichment_status = 'pending'
WHERE enrichment_status IN ('processing', 'error')
  AND enrichment_requested_at > NOW() - INTERVAL '2 hours';

# 7. Re-enable trigger
ALTER TABLE golf_courses ENABLE TRIGGER on_enrichment_requested;
```

---

### **Scenario: Supabase Edge Function Down**

```bash
# 1. Check edge function status
supabase functions list

# 2. Check logs
# (Supabase dashboard → Edge Functions → Logs)

# 3. Redeploy function
supabase functions deploy <function-name>

# 4. Test manually
curl -X POST 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/<function-name>' \
  -H 'Content-Type: application/json' \
  -d '{"test": "data"}'

# 5. If working, process backlog
# (Failed webhooks, missing ClickUp tasks, etc.)
```

---

### **Scenario: API Rate Limit Hit**

**Symptoms:**
- Multiple failures with "429 Too Many Requests"
- Affects Hunter.io, Perplexity, or Google APIs

**Recovery:**
```bash
# 1. Identify which API is limited
# Check error messages in enrichment_error

# 2. Pause enrichments temporarily
ALTER TABLE golf_courses DISABLE TRIGGER on_enrichment_requested;

# 3. Wait for rate limit reset (usually hourly or daily)

# 4. Implement rate limiting in agents
# (Code changes needed in agent implementations)

# 5. Batch process with delays
# Instead of 10 courses/hour, do 5 courses/hour with 12-min gaps

# 6. Re-enable trigger
ALTER TABLE golf_courses ENABLE TRIGGER on_enrichment_requested;
```

---

### **Scenario: Mass Data Corruption**

**When:** Bad deployment corrupts data

**Recovery:**
```sql
-- Step 1: Identify scope
SELECT MIN(enriched_at), MAX(enriched_at), COUNT(*)
FROM golf_course_contacts
WHERE enriched_at > '2024-10-XX 00:00:00'; -- Bad deployment timestamp

-- Step 2: Backup before deletion
CREATE TABLE golf_course_contacts_backup_20241018 AS
SELECT * FROM golf_course_contacts
WHERE enriched_at > '2024-10-XX 00:00:00';

-- Step 3: Delete corrupted data
DELETE FROM golf_course_contacts
WHERE enriched_at > '2024-10-XX 00:00:00';

UPDATE golf_courses
SET enrichment_status = NULL,
    enrichment_completed_at = NULL
WHERE enrichment_completed_at > '2024-10-XX 00:00:00';

-- Step 4: Re-enrich affected courses
UPDATE golf_courses
SET enrichment_status = 'pending'
WHERE id IN (SELECT DISTINCT golf_course_id FROM golf_course_contacts_backup_20241018);
```

---

## 📊 **Monitoring Dashboard (SQL Views)**

### Create monitoring views for easy access:

```sql
-- View 1: Current system status
CREATE VIEW v_system_health AS
SELECT
  COUNT(*) FILTER (WHERE enrichment_status = 'pending') as pending,
  COUNT(*) FILTER (WHERE enrichment_status = 'processing') as processing,
  COUNT(*) FILTER (WHERE enrichment_status = 'complete') as completed,
  COUNT(*) FILTER (WHERE enrichment_status = 'error') as errors,
  ROUND(
    COUNT(*) FILTER (WHERE enrichment_status = 'complete') * 100.0 /
    NULLIF(COUNT(*) FILTER (WHERE enrichment_status IN ('complete', 'error')), 0),
    2
  ) as success_rate_percent,
  ROUND(AVG(agent_cost_usd) FILTER (WHERE enrichment_status = 'complete'), 4) as avg_cost,
  ROUND(
    AVG(EXTRACT(EPOCH FROM (enrichment_completed_at - enrichment_requested_at)))
    FILTER (WHERE enrichment_status = 'complete'),
    1
  ) as avg_duration_seconds
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '7 days';

-- View 2: Recent errors
CREATE VIEW v_recent_errors AS
SELECT
  id,
  course_name,
  enrichment_error,
  enrichment_requested_at,
  retry_count,
  EXTRACT(EPOCH FROM (NOW() - enrichment_requested_at)) / 60 as minutes_ago
FROM golf_courses
WHERE enrichment_status = 'error'
  AND enrichment_requested_at > NOW() - INTERVAL '24 hours'
ORDER BY enrichment_requested_at DESC;

-- View 3: Cost analysis
CREATE VIEW v_cost_analysis AS
SELECT
  DATE(enrichment_requested_at) as date,
  COUNT(*) as courses,
  SUM(agent_cost_usd) as daily_cost,
  ROUND(AVG(agent_cost_usd), 4) as avg_per_course,
  ROUND(MIN(agent_cost_usd), 4) as min_cost,
  ROUND(MAX(agent_cost_usd), 4) as max_cost
FROM golf_courses
WHERE enrichment_status = 'complete'
  AND enrichment_requested_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(enrichment_requested_at)
ORDER BY date DESC;

-- Quick access
SELECT * FROM v_system_health;
SELECT * FROM v_recent_errors;
SELECT * FROM v_cost_analysis;
```

---

## 🎯 **SLAs (Service Level Agreements)**

### **Internal SLAs:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Enrichment Success Rate | 95% | Weekly average |
| Max Processing Time | 10 minutes | Per course |
| ClickUp Sync Success | 99% | Weekly average |
| Cost per Course | < $0.25 | Monthly average |
| Error Recovery Time | < 1 hour | From detection to retry |

### **Response Times:**

| Severity | Response Time | Example |
|----------|---------------|---------|
| Critical | 15 minutes | Render service down |
| High | 1 hour | Error rate > 20% |
| Medium | 4 hours | Cost overrun |
| Low | 24 hours | Individual course failure |

---

## 📞 **Escalation Path**

**Level 1: Automated Recovery**
- Retry logic handles transient failures
- Monitoring views show issues

**Level 2: Manual Intervention**
- Use recovery procedures from this playbook
- Check monitoring dashboard
- Review logs

**Level 3: Code Fix Required**
- Agent optimization needed
- Schema changes required
- Infrastructure upgrade

**Level 4: External Dependency**
- API provider outage (Hunter.io, Perplexity)
- Wait for recovery, batch retry

---

## 📚 **Useful Links**

- **Render Dashboard:** https://dashboard.render.com/web/srv-d3peu3t6ubrc73f438m0
- **Supabase Dashboard:** https://supabase.com/dashboard/project/oadmysogtfopkbmrulmq
- **ClickUp Workspace:** (Add your link)
- **Cost Tracking:** See `COST_OPTIMIZATION.md`
- **Edge Functions:** See `EDGE_FUNCTIONS.md`

---

**Last Updated:** October 18, 2024
**Maintained By:** DevOps Team
**Next Review:** Weekly on Mondays
