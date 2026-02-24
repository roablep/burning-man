# Setup Guide: Marketing Funnel Stack

Complete these steps in order. Each section depends on the previous one.
Estimated one-time setup. After that, it runs on its own.

---

## Step 0: Prerequisites

- Cloudflare account (free) with at least one domain or `*.pages.dev` subdomain
- Node.js 18+ installed (for Wrangler CLI)
- Brevo account (free) at brevo.com
- Twilio account (free trial) at twilio.com — fund with $10 minimum
- Google Workspace account (existing)
- ManyChat account (free) at manychat.com

---

## Step 1: Typeform — Restructure the Form

1. Log in to Typeform. Open your existing form.
2. Click **Add field** at the very top (before any existing fields).
3. Add **Email** field:
   - Mark as **Required**
   - Label: "Your email address"
4. Add **Phone** field immediately after:
   - Mark as **Required**
   - Label: "Your mobile number (for SMS updates)"
   - Set input type to **Phone number**
5. Move all existing survey/research questions after these two fields.
   Mark them as **Not required**.
6. Go to **Settings → Responses**:
   - Enable **"Save partial responses"** (or similar setting depending on your Typeform plan).
   - This ensures you capture email/phone even if the user abandons the form.
7. Go to **Connect → Webhooks**:
   - Add a new webhook endpoint. Use a placeholder URL for now (update in Step 4).
   - Enable **"Verified responses"** and copy the webhook secret.

---

## Step 2: Brevo — Create Account and Get API Key

1. Sign up at brevo.com (free tier: 300 emails/day, unlimited contacts).
2. Go to **Account → SMTP & API → API Keys**.
3. Create a new API key named "funnel-worker". Copy the key value.
4. Go to **Contacts → Lists**. Create a new list named **"Funnel Leads"**.
   Note the list ID (usually a small integer like `2` or `3`).
5. Update `BREVO_LIST_ID` in `workers/funnel-webhook/src/index.js` line with `listIds: [2]`.
6. Go to **Automations**. You will build Track A and Track B here after the worker is deployed.

---

## Step 3: Twilio — Create Account and Get Credentials

1. Sign up at twilio.com.
2. From the Console dashboard, note:
   - **Account SID** (looks like `ACxxxxxxxx...`)
   - **Auth Token**
3. Go to **Phone Numbers → Manage → Buy a number**.
   - Filter by "SMS capable". Buy a local number (~$1/month).
   - This is your `TWILIO_FROM_NUMBER`.
4. For production SMS, verify a Messaging Service at Messaging → Services (optional but recommended for deliverability).

---

## Step 4: Google Sheets — Create CRM Sheet and Service Account

