# Data Freshness Strategy
**Agent 8: Contact Freshness Validator**
**Purpose:** Keep contact database current - detect job changes, verify emails, find replacements

---

## The Problem

**Golf course staff turnover is HIGH:**
- General Managers: Average tenure 3-5 years
- Superintendents: Average tenure 4-7 years
- Golf Professionals: Average tenure 2-4 years

**Impact on Our Data:**
- 20-30% of contacts become stale annually
- Email bounces waste outreach efforts
- Calling wrong person damages credibility
- Miss new decision makers

**Solution:** Monthly automated validation + replacement discovery

---

## Agent 8: Contact Freshness Validator

### Trigger (Monthly Cron)

**Supabase Cron Job:**
```sql
-- Run first day of every month
SELECT cron.schedule(
    'monthly-contact-validation',
    '0 2 1 * *',  -- 2am on 1st of month
    $$
    SELECT contact_id, contact_name, contact_title, golf_course_id, linkedin_url, contact_email
    FROM golf_course_contacts
    WHERE (last_verified < NOW() - INTERVAL '30 days' OR last_verified IS NULL)
      AND is_active = true
    LIMIT 100;  -- Process 100 per run (avoid timeouts)
    $$
);
```

**Calls Edge Function:** `validate_contacts_batch`

---

### Agent 8 Workflow (Per Contact)

**Input:**
```json
{
  "contact_id": "uuid",
  "contact_name": "Stacy Foster",
  "contact_title": "General Manager",
  "golf_course_id": 123,
  "golf_course_name": "Richmond Country Club",
  "linkedin_url": "https://linkedin.com/in/stacy-foster-...",
  "contact_email": "sfoster@richmondcountryclubva.com"
}
```

**Step 1: LinkedIn Employment Check (if URL exists)**
```python
if contact.linkedin_url:
    linkedin_data = await scrape_linkedin_profile(contact.linkedin_url)

    # Check current company
    if linkedin_data.current_company != contact.golf_course_name:
        # JOB CHANGE DETECTED!
        changes.append({
            "type": "job_change",
            "old_company": contact.golf_course_name,
            "new_company": linkedin_data.current_company,
            "action": "mark_inactive_find_replacement"
        })
```

**Step 2: Email Deliverability Check**
```python
if contact.contact_email:
    verification = await hunter_verify_email(contact.contact_email)

    if verification.result == 'undeliverable':
        changes.append({
            "type": "email_invalid",
            "action": "update_verification_status"
        })
```

**Step 3: Find Replacement (if job change detected)**
```python
if job_change_detected:
    # Re-run Agent 2 on the golf course
    fresh_data = await agent2_extract_contacts(course.external_directory_url)

    # Find replacement for this role
    replacement = find_contact_by_title(fresh_data.staff, contact.contact_title)

    if replacement:
        # Create new contact record
        new_contact = await create_contact(replacement, golf_course_id)
        # Enrich immediately (Agents 3, 5, 6)
        new_contact = await enrich_contact(new_contact)

        changes.append({
            "type": "replacement_found",
            "new_contact_id": new_contact.contact_id,
            "action": "created_and_enriched"
        })
```

**Step 4: Update Supabase**
```python
updates = {
    "last_verified": NOW(),
}

if job_change_detected:
    updates.update({
        "is_active": False,
        "inactive_reason": 'job_change',
        "job_change_detected": True,
        "current_company": linkedin_data.current_company
    })

if email_invalid:
    updates.update({
        "email_verification_status": 'invalid'
    })

await supabase.from_('golf_course_contacts').update(updates).eq('contact_id', contact_id)
```

**Step 5: Sync to ClickUp**
```python
if job_change_detected:
    # Archive old task, create new task for replacement
    await clickup.update_task(contact.clickup_task_id, status='archived')
    if replacement_found:
        await clickup.create_task(new_contact_data)

if email_invalid:
    # Update custom field, add tag
    await clickup.update_task(contact.clickup_task_id, {
        "custom_fields": {"email_status": "Invalid"},
        "tags": ["email-bounced"]
    })
```

---

## Output

