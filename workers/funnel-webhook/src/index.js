/**
 * Cloudflare Worker — Funnel Webhook Handler
 *
 * Routes:
 *   POST /webhook/typeform   – Receives Typeform partial/full submissions
 *   POST /webhook/brevo      – Receives Brevo automation events (high-intent signal)
 *   GET  /health             – Simple health check
 *   GET  /qr                 – Redirect to QR code image for event leave-behind
 *
 * Environment secrets (set via `wrangler secret put`):
 *   BREVO_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER,
 *   SHEETS_SERVICE_CREDS (base64 JSON), SHEETS_SPREADSHEET_ID,
 *   TYPEFORM_WEBHOOK_SECRET
 */

const LANDING_PAGE_URL = 'https://burning.pages.dev';  // update to your Pages domain

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === 'GET' && url.pathname === '/health') {
      return new Response('ok', { status: 200 });
    }

    if (request.method === 'GET' && url.pathname === '/qr') {
      const qr = `https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=${encodeURIComponent(LANDING_PAGE_URL)}`;
      return Response.redirect(qr, 302);
    }

    if (request.method === 'POST' && url.pathname === '/webhook/typeform') {
      return handleTypeform(request, env, ctx);
    }

    if (request.method === 'POST' && url.pathname === '/webhook/brevo') {
      return handleBrevoEvent(request, env, ctx);
    }

    return new Response('Not found', { status: 404 });
  },

  // Nightly cron: refresh camp embeddings in D1
  async scheduled(event, env, ctx) {
    ctx.waitUntil(refreshCampEmbeddings(env));
  },
};

// ---------------------------------------------------------------------------
// Typeform webhook handler
// ---------------------------------------------------------------------------

async function handleTypeform(request, env, ctx) {
  // Verify Typeform signature
  if (env.TYPEFORM_WEBHOOK_SECRET) {
    const sig = request.headers.get('Typeform-Signature');
    if (!await verifyTypeformSignature(request.clone(), sig, env.TYPEFORM_WEBHOOK_SECRET)) {
      return new Response('Unauthorized', { status: 401 });
    }
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response('Bad request', { status: 400 });
  }

  const lead = extractLeadFromTypeform(body);
  if (!lead.email) {
    // Partial submission without email — nothing to do
    return new Response('ok', { status: 200 });
  }

  // Run all side-effects concurrently; don't block the response
  ctx.waitUntil(
    Promise.allSettled([
      upsertLeadInD1(lead, env),
      addContactToBrevo(lead, env),
      sendWelcomeSMS(lead, env),
      appendToGoogleSheet(lead, env),
    ])
  );

  return new Response('ok', { status: 200 });
}

// ---------------------------------------------------------------------------
// Brevo event handler (high-intent signal → trigger matchmaking intake)
// ---------------------------------------------------------------------------

async function handleBrevoEvent(request, env, ctx) {
  let events;
  try {
    events = await request.json();
  } catch {
    return new Response('Bad request', { status: 400 });
  }

  // Brevo sends an array of events
  const list = Array.isArray(events) ? events : [events];

  for (const event of list) {
    if (event.event === 'click' && event.tag === 'matchmaking-cta') {
      // User clicked the matchmaking CTA inside a drip email
      ctx.waitUntil(sendMatchmakingInvite(event.email, env));
    }
  }

  return new Response('ok', { status: 200 });
}

// ---------------------------------------------------------------------------
// Lead extraction from Typeform payload
// ---------------------------------------------------------------------------

function extractLeadFromTypeform(payload) {
  const answers = payload?.form_response?.answers ?? [];
  const fields  = payload?.form_response?.definition?.fields ?? [];

  const fieldMap = {};
  for (const field of fields) {
    fieldMap[field.id] = field.title.toLowerCase();
  }

  const lead = { source: 'typeform', skills: [], vibe_prefs: [] };

  for (const answer of answers) {
    const title = fieldMap[answer.field?.id] ?? '';
    const value = getAnswerValue(answer);

    if (/email/i.test(title))                lead.email      = value;
    else if (/phone|sms|text/i.test(title))  lead.phone      = normalizePhone(value);
    else if (/first.?name/i.test(title))     lead.first_name = value;
    else if (/last.?name/i.test(title))      lead.last_name  = value;
    else if (/instagram|ig.?handle/i.test(title)) lead.ig_handle = value;
    else if (/skill/i.test(title))           lead.skills     = toArray(value);
    else if (/vibe|interest/i.test(title))   lead.vibe_prefs = toArray(value);
    else if (/location|city/i.test(title))   lead.location   = value;
  }

  return lead;
}

