# Track A: Onboarding Drip Sequence (12 Touches)

Configure in **Brevo → Automations → Workflow**.
Trigger: contact added to list "Funnel Leads" (tag: `source:typeform`).

Behavior-gating: each email fires on a delay. If the contact opens or clicks
an email, Brevo logs that engagement. After 5 opens/clicks the contact is
tagged `high-intent` and becomes eligible for the matchmaking invite (Track B
handles the invite send via the `/webhook/brevo` endpoint).

Use the Brevo **A/B subject line** feature on touches 1, 4, and 8.

---

## Touch 1 — Day 0 (immediate after signup)
**Subject A:** "Welcome to the desert (the digital version)"
**Subject B:** "You just took the first step. Here's what happens next."

```
Hey {{contact.FIRSTNAME}},

You just joined a small group of people who are serious about
experiencing Burning Man — not just watching it on someone's
Instagram story.

Over the next few weeks I'm going to send you the things I wish
I'd known before my first burn. Not the Wikipedia stuff. The
actual stuff.

First up: the one question that separates people who have a
transformative burn from people who have a rough camping trip.

[Read: The Question Everyone Should Ask Before Going →]
```

**CTA button:** Links to a short Cloudflare Pages article (write once, ~400 words):
"What kind of participant do you want to be?" — frames the 10 principles
without being preachy, ends with a poll ("Are you going solo or joining a camp?").

---

## Touch 2 — Day 3
**Subject:** "The 10 Principles aren't a rule book"

```
Hey {{contact.FIRSTNAME}},

Every year, newbies show up having memorized the 10 Principles.
They can recite them. They think they understand them.

Then they're standing in a dust storm at 3am, watching someone
give away a handmade gift they'll carry 2,000 miles home, and it
clicks in a way no blog post could explain.

Here's a quick breakdown of each principle — written for humans,
not for the org's website.

[The 10 Principles, Actually Explained →]
```

**CTA:** Cloudflare Pages article. Keep it irreverent and human.

---

## Touch 3 — Day 7
**Subject:** "What is a theme camp, really?"

```
Burning Man without a camp is like a dinner party where you have
nowhere to sit.

Theme camps are the heartbeat of the event. They provide shade,
structure, community, and purpose. They're also one of the best
ways for first-timers to have an anchored experience instead of
wandering the playa alone.

Here's how they work — and why being part of one is the
difference between a vacation and an experience.

[Theme Camps: The Insider's Guide →]
```

---

## Touch 4 — Day 10
**Subject A:** "What do you actually bring?"
**Subject B:** "The packing list nobody gives you"

```
Gear emails are the least glamorous thing I'll ever send you.
This one's worth reading anyway.

The official packing list is fine. This one is from people who
forgot something expensive (or suffered without it).

[The Packing List That Actually Matters →]

P.S. If you're joining a camp, half of this list changes. More
on that soon.
```

---

## Touch 5 — Day 14
**Subject:** "The thing about tickets"

```
Burning Man tickets are... a whole thing.

Pre-sale. Main sale. STEP (Secure Ticket Exchange). OMG sale.
Low-income tickets. Vehicle passes.

If you don't know these words, you risk missing your window.
Here's the calendar and exactly what to do at each stage.

[Ticket Guide: Don't Miss Your Shot →]
```

**Note:** Update the article each year with real sale dates from
`burningman.org`.

---

## Touch 6 — Day 18
**Subject:** "Surviving the desert (survival is non-negotiable)"

```
People underestimate the desert.

It's not a weekend festival. It's a week in a temporary city
with no running water, extreme heat, dust that gets into
everything, and no Amazon delivery.

Here's the honest survival brief: hydration, foot care, dust
management, and what to do when something goes wrong.

[How to Not Get Hurt on the Playa →]
```

---

## Touch 7 — Day 21 (3 weeks)
**Subject:** "You've been with us 3 weeks. Real talk."

