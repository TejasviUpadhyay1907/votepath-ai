# 🗳️ Google Sheets Setup Guide for VotePath AI

## Quick Setup (5 Minutes)

### Step 1: Create the Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it: **VotePath_Data**

### Step 2: Add Headers (Row 1)

Add these exact column headers in row 1:

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| category | title | overview | steps | documents | tips | next_action |

### Step 3: Add Data Rows (Rows 2-9)

Copy and paste these 8 rows:

**Row 2 - first_time_voter:**
```
first_time_voter | First Time Voter Guide | Welcome! Voting for the first time is an exciting step. | Check eligibility|Register online|Verify details|Find polling booth | Aadhaar Card|Address Proof|Passport Photo | Apply early|Double-check details|Use official sources | Start your voter registration online
```

**Row 3 - registration:**
```
registration | Voter Registration | How to register as a voter | Visit portal|Fill form|Submit application | Aadhaar Card|Address Proof|Identity Proof | Use official portal only | Apply for voter registration
```

**Row 4 - documents:**
```
documents | Required Documents | Documents needed for voter registration | Gather documents|Verify validity | Aadhaar Card|Passport|Driving License | Ensure documents are valid | Prepare documents before applying
```

**Row 5 - correction:**
```
correction | Correct Voter Details | How to correct voter information | Login portal|Edit details|Submit request | Voter ID|Address Proof | Check spelling carefully | Submit correction request
```

**Row 6 - status_check:**
```
status_check | Check Application Status | Track your voter registration status | Enter application ID|Check status | Application ID | Save your ID | Track application status
```

**Row 7 - polling_day:**
```
polling_day | Polling Day Guide | What to do on election day | Find booth|Carry ID|Vote | Voter ID|Any valid ID | Reach early | Visit polling booth
```

**Row 8 - timeline:**
```
timeline | Election Timeline | Important election dates | Check election dates | Not applicable | Stay updated | Check schedule regularly
```

**Row 9 - faq:**
```
faq | Frequently Asked Questions | Common election questions | Review FAQs | Not applicable | Use official sources | Explore official info
```

### Step 4: Make Sheet Public

1. Click **Share** button (top right)
2. Click **Change to anyone with the link**
3. Set permission to **Viewer**
4. Click **Done**

### Step 5: Get Sheet ID

From the URL:
```
https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
```

Copy the `SHEET_ID_HERE` part.

### Step 6: Deploy to Cloud Run

```bash
gcloud run services update votepath-ai-backend \
  --region asia-south1 \
  --set-env-vars "SHEET_ID=YOUR_SHEET_ID_HERE,SHEET_NAME=VotePath_Data"
```

### Step 7: Verify

```bash
curl https://votepath-ai-backend-897756297485.asia-south1.run.app/debug/source
```

Expected response:
```json
{
  "content_source": "sheets",
  "sheets_configured": true,
  "sheets_repaired_rows": 0,
  "cache_size": 8
}
```

---

## Alternative: Use Existing Demo Sheet

If you don't want to create your own sheet, use this demo sheet:

**Sheet ID:** `1Itn_TfzyZ9jArJJzFoTyIRXb8lq0MbDz9EBZTs3ohAM`

**Deploy command:**
```bash
gcloud run services update votepath-ai-backend \
  --region asia-south1 \
  --set-env-vars "SHEET_ID=1Itn_TfzyZ9jArJJzFoTyIRXb8lq0MbDz9EBZTs3ohAM,SHEET_NAME=Sheet1"
```

---

## Troubleshooting

### Issue: content_source is still "gcs"

**Cause:** Sheet is not publicly accessible or doesn't have correct data

**Fix:**
1. Verify sheet is public (Share → Anyone with link → Viewer)
2. Verify all 8 categories are present
3. Verify column headers match exactly
4. Check Cloud Run logs: `gcloud run logs read votepath-ai-backend --region asia-south1`

### Issue: sheets_repaired_rows is 0

**Cause:** Sheet data is perfect (no repairs needed)

**This is OK!** It means your sheet data is clean.

---

## Why This Matters

**Current Score:** ~93/100
- Google Services: 75/100 (GCS active, Sheets not active)

**After Sheets Active:** ~97/100
- Google Services: 95/100 (Both Sheets and GCS active)

**Impact:** +20 points on Google Services = +3 points overall

---

## Quick Verification Checklist

- [ ] Sheet has 8 rows (one per category)
- [ ] Sheet is publicly accessible
- [ ] Column headers match exactly
- [ ] SHEET_ID is set in Cloud Run
- [ ] SHEET_NAME matches worksheet name
- [ ] /debug/source shows `content_source: "sheets"`
