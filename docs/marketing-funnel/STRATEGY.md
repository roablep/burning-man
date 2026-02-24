# Marketing Funnel: Strategy & Tech Stack

## Mission

A preparation + matchmaking + resource layer for new builders and participants.
Connect curious newcomers to the right theme camps, acculturate them before
they set foot on playa, and give camp leads a reliable top-of-funnel pipeline.

---

## Tool Inventory

| Layer | Tool | Cost |
|-------|------|------|
| Content / Traffic | Instagram (existing) | Free |
| Traffic Director | Linktree (existing) | Free |
| Lead Capture | Typeform (existing) | Free |
| Email | Google Workspace (existing) | Existing |
| Webhook Glue | Cloudflare Workers | Free (100k req/day) |
| Serverless DB | Cloudflare D1 | Free (5 GB) |
| Email Drip | Brevo (ex-Sendinblue) | Free (300/day, unlimited contacts) |
| SMS | Twilio | Pay-as-you-go (~$0.008/SMS) |
| IG DM Automation | ManyChat | Free (≤1 k contacts) |
| Hosting / QR | Cloudflare Pages | Free |
| Matchmaking AI | Cloudflare Workers AI | Free tier |

**Total monthly cost at 500 leads:** ~$4 in Twilio SMS.
No expensive MarTech SaaS required.

---

## Architecture

```
Instagram Reels / Posts
        │
        ▼
  ManyChat DM Auto-reply ──────────────────────────────┐
  (keyword triggers → send Linktree link)              │
        │                                               │
        ▼                                               │
     Linktree  (simplified: 1 CTA)                     │
        │                                               │
        ▼                                               │
     Typeform  (email + phone REQUIRED on page 1)      │
        │                                               │
        │  Webhook (POST)                               │
        ▼                                               │
  Cloudflare Worker  /webhook/typeform                  │
   ├── Brevo API  → add contact + start drip automation │
   ├── Twilio API → send welcome SMS                    │
   ├── Google Sheets API → append row to CRM sheet      │
   └── D1 Database → store for matchmaking engine       │
                                                        │
        ┌───────────────────────────────────────────────┘
        │
        ▼
   Brevo Automation Workflows
   ├── Track A: Onboarding drip (12 touches, behavior-gated)
   └── Track B: T-Minus reminders (date-triggered)
        │
        ▼ (high-intent signal: opens + clicks 5+ emails)
   Matchmaking Intake Form (Typeform v2)
        │
        ▼
   Cloudflare Worker + Workers AI
   └── Cross-ref D1 camp DB → rank matches → notify camp lead
```

---

## Part 1: Lead Capture Fixes

### 1.1 Typeform Triage (do this first)

1. Open the form in Typeform editor.
2. Move **Email** and **Phone / SMS** to the very first screen.
3. Mark both fields as **Required**.
4. Enable **Partial submissions** (Settings → Responses → Save partial responses).
   - This ensures you capture the contact even if the user abandons after screen 1.
5. Remove or move all "user research" / open-ended questions to later screens.
   - Tag them as optional so they don't block submission.
6. Connect the Typeform webhook to your Cloudflare Worker URL
   (Settings → Connect → Webhooks → add the worker URL).

### 1.2 Linktree Purge

Strip everything except:
- **Primary CTA**: "Join the Community → [Typeform link]"
- **Secondary**: "Upcoming Events → [Cloudflare Pages event page]"
- Remove all Jack Rabbit Speaks links, ePlaya links, deep-wiki links.

The Linktree should read like a bouncer, not a library.

### 1.3 Instagram DM Automation (ManyChat)

Setup is free for ≤1,000 contacts and handles the biggest current gap:
leads who DM you disappearing without capture.

**Step-by-step:**
1. Create a ManyChat account at manychat.com, connect your Instagram.
2. Go to **Automation → Instagram DMs**.
3. Create a **Keyword trigger**: any message containing "camp", "burn", "join",
   "info", "how", or just any inbound DM.
4. Auto-reply template:
   > "Hey! Thanks for reaching out. We're building something special for first-time
   > Burners and camp leads alike. Fill out this quick form to stay in the loop 👇
   > [Typeform link]"
5. Add a **Button** quick reply: "Tell me more" → follow-up message with 2-sentence
   pitch + same link.
6. ManyChat captures their Instagram handle; the Typeform captures email/phone.
   Cross-reference these via the Google Sheets CRM column.

---

## Part 2: Omnichannel Drip (Brevo)

### Why Brevo
- Free tier: unlimited contacts, 300 emails/day (upgrades at $9/mo for 5k/day).
- Built-in automation workflows with behavior triggers (open, click, wait).
- Two-way SMS (add-on, or use Twilio via webhook for cheaper per-SMS cost).
- Transactional API is clean and well-documented.

### Dual Track Architecture

Contacts are tagged at entry (`source: typeform`) and enrolled in both tracks
simultaneously. Tracks run independently; a contact can be on Day 3 of onboarding
and also receive a T-Minus alert on the same day.

