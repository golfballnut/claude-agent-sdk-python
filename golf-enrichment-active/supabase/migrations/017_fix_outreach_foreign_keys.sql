-- Migration 017: Fix Outreach Foreign Keys and Remove Duplicate Table
-- Created: 2025-11-01
-- Purpose: Fix broken foreign key relationships in outreach system and remove duplicate empty table

-- Context:
-- - outreach_activities (223 rows): Active production table
-- - outreach_activities_agent (0 rows): Duplicate empty table with incorrect foreign key references
-- - outreach_communications and outreach_sequences currently reference the wrong table (_agent)
-- - Need to fix foreign keys to point to the correct active table

-- Risk Assessment: MEDIUM
-- - Foreign key changes require careful validation
-- - All tables currently have 0 rows (communications/sequences) or empty duplicate (activities_agent)
-- - No data loss risk, but need to ensure application code uses correct table name

-- Step 1: Verify current state
-- These should all return 0 to proceed safely
DO $$
DECLARE
    comm_count INTEGER;
    seq_count INTEGER;
    agent_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO comm_count FROM outreach_communications;
    SELECT COUNT(*) INTO seq_count FROM outreach_sequences;
    SELECT COUNT(*) INTO agent_count FROM outreach_activities_agent;

    IF comm_count > 0 OR seq_count > 0 OR agent_count > 0 THEN
        RAISE EXCEPTION 'Safety check failed: Expected 0 rows in outreach_communications (%), outreach_sequences (%), and outreach_activities_agent (%)',
            comm_count, seq_count, agent_count;
    END IF;

    RAISE NOTICE 'Safety check passed: All tables empty as expected';
END $$;

-- Step 2: Drop incorrect foreign key constraints
-- These currently point to outreach_activities_agent (wrong table)
ALTER TABLE outreach_communications
    DROP CONSTRAINT IF EXISTS outreach_communications_outreach_activity_id_fkey;

ALTER TABLE outreach_sequences
    DROP CONSTRAINT IF EXISTS outreach_sequences_outreach_activity_id_fkey;

-- Step 3: Re-add foreign keys pointing to correct table
-- Now pointing to outreach_activities (the active production table)
-- Note: Primary key column is 'activity_id' not 'id'
ALTER TABLE outreach_communications
    ADD CONSTRAINT outreach_communications_outreach_activity_id_fkey
    FOREIGN KEY (outreach_activity_id)
    REFERENCES outreach_activities(activity_id)
    ON DELETE CASCADE;

ALTER TABLE outreach_sequences
    ADD CONSTRAINT outreach_sequences_outreach_activity_id_fkey
    FOREIGN KEY (outreach_activity_id)
    REFERENCES outreach_activities(activity_id)
    ON DELETE CASCADE;

-- Step 4: Drop the duplicate empty table
DROP TABLE IF EXISTS outreach_activities_agent CASCADE;

-- Verification:
-- After applying this migration:
-- - outreach_communications.outreach_activity_id → outreach_activities.activity_id ✓
-- - outreach_sequences.outreach_activity_id → outreach_activities.activity_id ✓
-- - outreach_activities_agent table removed ✓

-- Expected Result:
-- Tables reduced from 20 → 19
-- Foreign keys now point to correct active production table
-- Duplicate empty table removed