```
Hey {{contact.FIRSTNAME}},

Three weeks in. A few questions:

— Do you know what kind of camp you want to join?
— Do you know anyone who's been before?
— Are you excited, overwhelmed, or both?

All of those are normal. I want to hear where you're at.

Reply to this email — I read them.

If you're ready to take the next step, I have something to show
you next week.
```

**Why:** This touch is the "hand raise" moment. Replies to this email
get a manual follow-up from the human team. Configure Brevo to notify
the team inbox when a reply is received.

---

## Touch 8 — Day 25
**Subject A:** "The people who have the best burns"
**Subject B:** "What separates the good burns from the great ones"

```
After watching hundreds of first-timers go through their first
burn, the pattern is clear:

The people who have the best experiences are the ones who showed
up with a community — not just a campsite.

A camp gives you people to wake up with, a shade structure,
shared meals, a reason to leave the tent, and built-in mentors
who've been doing this for years.

If you haven't found your camp yet, that's what we're here for.

[How Our Matchmaking Works →]   ← tag this link as "matchmaking-cta" in Brevo
```

**Important:** Tag the CTA link in Brevo as `matchmaking-cta`. The
Brevo webhook fires when this link is clicked, which triggers the
matchmaking invite email via the Cloudflare Worker.

---

## Touch 9 — Day 30 (1 month)
**Subject:** "A month in — the logistics reality check"

```
One month of knowing about Burning Man. Here's your checklist:

☐ Tickets secured (or on the STEP waitlist)
☐ Vehicle pass sorted (if driving)
☐ Camp situation confirmed (solo or joined a camp)
☐ Gear list started
☐ Leave from work requested

Which ones are unchecked? Reply and we'll point you in the
right direction.
```

---

## Touch 10 — Day 45
**Subject:** "The art. The reason."

```
Everything else we've talked about — logistics, camps, survival —
is the scaffolding.

The art is the reason.

Burning Man is home to some of the most ambitious, temporary,
collaborative art installations in the world. None of it is for
sale. None of it will survive the week. That's the point.

Here's a look at some of what's been built — and how you can
participate in creating it.

[The Art of Burning Man →]
```

---

## Touch 11 — Day 60 (2 months)
**Subject:** "Two months out. What's your status?"

```
Hey {{contact.FIRSTNAME}},

We're getting closer. Two months is when the real prep starts.

If you're still looking for a camp — or if you've joined one
but have questions — now is the time to connect.

Our matchmaking is free, takes 5 minutes, and we do the intro.
You don't cold-email a camp lead. We make the introduction.

[Get Matched to a Camp →]   ← tag: "matchmaking-cta"
```

---

## Touch 12 — Day 90 (3 months — final onboarding touch)
**Subject:** "This is the last onboarding email. Here's what's next."

```
Hey {{contact.FIRSTNAME}},

This is the last email in the onboarding series.

If you've made it here, you know what you're getting into.
You're ready.

What happens now:

1. Watch your inbox for T-Minus reminders — practical
   deadline alerts as the burn approaches.

2. If you haven't found your camp yet, use the matchmaking
   link below. It's not too late.

3. Tell a friend. The burn is better with people you love.

[One last thing: Find Your Camp →]   ← tag: "matchmaking-cta"

See you on the playa.
```

---

## Brevo Automation Config Notes

- **List:** "Funnel Leads" (list ID 2, update in wrangler + worker)
- **Trigger:** Contact added to list
- **Wait nodes:** Use "Wait X days" between each touch
- **Goal (stop condition):** Contact purchases ticket (set via Brevo custom attribute
  `TICKET_STATUS = confirmed`) OR is tagged `placed`
- **A/B test:** Enable on touches 1, 4, 8 — track open rate, use winner after 200 sends
- **Reply tracking:** On touch 7, set sender to a real monitored inbox
  (your Google Workspace address) so replies hit a human