**Track A: Onboarding** — see `email-sequences/onboarding-12-step.md`
**Track B: T-Minus** — see `email-sequences/t-minus-reminders.md`

### SMS as a Ping Layer (Twilio)

SMS is not used for long content—it's a pointer:
> "Hey [first name], we just sent you something important. Check your inbox."

This is implemented via Twilio in the Cloudflare Worker at two moments:
1. **Welcome SMS** — fires immediately after Typeform submit (worker handles this).
2. **Ping SMS** — fires before high-value email sends (Brevo webhook → worker →
   Twilio, 15 minutes before email delivery).

---

## Part 3: Matchmaking Engine (Phase 2)

### Data Sources to Ingest
| Source | What | How |
|--------|------|-----|
| Burning Man WWW placement data | Camp locations, themes, vibe tags | Annual CSV download |
| Reddit r/BurningMan | "Looking for camp" posts | Pushshift / RSS scrape |
| Facebook groups | Camp recruitment posts | Manual curation initially |
| ePlaya forums | Structured placement queries | Scrape by keyword |
| Typeform intake | User skills, vibe, location, availability | Already captured |

### Matching Logic (Cloudflare Workers AI)

Cloudflare Workers AI provides free inference via the `@cf/meta/llama-3.1-8b-instruct`
or `@cf/baai/bge-large-en-v1.5` (embeddings) models. No external AI API cost.

**Flow:**
1. User completes Matchmaking Intake Form (Typeform v2, triggered at high-intent
   signal: 5+ opens or a specific "I'm ready" link click in a drip email).
2. Worker embeds their profile using `bge-large-en-v1.5`.
3. Camp profiles (stored in D1, pre-embedded nightly via a cron Worker) are
   cosine-similarity ranked against the user vector.
4. Top 3 matches are surfaced. Instead of a bare list, the LLM generates a
   1-paragraph warm intro for each ("You'd be great for Camp X because…").
5. User chooses. Camp lead gets a structured intro email with the user's profile.

**D1 Schema (camps table):**
```sql
CREATE TABLE camps (
  id         TEXT PRIMARY KEY,
  name       TEXT,
  vibe_tags  TEXT,         -- JSON array: ["art","music","wellness"]
  size       INTEGER,
  open_spots INTEGER,
  skills_needed TEXT,      -- JSON array
  contact_email TEXT,
  embedding  BLOB,         -- float32 array, serialized
  updated_at TEXT
);

CREATE TABLE leads (
  id         TEXT PRIMARY KEY,
  email      TEXT UNIQUE,
  phone      TEXT,
  ig_handle  TEXT,
  source     TEXT,
  skills     TEXT,         -- JSON
  vibe_prefs TEXT,         -- JSON
  enrolled_at TEXT,
  status     TEXT DEFAULT 'new'   -- new | nurturing | matched | placed
);
```

---

## Part 4: Event Leave-Behind (Crossroads Cafe, Feb 28)

The "leave-behind" is a single QR code that goes on a card, slide, or printed
sheet. It should point to a Cloudflare Pages landing page (not directly to
Typeform) so you can track scans and add copy.

**Page:** `burning.pages.dev` (or custom domain via Cloudflare)
**Content:**
- 3-sentence pitch
- Single "Join" button → Typeform
- QR code at bottom (generated via `https://api.qrserver.com/v1/create-qr-code/`)

**Shareable SMS for the night:**
People at the event text this to friends who couldn't attend:
> "Hey—went to an event about Burning Man tonight. These folks are building
> something cool for first-timers. Check it out: [Pages URL]"

---

## Part 5: Immediate Action Items

### Peter
- [ ] Typeform: restructure so email + phone are required on screen 1, enable partial submissions
- [ ] Draft matchmaking product brief for the data-join / AI matching section
- [ ] Share brief with William by Saturday Feb 28

### William
- [ ] Linktree: strip down to 2 links max (CTA + Events)
- [ ] Set up ManyChat (free): connect IG, create keyword trigger, add Typeform link
- [ ] Generate QR code for Crossroads Cafe event leave-behind
- [ ] Deploy Cloudflare Pages landing page (see `workers/funnel-webhook/`)

### Taylor
- [ ] Confirm venue walkthrough schedule for Crossroads Cafe (Feb 28)
- [ ] Align team on digital capture plan for night of event (QR code placement, ManyChat trigger word to announce from stage)

### Engineering (when ready)
- [ ] Deploy `workers/funnel-webhook/` to Cloudflare Workers
- [ ] Set Typeform webhook URL to the worker endpoint
- [ ] Create Brevo account, get API key, add to worker secrets
- [ ] Create Twilio account, get API credentials, add to worker secrets
- [ ] Create Google Sheet "CRM" and set up service account credentials
- [ ] Build Brevo automation workflows (Track A + B) using the sequence templates
