# Golf Enrichment Database Schema

**Last Updated:** November 1, 2025 (Post Phase 2.1 Cleanup)
**Database:** PostgreSQL 17.6.1
**Total Tables:** 17 (reduced from 22, 23% reduction)

---

## Overview

This document describes the final database schema after Phase 2.1 cleanup (Migrations 016-018).

**Cleanup Summary:**
- ✅ Removed 5 redundant/unused tables
- ✅ Fixed broken foreign key relationships
- ✅ Clear separation: production vs test vs staging

---

## Table Categories

### 1. Core Production Tables (6 tables)

#### golf_courses
**Purpose:** Main golf course records
**Rows:** 1,099
**Primary Key:** `id` (integer)
**Key Columns:**
- V2 Research: `course_tier`, `annual_rounds_estimate`, `has_water_hazards`, `water_hazards_count`
- V2 Metadata: `v2_research_json`, `v2_parsed_at`, `v2_validation_flags`, `v2_intelligence`
- Classification: `course_tier_confidence`, `course_tier_evidence`
- Legacy: `segment`, `segment_confidence`, `segment_signals` (pre-V2)

**Foreign Keys:**
- Referenced by: `golf_course_contacts`, `llm_research_staging`, `contact_changes`, `agent_tool_usage`, `outreach_activities`, `opt_out_log`

---

#### golf_course_contacts
**Purpose:** Main contact records for decision makers
**Rows:** 607
**Primary Key:** `contact_id` (uuid)
**Key Columns:**
- Core: `contact_name`, `contact_title`, `contact_email`, `contact_phone`
- Discovery: `contact_source`, `discovery_method`, `source_url`
- LinkedIn: `linkedin_url`, `employment_verified`, `tenure_at_course`
- Email Quality: `email_confidence`, `email_verification_status`, `email_enrichment_provider`
- Status: `is_active`, `inactive_reason`

**Foreign Keys:**
- `golf_course_id` → `golf_courses.id`
- Referenced by: `outreach_communications`, `contact_changes`, `opt_out_log`, `outreach_activities`, `agent_tool_usage`

---

#### llm_research_staging
**Purpose:** V2 JSON staging for manual research paste → validation → database write
**Rows:** 9
**Primary Key:** `id` (uuid)
**Key Columns:**
- Input: `course_name`, `state_code`, `v2_json` (5-section JSON)
- Processing: `status` (pending/processing/validated/validation_failed)
- Errors: `validation_error`
- Timestamps: `created_at`, `processed_at`

**Workflow:**
```
Manual paste → llm_research_staging table
  ↓ DATABASE TRIGGER
Edge Function: validate-v2-research
  ↓ HTTP POST
Render Validator API
  ↓ VALIDATES + PARSES
golf_courses + golf_course_contacts
```

**Foreign Keys:**
- `course_id` → `golf_courses.id`

---

#### outreach_activities
**Purpose:** Campaign tracking for range ball procurement and retrieval programs
**Rows:** 223
**Primary Key:** `activity_id` (uuid)
**Key Columns:**
- Outreach: `outreach_type`, `channel`, `purpose`, `status`
- Purchase Intel: `ball_type`, `turnover_frequency`, `turnover_month`, `next_purchase_date`
- Response: `response_received`, `response_notes`, `next_action`
- ClickUp: `clickup_task_id`, `clickup_sync_status`

**Foreign Keys:**
- `golf_course_id` → `golf_courses.id`
- `contact_id` → `golf_course_contacts.contact_id`
- Referenced by: `outreach_communications`, `outreach_sequences`

---

#### outreach_communications
**Purpose:** Interaction logging (emails, calls, messages)
**Rows:** 0 (ready for use)
**Primary Key:** `id` (uuid)
**Key Columns:**
- Channel: `channel`, `direction` (inbound/outbound)
- Timing: `sent_at`, `received_at`, `opened_at`, `clicked_at`
- Content: `subject`, `body`, `response_text`
- Integration: `email_message_id`, `linkedin_message_id`, `clickup_comment_id`

**Foreign Keys:**
- `outreach_activity_id` → `outreach_activities.activity_id` ✅ FIXED in Migration 017
- `contact_id` → `golf_course_contacts.contact_id`
- `responder_contact_id` → `golf_course_contacts.contact_id`

---

#### outreach_sequences
**Purpose:** Automated follow-up sequences (drip campaigns)
**Rows:** 0 (ready for use)
**Primary Key:** `id` (uuid)
**Key Columns:**
- Sequence: `sequence_type`, `total_steps`, `current_step`, `status`
- Timing: `started_at`, `next_scheduled_at`, `completed_at`
- Response: `response_received`, `response_step`, `response_channel`
- Control: `paused_at`, `paused_by`, `paused_reason`

