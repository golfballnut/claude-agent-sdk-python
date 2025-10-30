-- Migration 005: Outreach Activity & Communication Tracking
-- Purpose: Complete outreach campaign management with communication logging
-- Project: golf-course-outreach (apply to production Supabase)
-- Date: October 18, 2024
--
-- This migration creates:
-- 1. outreach_activities - Campaign tracking (mirrors ClickUp Outreach Activities)
-- 2. outreach_communications - EVERY interaction logged (audit trail)
-- 3. outreach_sequences - Automation state management
-- 4. Edge case handling (opt-outs, contact changes, etc.)
-- 5. Analytics views for reporting

-- ============================================================================
-- PART 1: outreach_activities (Campaign Tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS outreach_activities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- ClickUp Integration
  clickup_task_id TEXT UNIQUE,        -- Link back to ClickUp task
  clickup_folder_id TEXT,              -- Which folder (for filtering)
  clickup_list_id TEXT,                -- Which list

  -- References
  course_id UUID REFERENCES golf_courses(id) ON DELETE CASCADE,
  primary_contact_id UUID REFERENCES golf_course_contacts(id),

  -- Campaign Configuration
  outreach_type TEXT NOT NULL,         -- 'range_ball_buy', 'range_ball_sell', 'range_ball_lease', 'ball_retrieval', etc.
  target_segment TEXT,                 -- Copied from course: 'high-end', 'budget', 'both'
  opportunity_score INT CHECK (opportunity_score BETWEEN 1 AND 10),
  conversation_starter_num INT,        -- Which starter led with (1-5)
  sequence_type TEXT,                  -- '3_email', '5_touch_multi_channel', etc.

  -- Status Tracking
  status TEXT NOT NULL DEFAULT 'scheduled',
  -- Options: 'scheduled', 'active', 'replied', 'meeting_scheduled', 'closed_won', 'closed_lost', 'opted_out', 'contact_left'
  status_updated_at TIMESTAMPTZ,

  -- Timeline
  created_at TIMESTAMPTZ DEFAULT NOW(),
  first_contact_at TIMESTAMPTZ,        -- When first touch sent
  last_contact_at TIMESTAMPTZ,         -- Most recent touch
  response_received_at TIMESTAMPTZ,    -- When they replied
  meeting_booked_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ,

  -- Response Data
  response_channel TEXT,                -- 'email', 'linkedin', 'phone', 'in_person'
  responded BOOLEAN DEFAULT false,
  responded_by_contact_id UUID REFERENCES golf_course_contacts(id),  -- Who actually responded (edge case!)

  -- Outcome
  outcome TEXT,                         -- 'qualified', 'not_interested', 'wrong_contact', 'opted_out', etc.
  outcome_notes TEXT,
  deal_value_usd DECIMAL(10,2),

  -- Metrics
  total_touches INT DEFAULT 0,
  email_opens INT DEFAULT 0,
  email_clicks INT DEFAULT 0,

  -- Cost Attribution
  enrichment_cost_usd DECIMAL(10,4),  -- From agent workflow
  outreach_cost_usd DECIMAL(10,4),     -- Email/LinkedIn costs

  -- Metadata
  created_by TEXT,                      -- 'agent_automation', 'manual', 'api'
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_outreach_by_course ON outreach_activities(course_id, status);
CREATE INDEX IF NOT EXISTS idx_outreach_by_status ON outreach_activities(status, created_at);
CREATE INDEX IF NOT EXISTS idx_outreach_by_segment ON outreach_activities(target_segment, status);
CREATE INDEX IF NOT EXISTS idx_outreach_responded ON outreach_activities(responded, response_received_at) WHERE responded = true;
CREATE INDEX IF NOT EXISTS idx_outreach_clickup ON outreach_activities(clickup_task_id) WHERE clickup_task_id IS NOT NULL;

-- Comments
COMMENT ON TABLE outreach_activities IS 'Tracks outreach campaigns - mirrors ClickUp Outreach Activities list with additional metadata';
COMMENT ON COLUMN outreach_activities.responded_by_contact_id IS 'Edge case: Different contact may respond than originally contacted';

-- ============================================================================
-- PART 2: outreach_communications (EVERY Interaction Logged)
-- ============================================================================

CREATE TABLE IF NOT EXISTS outreach_communications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- References
  outreach_activity_id UUID REFERENCES outreach_activities(id) ON DELETE CASCADE,
  contact_id UUID REFERENCES golf_course_contacts(id),              -- Who we contacted
  responder_contact_id UUID REFERENCES golf_course_contacts(id),   -- Who actually responded (may differ!)

  -- Communication Details
  channel TEXT NOT NULL,                -- 'email', 'linkedin', 'phone', 'in_person'
  direction TEXT NOT NULL,              -- 'outbound', 'inbound'

  -- Timing
  sent_at TIMESTAMPTZ,                  -- When we sent (outbound)
  received_at TIMESTAMPTZ,              -- When they sent (inbound)
  opened_at TIMESTAMPTZ,                -- Email opened (if tracked)
  clicked_at TIMESTAMPTZ,               -- Link clicked (if tracked)

  -- Content (Outbound)
  subject TEXT,
  body TEXT,
  conversation_starter_num INT,         -- Which AI starter used
  sequence_step INT,                    -- Email #1, #2, #3, etc.

  -- Response (Inbound)
  response_text TEXT,
  response_sentiment TEXT,              -- 'positive', 'neutral', 'negative', 'interested', 'not_interested', 'opt_out'
  response_summary TEXT,                 -- AI-generated summary of response
  next_action TEXT,                     -- 'follow_up', 'schedule_meeting', 'send_proposal', 'close', 'disqualify'

  -- External System IDs
  email_message_id TEXT,                -- SendGrid/Mailgun message ID
  email_thread_id TEXT,                 -- Group related emails
  linkedin_message_id TEXT,
  phone_call_recording_url TEXT,
  clickup_comment_id TEXT,             -- Which ClickUp comment
  clickup_subtask_id TEXT,             -- Which subtask this relates to

  -- Edge Case Data
  forwarded_to_email TEXT,             -- If they forwarded to someone
  forwarded_to_name TEXT,
  auto_reply BOOLEAN DEFAULT false,    -- Was this an auto-reply?
  bounce_type TEXT,                    -- 'hard', 'soft', null

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  logged_by TEXT DEFAULT 'system'      -- 'system', 'webhook', 'manual'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_comms_by_activity ON outreach_communications(outreach_activity_id, created_at);
CREATE INDEX IF NOT EXISTS idx_comms_by_channel ON outreach_communications(channel, direction, created_at);
CREATE INDEX IF NOT EXISTS idx_comms_responses ON outreach_communications(direction, response_sentiment) WHERE direction = 'inbound';
CREATE INDEX IF NOT EXISTS idx_comms_by_starter ON outreach_communications(conversation_starter_num, response_sentiment) WHERE conversation_starter_num IS NOT NULL;

-- Comments
COMMENT ON TABLE outreach_communications IS 'Complete audit trail of EVERY communication - email, LinkedIn, phone, in-person';
COMMENT ON COLUMN outreach_communications.responder_contact_id IS 'Edge case: Different person may respond (e.g., GM forwards to procurement)';
COMMENT ON COLUMN outreach_communications.response_sentiment IS 'AI-generated sentiment from response text';

-- ============================================================================
-- PART 3: outreach_sequences (Automation State)
-- ============================================================================

CREATE TABLE IF NOT EXISTS outreach_sequences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- References
  outreach_activity_id UUID REFERENCES outreach_activities(id) ON DELETE CASCADE,

  -- Sequence Configuration
  sequence_type TEXT NOT NULL,          -- 'email_3_touch', 'multi_channel_5_touch', 'custom'
  total_steps INT NOT NULL,
  current_step INT DEFAULT 0,

  -- State
  status TEXT NOT NULL DEFAULT 'active',
  -- Options: 'active', 'paused', 'completed', 'stopped', 'unsubscribed'

  -- Timeline
  started_at TIMESTAMPTZ DEFAULT NOW(),
  next_scheduled_at TIMESTAMPTZ,       -- When next touch should happen
  completed_at TIMESTAMPTZ,

  -- Results
  response_received BOOLEAN DEFAULT false,
  response_step INT,                   -- Which step got response (Email #2, etc.)
  response_channel TEXT,               -- Which channel worked

  -- Automation Control
  paused_at TIMESTAMPTZ,
  paused_by TEXT,                      -- 'user', 'system', 'opt_out', 'error'
  paused_reason TEXT,

  -- A/B Testing
  variant TEXT,                        -- 'A', 'B', 'control'
  test_group TEXT,                     -- For tracking test cohorts

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sequences_active ON outreach_sequences(status, next_scheduled_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_sequences_by_activity ON outreach_sequences(outreach_activity_id);

-- Comments
COMMENT ON TABLE outreach_sequences IS 'Automation state for multi-touch sequences - knows which step to execute next';
COMMENT ON COLUMN outreach_sequences.next_scheduled_at IS 'Cron job checks this to trigger next touch in sequence';

-- ============================================================================
-- PART 4: Opt-Out & Blacklist Management (Compliance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS opt_out_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Who opted out
  contact_id UUID REFERENCES golf_course_contacts(id),
  course_id UUID REFERENCES golf_courses(id),
  email TEXT,

  -- When & How
  opted_out_at TIMESTAMPTZ DEFAULT NOW(),
  opt_out_method TEXT,                  -- 'email_reply', 'unsubscribe_link', 'phone_request', 'linkedin'
  opt_out_text TEXT,                    -- Their exact words

  -- Context
  outreach_activity_id UUID REFERENCES outreach_activities(id),
  communication_id UUID REFERENCES outreach_communications(id),

  -- Compliance
  ip_address INET,
  user_agent TEXT,
  honored_at TIMESTAMPTZ,               -- When we stopped contacting

  -- IMMUTABLE (cannot be deleted, only logged)
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_optout_by_contact ON opt_out_log(contact_id, opted_out_at);
CREATE INDEX IF NOT EXISTS idx_optout_by_email ON opt_out_log(email, opted_out_at);

COMMENT ON TABLE opt_out_log IS 'IMMUTABLE audit log of all opt-out requests for compliance';

-- ============================================================================
-- PART 5: Contact Change Tracking (Edge Cases)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contact_changes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Which contact
  contact_id UUID REFERENCES golf_course_contacts(id),
  course_id UUID REFERENCES golf_courses(id),

  -- What changed
  change_type TEXT NOT NULL,            -- 'left_company', 'title_change', 'email_change', 'inactive', 'duplicate_found'
  old_value TEXT,
  new_value TEXT,

  -- How detected
  detected_at TIMESTAMPTZ DEFAULT NOW(),
  detected_by TEXT,                     -- 'agent_8', 'email_bounce', 'linkedin_check', 'manual'
  detection_method TEXT,
  confidence INT CHECK (confidence BETWEEN 1 AND 10),

  -- Actions Taken
  action_taken TEXT,                    -- 'marked_inactive', 'updated_email', 'found_replacement', etc.
  replacement_contact_id UUID REFERENCES golf_course_contacts(id),

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contact_changes ON contact_changes(contact_id, detected_at);
CREATE INDEX IF NOT EXISTS idx_contact_left ON contact_changes(change_type, detected_at) WHERE change_type = 'left_company';

COMMENT ON TABLE contact_changes IS 'Tracks contact changes over time - job changes, email changes, etc. Critical for data freshness';

-- ============================================================================
-- PART 6: Helper Functions
-- ============================================================================

-- Function: Create outreach activity from enriched course
CREATE OR REPLACE FUNCTION create_outreach_activity_from_enrichment(
  p_course_id UUID,
  p_primary_contact_id UUID,
  p_outreach_type TEXT,
  p_enrichment_cost DECIMAL
)
RETURNS UUID AS $$
DECLARE
  v_activity_id UUID;
  v_course_segment TEXT;
  v_opportunity_score INT;
BEGIN
  -- Get course data
  SELECT segment, opportunities->>p_outreach_type INTO v_course_segment, v_opportunity_score
  FROM golf_courses
  WHERE id = p_course_id;

  -- Create activity
  INSERT INTO outreach_activities (
    course_id,
    primary_contact_id,
    outreach_type,
    target_segment,
    opportunity_score,
    enrichment_cost_usd,
    status,
    created_by
  ) VALUES (
    p_course_id,
    p_primary_contact_id,
    p_outreach_type,
    v_course_segment,
    v_opportunity_score::INT,
    p_enrichment_cost,
    'scheduled',
    'agent_automation'
  )
  RETURNING id INTO v_activity_id;

  RETURN v_activity_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_outreach_activity_from_enrichment IS 'Helper: Create outreach activity after agent enrichment completes';

-- Function: Log communication (inbound or outbound)
CREATE OR REPLACE FUNCTION log_communication(
  p_outreach_activity_id UUID,
  p_channel TEXT,
  p_direction TEXT,
  p_contact_id UUID DEFAULT NULL,
  p_subject TEXT DEFAULT NULL,
  p_body TEXT DEFAULT NULL,
  p_response_text TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  v_comm_id UUID;
BEGIN
  INSERT INTO outreach_communications (
    outreach_activity_id,
    contact_id,
    channel,
    direction,
    sent_at,
    received_at,
    subject,
    body,
    response_text
  ) VALUES (
    p_outreach_activity_id,
    p_contact_id,
    p_channel,
    p_direction,
    CASE WHEN p_direction = 'outbound' THEN NOW() ELSE NULL END,
    CASE WHEN p_direction = 'inbound' THEN NOW() ELSE NULL END,
    p_subject,
    p_body,
    p_response_text
  )
  RETURNING id INTO v_comm_id;

  -- Update activity
  IF p_direction = 'outbound' THEN
    UPDATE outreach_activities
    SET total_touches = total_touches + 1,
        last_contact_at = NOW()
    WHERE id = p_outreach_activity_id;
  ELSIF p_direction = 'inbound' THEN
    UPDATE outreach_activities
    SET responded = true,
        response_received_at = NOW(),
        response_channel = p_channel,
        status = 'replied'
    WHERE id = p_outreach_activity_id;
  END IF;

  RETURN v_comm_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_communication IS 'Helper: Log any communication (email, LinkedIn, phone) with automatic activity updates';

-- Function: Handle opt-out (CRITICAL for compliance)
CREATE OR REPLACE FUNCTION handle_opt_out(
  p_contact_id UUID,
  p_opt_out_text TEXT DEFAULT NULL,
  p_method TEXT DEFAULT 'email_reply'
)
RETURNS BOOLEAN AS $$
DECLARE
  v_course_id UUID;
BEGIN
  -- Get course ID
  SELECT golf_course_id INTO v_course_id
  FROM golf_course_contacts
  WHERE id = p_contact_id;

  -- Mark contact as opted out
  UPDATE golf_course_contacts
  SET opted_out = true,
      opted_out_at = NOW(),
      opt_out_method = p_method,
      do_not_contact = true
  WHERE id = p_contact_id;

  -- Log to immutable audit table
  INSERT INTO opt_out_log (
    contact_id,
    course_id,
    email,
    opted_out_at,
    opt_out_method,
    opt_out_text,
    honored_at
  )
  SELECT
    p_contact_id,
    golf_course_id,
    email,
    NOW(),
    p_method,
    p_opt_out_text,
    NOW()
  FROM golf_course_contacts
  WHERE id = p_contact_id;

  -- Stop ALL active sequences for this contact
  UPDATE outreach_sequences
  SET status = 'unsubscribed',
      paused_at = NOW(),
      paused_by = 'opt_out',
      paused_reason = p_opt_out_text
  WHERE outreach_activity_id IN (
    SELECT id FROM outreach_activities WHERE primary_contact_id = p_contact_id
  );

  -- Update all outreach activities
  UPDATE outreach_activities
  SET status = 'opted_out',
      status_updated_at = NOW(),
      outcome = 'opted_out'
  WHERE primary_contact_id = p_contact_id
    AND status NOT IN ('closed_won', 'closed_lost');

  RETURN true;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION handle_opt_out IS 'CRITICAL: Immediately handle opt-out requests for compliance - stops all sequences';

-- Function: Mark contact as left company
CREATE OR REPLACE FUNCTION mark_contact_left_company(
  p_contact_id UUID,
  p_detection_method TEXT DEFAULT 'email_bounce',
  p_notes TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
  -- Mark contact inactive
  UPDATE golf_course_contacts
  SET is_active = false,
      left_date = NOW(),
      left_reason = p_detection_method
  WHERE id = p_contact_id;

  -- Log change
  INSERT INTO contact_changes (
    contact_id,
    course_id,
    change_type,
    old_value,
    new_value,
    detected_at,
    detected_by,
    detection_method,
    action_taken
  )
  SELECT
    p_contact_id,
    golf_course_id,
    'left_company',
    'active',
    'inactive',
    NOW(),
    'system',
    p_detection_method,
    'marked_inactive'
  FROM golf_course_contacts
  WHERE id = p_contact_id;

  -- Stop active sequences
  UPDATE outreach_sequences
  SET status = 'stopped',
      paused_at = NOW(),
      paused_by = 'contact_left',
      paused_reason = p_notes
  WHERE outreach_activity_id IN (
    SELECT id FROM outreach_activities WHERE primary_contact_id = p_contact_id
  )
  AND status = 'active';

  -- Update outreach activities
  UPDATE outreach_activities
  SET status = 'contact_left',
      status_updated_at = NOW(),
      outcome = 'contact_left',
      outcome_notes = p_notes
  WHERE primary_contact_id = p_contact_id
    AND status IN ('scheduled', 'active', 'replied');

  RETURN true;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION mark_contact_left_company IS 'Handle edge case: Contact left company - stops sequences, marks inactive';

-- ============================================================================
-- PART 7: Analytics Views
-- ============================================================================

-- View: Outreach performance dashboard
CREATE OR REPLACE VIEW v_outreach_performance AS
SELECT
  target_segment,
  outreach_type,
  COUNT(*) as total_campaigns,
  COUNT(*) FILTER (WHERE responded = true) as responses,
  ROUND(COUNT(*) FILTER (WHERE responded = true) * 100.0 / NULLIF(COUNT(*), 0), 2) as response_rate_percent,
  COUNT(*) FILTER (WHERE status = 'meeting_scheduled') as meetings_booked,
  COUNT(*) FILTER (WHERE status = 'closed_won') as closed_won,
  ROUND(AVG(total_touches), 1) as avg_touches_to_response,
  ROUND(AVG(deal_value_usd) FILTER (WHERE status = 'closed_won'), 2) as avg_deal_value,
  SUM(deal_value_usd) FILTER (WHERE status = 'closed_won') as total_revenue
FROM outreach_activities
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY target_segment, outreach_type
ORDER BY target_segment, total_campaigns DESC;

COMMENT ON VIEW v_outreach_performance IS 'Key metrics by segment and opportunity type';

-- View: Communication channel effectiveness
CREATE OR REPLACE VIEW v_channel_effectiveness AS
SELECT
  channel,
  direction,
  COUNT(*) as total_communications,
  COUNT(*) FILTER (WHERE direction = 'inbound') as responses_received,
  ROUND(
    COUNT(*) FILTER (WHERE direction = 'inbound') * 100.0 /
    NULLIF(COUNT(*) FILTER (WHERE direction = 'outbound'), 0),
    2
  ) as response_rate_percent,
  ROUND(
    AVG(EXTRACT(EPOCH FROM (received_at - sent_at)) / 3600)
    FILTER (WHERE direction = 'inbound' AND sent_at IS NOT NULL),
    1
  ) as avg_hours_to_response
FROM outreach_communications
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY channel, direction
ORDER BY channel, direction;

COMMENT ON VIEW v_channel_effectiveness IS 'Which channels work best? Email vs LinkedIn vs Phone';

-- View: Conversation starter effectiveness (A/B testing)
CREATE OR REPLACE VIEW v_conversation_starter_performance AS
SELECT
  conversation_starter_num,
  COUNT(*) as times_used,
  COUNT(*) FILTER (WHERE direction = 'inbound') as got_response,
  ROUND(
    COUNT(*) FILTER (WHERE direction = 'inbound') * 100.0 / NULLIF(COUNT(*), 0),
    2
  ) as response_rate_percent,
  ROUND(AVG(EXTRACT(EPOCH FROM (received_at - sent_at)) / 3600), 1) as avg_hours_to_response,
  array_agg(DISTINCT response_sentiment) FILTER (WHERE response_sentiment IS NOT NULL) as sentiments
FROM outreach_communications
WHERE conversation_starter_num IS NOT NULL
  AND created_at > NOW() - INTERVAL '90 days'
GROUP BY conversation_starter_num
ORDER BY response_rate_percent DESC NULLS LAST;

COMMENT ON VIEW v_conversation_starter_performance IS 'Which AI-generated starters work best? Use for optimization';

-- View: Active sequences needing attention
CREATE OR REPLACE VIEW v_active_sequences AS
SELECT
  s.id as sequence_id,
  s.outreach_activity_id,
  a.status as activity_status,
  s.current_step,
  s.total_steps,
  s.next_scheduled_at,
  g.course_name,
  c.name as contact_name,
  c.email,
  a.outreach_type,
  CASE
    WHEN s.next_scheduled_at < NOW() THEN 'OVERDUE'
    WHEN s.next_scheduled_at < NOW() + INTERVAL '1 hour' THEN 'DUE_SOON'
    ELSE 'SCHEDULED'
  END as urgency
FROM outreach_sequences s
JOIN outreach_activities a ON s.outreach_activity_id = a.id
JOIN golf_courses g ON a.course_id = g.id
JOIN golf_course_contacts c ON a.primary_contact_id = c.id
WHERE s.status = 'active'
  AND s.next_scheduled_at IS NOT NULL
ORDER BY s.next_scheduled_at ASC;

COMMENT ON VIEW v_active_sequences IS 'Shows which sequences need to execute next - used by automation cron job';

-- ============================================================================
-- PART 8: Triggers for Automation
-- ============================================================================

-- Trigger: Auto-update activity timestamp on communication
CREATE OR REPLACE FUNCTION update_activity_on_communication()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.direction = 'inbound' THEN
    UPDATE outreach_activities
    SET responded = true,
        response_received_at = NEW.received_at,
        response_channel = NEW.channel,
        status = 'replied',
        status_updated_at = NOW(),
        responded_by_contact_id = NEW.responder_contact_id
    WHERE id = NEW.outreach_activity_id
      AND responded = false;  -- Only update if not already marked
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_communication_logged ON outreach_communications;
CREATE TRIGGER on_communication_logged
AFTER INSERT ON outreach_communications
FOR EACH ROW
EXECUTE FUNCTION update_activity_on_communication();

COMMENT ON TRIGGER on_communication_logged ON outreach_communications IS 'Auto-update activity status when response received';

-- ============================================================================
-- PART 9: Analytics Queries (For Dashboards)
-- ============================================================================

-- Quick health check
CREATE OR REPLACE FUNCTION get_outreach_health()
RETURNS TABLE (
  metric TEXT,
  value NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT 'total_campaigns'::TEXT, COUNT(*)::NUMERIC FROM outreach_activities
  UNION ALL
  SELECT 'active_campaigns', COUNT(*)::NUMERIC FROM outreach_activities WHERE status IN ('scheduled', 'active', 'replied')
  UNION ALL
  SELECT 'response_rate_percent', ROUND(COUNT(*) FILTER (WHERE responded = true) * 100.0 / NULLIF(COUNT(*), 0), 2)
    FROM outreach_activities
  UNION ALL
  SELECT 'meeting_rate_percent', ROUND(COUNT(*) FILTER (WHERE status = 'meeting_scheduled') * 100.0 / NULLIF(COUNT(*), 0), 2)
    FROM outreach_activities
  UNION ALL
  SELECT 'win_rate_percent', ROUND(COUNT(*) FILTER (WHERE status = 'closed_won') * 100.0 / NULLIF(COUNT(*) FILTER (WHERE status IN ('closed_won', 'closed_lost')), 0), 2)
    FROM outreach_activities
  UNION ALL
  SELECT 'avg_touches_to_response', ROUND(AVG(total_touches) FILTER (WHERE responded = true), 1)
    FROM outreach_activities;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_outreach_health IS 'Quick dashboard: SELECT * FROM get_outreach_health();';

-- ============================================================================
-- PART 10: Data Integrity
-- ============================================================================

-- Ensure outreach activities link to valid contacts
ALTER TABLE outreach_activities
ADD CONSTRAINT fk_outreach_primary_contact
FOREIGN KEY (primary_contact_id)
REFERENCES golf_course_contacts(id)
ON DELETE SET NULL;  -- If contact deleted, keep activity but null the reference

-- Ensure communications link to activities
ALTER TABLE outreach_communications
ADD CONSTRAINT fk_comm_activity
FOREIGN KEY (outreach_activity_id)
REFERENCES outreach_activities(id)
ON DELETE CASCADE;  -- If activity deleted, delete communications too

-- Prevent duplicate active campaigns for same course+type
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_campaign
ON outreach_activities(course_id, outreach_type)
WHERE status IN ('scheduled', 'active', 'replied', 'meeting_scheduled');

COMMENT ON INDEX idx_unique_active_campaign IS 'Prevent duplicate campaigns - only one active campaign per course per opportunity type';

-- ============================================================================
-- PART 11: Sample Data for Testing
-- ============================================================================

-- (DO NOT RUN IN PRODUCTION - for reference only)

/*
-- Example: Create outreach activity after enrichment
SELECT create_outreach_activity_from_enrichment(
  'course-uuid',
  'contact-uuid',
  'range_ball_buy',
  0.2767
);

-- Example: Log outbound email
SELECT log_communication(
  'activity-uuid',
  'email',
  'outbound',
  'contact-uuid',
  'CCV + Range Ball Opportunity',
  'Full email body here...',
  NULL
);

-- Example: Log inbound response
SELECT log_communication(
  'activity-uuid',
  'email',
  'inbound',
  'contact-uuid',
  NULL,
  NULL,
  'Yes, interested! Lets talk.'
);

-- Example: Handle opt-out
SELECT handle_opt_out(
  'contact-uuid',
  'Please remove from your list',
  'email_reply'
);

-- Example: Contact left company
SELECT mark_contact_left_company(
  'contact-uuid',
  'email_auto_reply',
  'Auto-reply: No longer with company'
);
*/

-- ============================================================================
-- PART 12: Migration Completion
-- ============================================================================

-- Verify tables created
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'outreach_activities') THEN
    RAISE EXCEPTION 'Migration failed: outreach_activities table not created';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'outreach_communications') THEN
    RAISE EXCEPTION 'Migration failed: outreach_communications table not created';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'outreach_sequences') THEN
    RAISE EXCEPTION 'Migration failed: outreach_sequences table not created';
  END IF;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'Migration 005 Complete!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Created tables:';
  RAISE NOTICE '  - outreach_activities (campaign tracking)';
  RAISE NOTICE '  - outreach_communications (audit trail)';
  RAISE NOTICE '  - outreach_sequences (automation state)';
  RAISE NOTICE '  - opt_out_log (compliance)';
  RAISE NOTICE '  - contact_changes (edge cases)';
  RAISE NOTICE '';
  RAISE NOTICE 'Created 4 helper functions';
  RAISE NOTICE 'Created 4 analytics views';
  RAISE NOTICE 'Created indexes for performance';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Quick test:';
  RAISE NOTICE '  SELECT * FROM get_outreach_health();';
  RAISE NOTICE '  SELECT * FROM v_outreach_performance;';
  RAISE NOTICE '========================================';
END $$;

-- Log migration
INSERT INTO _migrations (name, applied_at)
VALUES ('005_outreach_tables', NOW())
ON CONFLICT (name) DO UPDATE SET applied_at = NOW();
