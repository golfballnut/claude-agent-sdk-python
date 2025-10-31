# Render Deployment Guide - Apollo Integration

**Last Updated:** October 29, 2025
**Purpose:** Deploy Agent 2-Apollo to production on Render

---

## Environment Variables to Add on Render

### Required New Variable:

**APOLLO_API_KEY**
- Value: Your Apollo.io Professional API key
- Where: Render Dashboard → Your Service → Environment
- Security: Mark as "Secret" (hidden in logs)

### Existing Variables (Keep):

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `HUNTER_API_KEY` (optional - can keep as backup)

---

## Steps to Add APOLLO_API_KEY on Render

**1. Go to Render Dashboard**
- URL: https://dashboard.render.com/

**2. Select Your Service**
- Click on: `golf-course-enrichment` service (or whatever your service is named)

**3. Navigate to Environment**
- Left sidebar: Click "Environment"
- OR go to: Settings → Environment

**4. Add New Environment Variable**
- Click "Add Environment Variable"
- **Key:** `APOLLO_API_KEY`
- **Value:** Paste your Apollo API key (starts with `7bw2lpovpT...`)
- ☑️ Check "Secret" (hides value in logs/UI)
- Click "Save Changes"

**5. Trigger Redeploy**
- Render will auto-redeploy when env vars change
- OR manually click "Manual Deploy" → "Deploy latest commit"

---

## Verification

After deployment, check logs for:
```
✅ APOLLO_API_KEY found
✅ Apollo.io API connection successful
```

If you see:
```
❌ APOLLO_API_KEY not found in .env
```

Then the environment variable wasn't set correctly.

---

## Testing Checklist

**Before production deploy:**
- [ ] APOLLO_API_KEY added to Render
- [ ] Test deployment successful
- [ ] First course enrichment completes
- [ ] Database writes successful
- [ ] Check Apollo usage: https://app.apollo.io/usage
- [ ] Verify credits being consumed correctly

**After deploy:**
- [ ] Monitor first 10 courses
- [ ] Check credit consumption rate
- [ ] Validate email quality (90%+ confidence)
- [ ] Track costs (should be ~$0.13/course)
- [ ] Watch for API errors

---

## Cost Monitoring

**Monthly Budget:**
- Apollo: $79/month (4,020 credits)
- Target: ~3 credits per course
- 500 courses = 1,500 credits/month
- **Well under limit!**

**Alerts to Set:**
- Credit usage > 3,000/month (75% of limit)
- Cost per course > $0.20
- Email coverage < 50%
- API error rate > 5%

---

## Rollback Plan

If issues arise after deployment:

**1. Disable Apollo Temporarily**
- Remove APOLLO_API_KEY from Render (or comment out)
- Service will fail gracefully
- Revert to old orchestrator

**2. Investigate**
- Check Render logs
- Check Apollo usage dashboard
- Review error messages

**3. Fix and Redeploy**
- Fix issues in teams/ folder
- Test locally
- Sync to production/
- Redeploy

---

## Production URLs

**Render Service:** (your service URL)
**Apollo Dashboard:** https://app.apollo.io/usage
**Supabase:** https://supabase.com/dashboard/project/oadmysogtfopkbmrulmq

---

**Next:** Add APOLLO_API_KEY to Render, then deploy!