**Foreign Keys:**
- `outreach_activity_id` → `outreach_activities.activity_id` ✅ FIXED in Migration 017

---

### 2. Test Tables (3 tables)

Created in Migration 015 for Docker validation (Phase 2.3). Safe to truncate.

#### golf_courses_test
**Purpose:** Test courses for Docker validation
**Rows:** 3
**Schema:** Matches `golf_courses` (68 columns)

#### golf_course_contacts_test
**Purpose:** Test contacts for Docker validation
**Rows:** 1
**Schema:** Matches `golf_course_contacts` (53 columns)

#### llm_research_staging_test
**Purpose:** Test staging for Docker validation
**Rows:** 3
**Schema:** Matches `llm_research_staging` (9 columns)

**Usage:**
- Set `USE_TEST_TABLES=true` in validator environment
- Prevents pollution of production data during testing
- Clean with: `TRUNCATE golf_courses_test, golf_course_contacts_test, llm_research_staging_test CASCADE;`

---

### 3. Supporting Tables (8 tables)

#### agent_tool_usage
**Purpose:** Cost tracking and performance metrics for all agent tool calls
**Rows:** 806
**Primary Key:** `usage_id` (uuid)
**Key Columns:**
- Context: `job_id`, `agent_name`, `tool_name`
- Links: `golf_course_id`, `contact_id`
- Performance: `duration_ms`, `cost_usd`, `success`, `error_message`
- Quality: `data_quality_score`, `records_found`

---

#### test_agent_tool_usage
**Purpose:** Test version of agent_tool_usage for SDK development
**Rows:** 0
**Schema:** Similar to `agent_tool_usage` (14 columns)

---

#### city_region_mapping
**Purpose:** Regional assignment fallback when ZIP code unavailable
**Rows:** 290
**Primary Key:** `id` (integer)
**Key Columns:** `city`, `state_code`, `region`

---

#### zipcode_region_mapping
**Purpose:** Primary regional assignment via ZIP code
**Rows:** 5,048
**Primary Key:** `id` (integer)
**Key Columns:** `zipcode`, `state_code`, `region`, `city`, `county`

---

#### contact_changes
**Purpose:** Audit log for contact changes (job changes, email updates, etc.)
**Rows:** 0
**Primary Key:** `id` (uuid)
**Key Columns:**
- Change: `change_type`, `old_value`, `new_value`
- Detection: `detected_at`, `detected_by`, `detection_method`, `confidence`
- Action: `action_taken`, `replacement_contact_id`

**Foreign Keys:**
- `contact_id` → `golf_course_contacts.contact_id`
- `course_id` → `golf_courses.id`
- `replacement_contact_id` → `golf_course_contacts.contact_id`

---

#### opt_out_log
**Purpose:** Compliance tracking for unsubscribe requests
**Rows:** 0
**Primary Key:** `id` (uuid)
**Key Columns:**
- Identity: `contact_id`, `course_id`, `email`
- Opt-out: `opted_out_at`, `opt_out_method`, `opt_out_text`
- Context: `outreach_activity_id`, `communication_id`
- Technical: `ip_address`, `user_agent`

**Foreign Keys:**
- `contact_id` → `golf_course_contacts.contact_id`
- `course_id` → `golf_courses.id`
- `communication_id` → `outreach_communications.id`

---

#### monitoring_checks
**Purpose:** Service health check results with historical tracking
**Rows:** 102
**Primary Key:** `id` (uuid)
**Key Columns:**
- Service: `service_name`, `metric_type`, `metric_value`, `metric_unit`
- Status: `status`, `threshold_breached`, `threshold_level`
- Alerting: `alert_created`, `alert_clickup_task_id`
- Performance: `check_duration_ms`, `api_error`

---

#### monitoring_settings
**Purpose:** Service monitoring configuration
**Rows:** 9
**Primary Key:** `service_name` (text)
**Key Columns:**
- Config: `display_name`, `enabled`, `check_interval_hours`
- Thresholds: `thresholds` (jsonb)
- Alerting: `clickup_task_id`, `clickup_list_id`, `alert_cooldown_hours`
- Method: `monitoring_method`, `api_endpoint`

---

## Tables Removed (Phase 2.1)