1. In Google Drive, create a new spreadsheet named **"Burning Man CRM"**.
2. In Sheet 1, rename the tab to **"Leads"**.
3. Add headers in row 1: `Timestamp | Email | Phone | First Name | Last Name | IG Handle | Source | Skills | Vibe Prefs | Location | Status`
4. Copy the spreadsheet ID from the URL (the long alphanumeric string between `/d/` and `/edit`).
5. Go to [console.cloud.google.com](https://console.cloud.google.com):
   - Create a new project (or use an existing one).
   - Enable **Google Sheets API**.
   - Go to **IAM & Admin → Service Accounts → Create Service Account**.
   - Name: `funnel-worker`, Role: Editor.
   - Create a JSON key. Download the file.
6. Back in your Google Sheet, click **Share**. Share with the service account email address (ends in `@...iam.gserviceaccount.com`). Give it **Editor** access.
7. Base64-encode the service account JSON:
   ```bash
   base64 -i service-account.json | tr -d '\n'
   ```
   You'll use this as the `SHEETS_SERVICE_CREDS` secret.

---

## Step 5: Deploy the Cloudflare Worker

```bash
cd workers/funnel-webhook

# Install Wrangler
npm install

# Log in to Cloudflare
npx wrangler login

# Create the D1 database
npx wrangler d1 create funnel-db
# Copy the database_id from the output into wrangler.toml

# Run the schema migration
npx wrangler d1 execute funnel-db --file=src/schema.sql

# Set secrets (run each line, paste value when prompted)
npx wrangler secret put BREVO_API_KEY
npx wrangler secret put TWILIO_ACCOUNT_SID
npx wrangler secret put TWILIO_AUTH_TOKEN
npx wrangler secret put TWILIO_FROM_NUMBER
npx wrangler secret put TYPEFORM_WEBHOOK_SECRET
npx wrangler secret put SHEETS_SPREADSHEET_ID
npx wrangler secret put SHEETS_SERVICE_CREDS

# Deploy
npx wrangler deploy
```

After deploy, Wrangler prints your worker URL:
`https://funnel-webhook.<your-subdomain>.workers.dev`

Verify: `curl https://funnel-webhook.<your-subdomain>.workers.dev/health`
Expected response: `ok`

---

## Step 6: Connect Typeform Webhook

1. Go back to Typeform → Connect → Webhooks.
2. Update the webhook URL to:
   `https://funnel-webhook.<your-subdomain>.workers.dev/webhook/typeform`
3. The webhook secret you copied earlier should match what you set as `TYPEFORM_WEBHOOK_SECRET`.
4. Click **Test Webhook**. Check the Worker logs with `npx wrangler tail` to confirm the payload arrives.

---

## Step 7: Build Brevo Automation Workflows

### Track A: Onboarding Sequence (12 touches)

1. Brevo → Automations → Create Workflow.
2. Trigger: **Contact is added to a list** → Select "Funnel Leads".
3. Build the sequence using **Send Email** + **Wait X days** nodes.
4. For each touch, create an email campaign in Brevo first, then reference it in the workflow.
5. Use the templates in `email-sequences/onboarding-12-step.md`.
6. On Touch 8 and 11, tag the "Get Matched" CTA link:
   - In the Brevo email editor, select the link → add attribute `data-tag: matchmaking-cta`
   - In Brevo Automation settings, add a **Webhook** node to call:
     `POST https://funnel-webhook.<your-subdomain>.workers.dev/webhook/brevo`
     Payload: `{ "event": "click", "tag": "matchmaking-cta", "email": "{{contact.EMAIL}}" }`

### Track B: T-Minus Sequence

1. Brevo → Automations → Create Workflow.
2. Trigger: **A specific date** → set the Burning Man start date (e.g., `2025-08-25`).
3. Use **Wait until X days before** trigger offsets (Brevo supports negative offsets).
4. Use the templates in `email-sequences/t-minus-reminders.md`.

---

## Step 8: ManyChat — Instagram DM Automation

1. Sign up at manychat.com. Connect your Instagram account.
2. Go to **Automation → Instagram Stories Mention** and **Automation → Instagram DMs**.
3. Create a **Keyword Trigger** for DMs:
   - Keywords: `camp`, `burn`, `join`, `info`, `how`, `ticket`, and also catch-all for any DM.
4. Response message:
   ```
   Hey! Thanks for reaching out 🔥

   We're building a resource for people exploring Burning Man for the first
   time — connecting newcomers with the right theme camps and community.

   Fill out this quick form to stay in the loop (takes 60 seconds):
   [Typeform link]

   Any questions? Just reply here.
   ```
5. Add a **Quick Reply button**: "Tell me more" → sends a second message:
   ```
   We run a free matchmaking service connecting people with theme camps
   that fit their vibe, location, and skills.

   Over 12 weeks we'll send you everything you need to know.
   Join here: [Typeform link]
   ```
6. Also set up **Comment Automation** for posts: anyone who comments "info" or "camp"
   gets an automatic DM with the Typeform link.

---

## Step 9: Cloudflare Pages — Event Landing Page

1. Create a new repository (or a `/landing` folder in this repo) with a simple `index.html`.
2. Push to GitHub. In Cloudflare Pages, connect the repo.
3. Deploy: Cloudflare Pages gives you `https://<project>.pages.dev` for free.
4. Content (keep it simple):
   ```html
   <h1>Find Your People at Burning Man</h1>
   <p>We connect first-time Burners with the right theme camp for their vibe,
      skills, and schedule. Free. No cold emails. We make the intro.</p>
   <a href="[Typeform link]">Join Now →</a>
   ```
5. Generate the QR code:
   ```
   https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=https%3A%2F%2F<your>.pages.dev
   ```
   Download this image and use it on event materials.

---

## Step 10: Verify the Full Flow

Run through the complete funnel manually:

1. Submit the Typeform with a test email and phone number.
2. Verify the Cloudflare Worker receives the webhook (check `npx wrangler tail`).
3. Check that the contact appears in Brevo (Contacts list).
4. Check that a welcome SMS arrives on the test phone.
5. Check that a row appears in the Google Sheets CRM.
6. Verify the onboarding automation in Brevo shows the contact as enrolled.
7. Send a test DM to your Instagram → confirm ManyChat auto-reply fires.

---

## Ongoing Maintenance

| Task | Frequency | Owner |
|------|-----------|-------|
| Update ticket dates in T-Minus sequence | January each year | Peter/William |
| Review ManyChat keyword triggers | Monthly | William |
| Check Brevo deliverability / unsubscribe rate | Monthly | William |
| Replenish Twilio balance | When balance < $5 | Anyone |
| Update camp database in D1 | When new placement data is released | Engineering |
| Audit Linktree links | Monthly | William |

---

## Cost Summary at Scale

| Service | Free Tier | Paid Upgrade Trigger |
|---------|-----------|---------------------|
| Brevo | 300 emails/day | > 300 emails/day → $9/mo (5k/day) |
| Twilio | Pay-per-SMS | N/A — ~$0.008/SMS |
| Cloudflare Workers | 100k req/day | > 100k req/day → $5/mo (10M req) |
| Cloudflare D1 | 5 GB | > 5 GB (unlikely at this scale) |
| Cloudflare Pages | Unlimited | Never |
| ManyChat | 1,000 contacts | > 1k contacts → $15/mo |

**Break-even math:** At 500 leads/month, 1 welcome SMS each = ~$4 Twilio.
Everything else free. Total cost: **$4/month** until you hit ManyChat's 1k limit.
After that, $19/month total handles the platform comfortably to 5,000 leads.