function getAnswerValue(answer) {
  switch (answer.type) {
    case 'text':           return answer.text   ?? '';
    case 'email':          return answer.email  ?? '';
    case 'phone_number':   return answer.phone_number ?? '';
    case 'choice':         return answer.choice?.label ?? '';
    case 'choices':        return (answer.choices?.labels ?? []).join(', ');
    default:               return String(answer[answer.type] ?? '');
  }
}

function toArray(value) {
  if (Array.isArray(value)) return value;
  return value ? value.split(',').map(s => s.trim()) : [];
}

function normalizePhone(raw) {
  if (!raw) return null;
  const digits = raw.replace(/\D/g, '');
  return digits.length === 10 ? `+1${digits}` : `+${digits}`;
}

// ---------------------------------------------------------------------------
// D1: upsert lead
// ---------------------------------------------------------------------------

async function upsertLeadInD1(lead, env) {
  await env.DB.prepare(`
    INSERT INTO leads (email, phone, first_name, last_name, ig_handle, source, skills, vibe_prefs, location)
    VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)
    ON CONFLICT(email) DO UPDATE SET
      phone      = coalesce(?2, phone),
      first_name = coalesce(?3, first_name),
      updated_at = datetime('now')
  `).bind(
    lead.email,
    lead.phone      ?? null,
    lead.first_name ?? null,
    lead.last_name  ?? null,
    lead.ig_handle  ?? null,
    lead.source,
    JSON.stringify(lead.skills),
    JSON.stringify(lead.vibe_prefs),
    lead.location   ?? null,
  ).run();
}

// ---------------------------------------------------------------------------
// Brevo: create/update contact and trigger onboarding automation
// ---------------------------------------------------------------------------