**Per Contact:**
```json
{
  "contact_id": "uuid",
  "status": "current|job_change|email_invalid|both",
  "changes_detected": [
    {
      "type": "job_change",
      "action_taken": "marked_inactive_created_replacement",
      "replacement_contact_id": "new-uuid"
    }
  ],
  "last_verified": "2025-02-01T02:00:00Z",
  "cost": 0.015
}
```

**Batch Summary:**
```json
{
  "total_validated": 100,
  "still_current": 75,
  "job_changes": 20,
  "email_invalid": 10,
  "replacements_found": 15,
  "cost": 1.50
}
```

---

## Supabase Trigger Example (Bi-Directional Sync)

**ClickUp Webhook → Supabase Update:**

```sql
CREATE OR REPLACE FUNCTION sync_clickup_updates()
RETURNS TRIGGER AS $$
BEGIN
    -- Example: Sales rep corrected email in ClickUp
    -- Webhook delivers update to edge function
    -- Edge function updates this contact

    NEW.updated_at = NOW();

    -- Log the sync
    INSERT INTO sync_audit_log (
        contact_id,
        sync_direction,
        changed_fields,
        synced_at
    ) VALUES (
        NEW.contact_id,
        'clickup_to_supabase',
        jsonb_build_object('email', OLD.contact_email, 'new_email', NEW.contact_email),
        NOW()
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## Monthly Freshness Cadence

**Week 1 of Month:** Validate 400 contacts (100/day × 4 days)
**Week 2:** Process results, create replacements
**Week 3:** Sales team updates ClickUp with corrections
**Week 4:** ClickUp → Supabase sync, prepare next batch

**Cost:**
- 400 contacts × $0.015 = $6/month
- Replacement enrichment: 80 contacts × $0.15 = $12/month
- **Total: $18/month** to keep 400 contacts fresh

---

## Your Schema Already Supports This! ✅

**Existing Columns (Perfect for Agent 8):**

`golf_course_contacts`:
- ✅ is_active (boolean) - Mark false when job change
- ✅ inactive_reason (enum) - Set to 'job_change'
- ✅ job_change_detected (boolean) - Flag for review
- ✅ employment_verified (boolean) - Track verification
- ✅ employment_verified_date (timestamp) - When last checked
- ✅ current_company (text) - Where they are now
- ✅ current_position (text) - Current role
- ✅ linkedin_enrichment_status (enum) - Track LinkedIn status
- ✅ email_verification_status (enum) - Track email status
- ✅ last_verified (timestamp) - Agent 8 updates this
- ✅ clickup_task_id (text) - For ClickUp sync

**You built this already - Agent 8 just uses it!**

---

## Recommended Additions

**New Columns (Optional but useful):**
```sql
ALTER TABLE golf_course_contacts
  ADD COLUMN IF NOT EXISTS validation_count INT DEFAULT 0,  -- How many times validated
  ADD COLUMN IF NOT EXISTS replacement_for_contact_id UUID REFERENCES golf_course_contacts(contact_id),  -- If this contact replaced someone
  ADD COLUMN IF NOT EXISTS replaced_by_contact_id UUID REFERENCES golf_course_contacts(contact_id);  -- If this contact was replaced
```

**Create Audit Table:**
```sql
CREATE TABLE contact_validation_log (
  id SERIAL PRIMARY KEY,
  contact_id UUID REFERENCES golf_course_contacts(contact_id),
  validation_date TIMESTAMP DEFAULT NOW(),
  changes_detected JSONB,  -- {job_change: true, email_invalid: false}
  actions_taken JSONB,  -- {marked_inactive: true, replacement_created: true}
  agent8_cost DECIMAL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Next Steps (Document in Handoff)

**Immediate (Next Session):**
1. Apply migration to Supabase
2. Build orchestrator
3. Test on 5 courses
4. Validate data in YOUR Supabase/ClickUp

**Short-Term (Week 1-2):**
5. Multi-state support (directory mapping)
6. Deploy orchestrator to Railway/Render
7. Set up Supabase trigger → Edge function
8. End-to-end automation test

**Medium-Term (Week 3-4):**
9. Build Agent 8 (contact validator)
10. ClickUp webhook → Supabase sync
11. Full system in production

Ready to create these docs?