### Migration 016: Legacy Apollo Test Tables
- ❌ `test_golf_courses` (5 rows, 50 columns)
- ❌ `test_golf_course_contacts` (23 rows, 54 columns)
- **Reason:** Outdated schema from archived Apollo workflow (pre-Oct 30, 2025)
- **Replaced by:** `golf_courses_test` and `golf_course_contacts_test` (Migration 015)

### Migration 017: Duplicate Outreach Table
- ❌ `outreach_activities_agent` (0 rows, 30 columns)
- **Reason:** Empty duplicate with incorrect foreign key references
- **Fixed:** Foreign keys in `outreach_communications` and `outreach_sequences` now point to `outreach_activities.activity_id`

### Migration 018: Unused Staging Tables
- ❌ `golf_courses_staging` (978 rows, 61 columns)
- ❌ `golf_course_contacts_staging` (0 rows, 52 columns)
- **Reason:** No code references, abandoned manual validation workflow
- **User Confirmed:** Data not needed (2025-11-01)

---

## Key Relationships

### V2 Workflow (Active)
```
llm_research_staging (manual paste)
  → golf_courses (course_id FK)
    → golf_course_contacts (golf_course_id FK)
      → outreach_activities (contact_id FK)
        → outreach_communications (outreach_activity_id FK)
        → outreach_sequences (outreach_activity_id FK)
```

### Tracking & Monitoring
```
agent_tool_usage
  → golf_courses (golf_course_id FK)
  → golf_course_contacts (contact_id FK)

monitoring_checks
  → monitoring_settings (service_name FK)
```

### Regional Assignment
```
golf_courses.zipcode → zipcode_region_mapping.zipcode → region
golf_courses.city → city_region_mapping.city → region (fallback)
```

---

## Migration History

| Migration | Date | Description |
|-----------|------|-------------|
| 013 | Oct 31, 2025 | Create `llm_research_staging` table |
| 014 | Oct 31, 2025 | Add V2 fields to `golf_courses` and `golf_course_contacts` |
| 015 | Oct 31, 2025 | Create test tables for Docker validation |
| 016 | Nov 1, 2025 | Remove legacy Apollo test tables |
| 017 | Nov 1, 2025 | Fix outreach foreign keys, remove duplicate table |
| 018 | Nov 1, 2025 | Remove unused staging tables |

---

## Production vs Test Separation

### Production Tables (Use in production code)
- `golf_courses`
- `golf_course_contacts`
- `llm_research_staging`
- All supporting tables

### Test Tables (Use with `USE_TEST_TABLES=true`)
- `golf_courses_test`
- `golf_course_contacts_test`
- `llm_research_staging_test`

### Validation
```sql
-- Verify test tables are isolated
SELECT COUNT(*) FROM golf_courses_test;        -- Should be small (< 10)
SELECT COUNT(*) FROM golf_course_contacts_test; -- Should be small (< 10)
SELECT COUNT(*) FROM golf_courses;              -- Should be production data (> 1000)
```

---

## Enum Types

### enrichment_status_enum
- `pending`
- `processing`
- `completed`
- `error`
- `manual_entry`
- `ready`

Used by: `golf_courses.enrichment_status`

---

## Best Practices

1. **Use test tables for Docker/SDK testing** - Set `USE_TEST_TABLES=true`
2. **Never delete from production tables** - Use `is_active=false` for soft deletes
3. **Track all changes** - Use `contact_changes` audit log
4. **Monitor costs** - Use `agent_tool_usage` for cost tracking
5. **Respect opt-outs** - Check `opt_out_log` before outreach
6. **Regional assignment** - Prefer ZIP code over city mapping

---

## Schema Statistics

**Total Tables:** 17
**Production Tables:** 6 (35%)
**Test Tables:** 3 (18%)
**Supporting Tables:** 8 (47%)

**Total Rows (Production):**
- golf_courses: 1,099
- golf_course_contacts: 607
- outreach_activities: 223
- agent_tool_usage: 806
- llm_research_staging: 9
- zipcode_region_mapping: 5,048
- city_region_mapping: 290

**Foreign Key Relationships:** 23 total

---

## Future Considerations

### Phase 2.2: Contact Enrichment
- Apollo/Hunter email discovery workflow
- New columns: `apollo_enriched_at`, `hunter_enriched_at`
- Target: ≥70% email discovery rate

### Phase 3: Organization & Scoring
- Organizer agent with deterministic scoring
- New table: `course_scores` (scoring results)
- New columns: `priority_score`, `score_breakdown`

### Phase 4: ClickUp Integration
- Enhanced sync with routing logic
- New columns: `clickup_list_id`, `clickup_outreach_task_id`

---

**END OF SCHEMA DOCUMENTATION**