async function addContactToBrevo(lead, env) {
  const body = {
    email:      lead.email,
    attributes: {
      FIRSTNAME: lead.first_name ?? '',
      LASTNAME:  lead.last_name  ?? '',
      SMS:       lead.phone      ?? '',
    },
    listIds:    [2],   // update list ID to your "Funnel Leads" list in Brevo
    updateEnabled: true,
  };

  const res = await fetch('https://api.brevo.com/v3/contacts', {
    method:  'POST',
    headers: {
      'api-key':      env.BREVO_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error('Brevo upsert failed:', res.status, text);
  }
}

// ---------------------------------------------------------------------------
// Twilio: welcome SMS
// ---------------------------------------------------------------------------

async function sendWelcomeSMS(lead, env) {
  if (!lead.phone) return;

  const firstName = lead.first_name ?? 'there';
  const message   = `Hey ${firstName}! You're in. Watch your inbox — we're sending you everything you need to get started. Questions? Reply here. 🔥`;

  const params = new URLSearchParams({
    From: env.TWILIO_FROM_NUMBER,
    To:   lead.phone,
    Body: message,
  });

  const res = await fetch(
    `https://api.twilio.com/2010-04-01/Accounts/${env.TWILIO_ACCOUNT_SID}/Messages.json`,
    {
      method:  'POST',
      headers: {
        Authorization: 'Basic ' + btoa(`${env.TWILIO_ACCOUNT_SID}:${env.TWILIO_AUTH_TOKEN}`),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params,
    }
  );

  if (!res.ok) {
    const text = await res.text();
    console.error('Twilio SMS failed:', res.status, text);
  }
}

// ---------------------------------------------------------------------------
// Google Sheets: append row to CRM sheet
// ---------------------------------------------------------------------------

async function appendToGoogleSheet(lead, env) {
  if (!env.SHEETS_SERVICE_CREDS || !env.SHEETS_SPREADSHEET_ID) return;

  const token = await getGoogleAccessToken(env.SHEETS_SERVICE_CREDS);
  if (!token) return;

  const row = [
    new Date().toISOString(),
    lead.email,
    lead.phone      ?? '',
    lead.first_name ?? '',
    lead.last_name  ?? '',
    lead.ig_handle  ?? '',
    lead.source,
    (lead.skills   ?? []).join(', '),
    (lead.vibe_prefs ?? []).join(', '),
    lead.location  ?? '',
    'new',   // status
  ];

  const res = await fetch(
    `https://sheets.googleapis.com/v4/spreadsheets/${env.SHEETS_SPREADSHEET_ID}/values/Leads!A:K:append?valueInputOption=USER_ENTERED`,
    {
      method:  'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ values: [row] }),
    }
  );

  if (!res.ok) {
    const text = await res.text();
    console.error('Sheets append failed:', res.status, text);
  }
}

async function getGoogleAccessToken(credsBase64) {
  try {
    const creds = JSON.parse(atob(credsBase64));
    const now   = Math.floor(Date.now() / 1000);
    const claim = {
      iss:   creds.client_email,
      scope: 'https://www.googleapis.com/auth/spreadsheets',
      aud:   'https://oauth2.googleapis.com/token',
      iat:   now,
      exp:   now + 3600,
    };
    // Workers don't have crypto.subtle.sign for RS256 natively in a simple way,
    // so we use the service account's token endpoint directly via a JWT library.
    // For simplicity: use Workerd's Web Crypto API to sign the JWT.
    const jwt   = await signJwt(claim, creds.private_key);
    const res   = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body:   `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`,
    });
    const data  = await res.json();
    return data.access_token ?? null;
  } catch (e) {
    console.error('Google token error:', e);
    return null;
  }
}

async function signJwt(payload, pemKey) {
  const header   = { alg: 'RS256', typ: 'JWT' };
  const enc      = (obj) => btoa(JSON.stringify(obj)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const unsigned = `${enc(header)}.${enc(payload)}`;

  // Import PEM private key
  const keyData  = pemKey.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '');
  const binaryKey = Uint8Array.from(atob(keyData), c => c.charCodeAt(0));
  const cryptoKey = await crypto.subtle.importKey(
    'pkcs8', binaryKey.buffer,
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false, ['sign']
  );

  const sigBuffer = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', cryptoKey, new TextEncoder().encode(unsigned));
  const sig       = btoa(String.fromCharCode(...new Uint8Array(sigBuffer))).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  return `${unsigned}.${sig}`;
}

// ---------------------------------------------------------------------------
// Matchmaking invite (triggered by high-intent Brevo event)
// ---------------------------------------------------------------------------

async function sendMatchmakingInvite(email, env) {
  const MATCHMAKING_FORM_URL = 'https://form.typeform.com/to/MATCHMAKING_FORM_ID'; // update

  const res = await fetch('https://api.brevo.com/v3/smtp/email', {
    method:  'POST',
    headers: {
      'api-key':      env.BREVO_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sender:  { name: 'Burning Man Collective', email: 'hello@yourorg.com' },
      to:      [{ email }],
      subject: "You're ready — let's find your camp",
      htmlContent: `
        <p>Hey,</p>
        <p>You've been learning about the burn, and we think you're ready for the next step.</p>
        <p>We match people like you with theme camps that fit your vibe, skills, and schedule.
           It takes 5 minutes and we handle the intro.</p>
        <p><a href="${MATCHMAKING_FORM_URL}" style="background:#E25822;color:#fff;padding:12px 24px;
           border-radius:4px;text-decoration:none;font-weight:bold;">Find My Camp →</a></p>
        <p>Questions? Just reply to this email.</p>
      `,
    }),
  });

  if (!res.ok) {
    console.error('Matchmaking invite failed:', res.status, await res.text());
  }
}

// ---------------------------------------------------------------------------
// Nightly cron: refresh camp embeddings
// ---------------------------------------------------------------------------

async function refreshCampEmbeddings(env) {
  const camps = await env.DB.prepare('SELECT id, name, vibe_tags, skills_needed, description FROM camps').all();

  for (const camp of camps.results ?? []) {
    const text = [
      camp.name,
      camp.description ?? '',
      (JSON.parse(camp.vibe_tags ?? '[]')).join(' '),
      (JSON.parse(camp.skills_needed ?? '[]')).join(' '),
    ].join('. ');

    const res = await env.AI.run('@cf/baai/bge-large-en-v1.5', { text: [text] });
    const embedding = res?.data?.[0];
    if (!embedding) continue;

    const blob = new Uint8Array(Float32Array.from(embedding).buffer);
    await env.DB.prepare('UPDATE camps SET embedding = ?1, updated_at = datetime(\'now\') WHERE id = ?2')
      .bind(blob, camp.id).run();
  }
}

// ---------------------------------------------------------------------------
// Typeform signature verification
// ---------------------------------------------------------------------------

async function verifyTypeformSignature(request, signature, secret) {
  if (!signature) return false;
  const body    = await request.text();
  const key     = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sigBuf  = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(body));
  const expected = 'sha256=' + Array.from(new Uint8Array(sigBuf)).map(b => b.toString(16).padStart(2, '0')).join('');
  return expected === signature;
}
