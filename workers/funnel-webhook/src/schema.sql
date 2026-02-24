-- Cloudflare D1 schema for the burning-man funnel
-- Run: wrangler d1 execute funnel-db --file=src/schema.sql

CREATE TABLE IF NOT EXISTS leads (
  id            TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email         TEXT UNIQUE NOT NULL,
  phone         TEXT,
  first_name    TEXT,
  last_name     TEXT,
  ig_handle     TEXT,
  source        TEXT DEFAULT 'typeform',   -- typeform | manychat | event | organic
  skills        TEXT,                       -- JSON array
  vibe_prefs    TEXT,                       -- JSON array
  location      TEXT,
  status        TEXT DEFAULT 'new',         -- new | nurturing | matched | placed
  brevo_id      TEXT,                       -- Brevo contact ID for dedup
  enrolled_at   TEXT DEFAULT (datetime('now')),
  updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS camps (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  vibe_tags     TEXT,                       -- JSON array: ["art","music","wellness"]
  size          INTEGER,
  open_spots    INTEGER,
  skills_needed TEXT,                       -- JSON array
  description   TEXT,
  contact_email TEXT,
  embedding     BLOB,                       -- float32 cosine embedding, serialized
  updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS matches (
  id            TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  lead_id       TEXT REFERENCES leads(id),
  camp_id       TEXT REFERENCES camps(id),
  score         REAL,
  intro_text    TEXT,                       -- AI-generated warm intro paragraph
  status        TEXT DEFAULT 'pending',     -- pending | sent | accepted | declined
  created_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_leads_email  ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_matches_lead ON matches(lead_id);
