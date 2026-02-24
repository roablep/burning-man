# Track B: T-Minus Logistical Reminder Sequence

Configure in **Brevo → Automations → Workflow**.
Trigger: **date-based** — relative to Burning Man start date (last Monday of August).

Set a custom contact attribute `BM_YEAR` = current year. Use Brevo's
"Relative to date" trigger with a fixed anchor date (e.g., `2025-08-25`).

Each reminder is paired with an **SMS ping** sent 15 minutes before the email
via the Brevo webhook → Cloudflare Worker → Twilio pipeline.

---

## T-Minus 6 Months (~February)
**Subject:** "T-6 months: The only thing to do right now"

```
Hey {{contact.FIRSTNAME}},

Six months out. One thing matters right now:

Get on the ticket mailing list at burningman.org so you don't
miss the sale announcement.

That's it. Don't buy anything, don't book anything else yet.
Just make sure you'll know when tickets go on sale.

[Subscribe to Burning Man Ticket Alerts →]

More soon.
```

**SMS (sent 15 min before):**
`[First name], heads up — check your email. We sent you the T-6 month ticket alert. 🔥`

---

## T-Minus 5 Months (~March)
**Subject:** "T-5 months: Tickets open soon — here's the full calendar"

```
Ticket sales are roughly 5 months out. Here's the full schedule
so nothing catches you off guard:

STEP pre-sale lottery: [date range]
Main sale: [date]
OMG sale (last resort): [date]
STEP transfer window: [dates]
Vehicle passes: sold separately, same windows

The main sale sells out in hours. Set a calendar reminder now.

[Full Ticket & Vehicle Pass Guide →]
```

*Update dates each year from burningman.org/tickets.*

---

## T-Minus 4 Months (~April)
**Subject:** "T-4 months: Camp confirmed?"

```
Four months out is when camps finalize their rosters.

If you don't have a camp confirmed by now, the window is
starting to close for established camps. Some smaller or newer
camps are still open.

If you're still looking:

[Use Our Free Matchmaking →]

If you're confirmed: tell your camp lead you got this email —
they'll love knowing their recruits are being prepped.
```

---

## T-Minus 3 Months (~May)
**Subject:** "T-3 months: Gear and the vehicle situation"

```
Three months out is gear season.

The things that are worth spending money on:
- Shade structure (EZ-up or better)
- Sleeping system rated for 30°F nights and 100°F days
- Dust-proof storage bins (gamma-sealed lids)
- Hydration bladder (3L minimum)
- Headlamp + bike lights (required)

The things you don't need to buy new:
- Everything else

If your camp has communal gear, confirm what they're providing
before you buy anything.

[Full Gear Guide →]

Also: if you're driving, your vehicle pass must be sorted now.
```

---

## T-Minus 2 Months (~June)
**Subject:** "T-2 months: Travel, leave, and the pre-burn logistics"

```
Two months out — the logistics get real.

Checklist:
☐ Time off from work confirmed
☐ Travel booked (flight or drive plan)
☐ Camp dues paid (if your camp charges them)
☐ Ticket in hand or on STEP
☐ Vehicle pass secured (if driving)
☐ Sleeping gear sorted

Anything unchecked? Reply and we'll help.

The drive from Reno (nearest major airport) to Black Rock City
is about 2.5 hours under normal conditions. Plan for 4-6 hours
on gate day. Seriously.
```

---

## T-Minus 6 Weeks
**Subject:** "T-6 weeks: Leave No Trace and the LNT mindset"

```
One of Burning Man's most important principles is Leave No
Trace. The desert must be returned to its exact original state.

That means:
- MOOP (Matter Out Of Place) discipline: no glitter, no feathers
  that shed, no single-use plastics on the open playa
- Every camp is inspected post-event
- Camp MOOP scores affect future placement

Your camp lead will cover this. This is just your heads-up so
you're not that person with the sequin jacket that sheds
everywhere.

[LNT Guide for First-Timers →]
```

---

## T-Minus 4 Weeks
**Subject:** "T-4 weeks: Pack your bag — for real this time"

```
One month out. Pack now, not the night before.

The goal: test every piece of gear. Set up your tent in the
backyard. Fill your hydration bladder. Wear your dust mask.

Things people forget:
- Work gloves (for camp build/strike)
- Zip ties (infinite uses)
- A rag for the bike chain
- Electrolytes (not just water — you need salt)
- A physical copy of your ticket and vehicle pass
- Cash for ice ($10/bag at the ice vendor)

Anything your camp provides: confirm in writing by this week.
```

---

## T-Minus 2 Weeks
**Subject:** "T-2 weeks: Final checklist and the mental game"

```
Two weeks out. The logistics are either handled or they're not.
If anything is unchecked, now is the time — not the day before.

The mental game:

The first day or two on playa can be disorienting for newcomers.
The scale, the heat, the dust, the lack of phone signal —
it's overwhelming. This is normal.

Give yourself permission to settle in slowly. You don't have to
see everything. The burn will meet you where you are.

See the final checklist here:

[Pre-Departure Checklist →]
```

---

## T-Minus 3 Days
**Subject:** "T-3 days: You're almost there"

```
Three days.

Last calls:
- Top off your water containers (3 gallons/person/day minimum)
- Download offline maps of the playa (Dust Maps app)
- Print your ticket and vehicle pass — cell service is dead on
  the way in and at gate
- Charge everything the night before you leave
- Set an out-of-office

Your camp is expecting you. They've been building for you.
Show up ready to contribute from day one.

See you on the playa. 🔥
```

**SMS (sent same time as email):**
`You're 3 days out. Check your email — we sent your final checklist. 🔥`

---

## T-Plus 2 Weeks (Post-Event)
**Subject:** "You did it. What now?"

```
Hey {{contact.FIRSTNAME}},

How was it?

The post-burn comedown is real. Returning to "default world" after
a week in Black Rock City is jarring for most people.

A few things to know:

1. The "playa brain" fog lifts in about a week.
2. The community continues year-round — events, camps, regional
   burns.
3. If your camp was a good fit, now is the time to re-up for
   next year. Camps plan 10-12 months out.

We'd love to hear how it went. Reply to this email — what
surprised you most?

And if you want to get more involved — as a camp organizer, an
art builder, or a volunteer — reply with "next level" and we'll
point you in the right direction.
```

---

## Brevo Automation Config Notes

- **Trigger type:** Date-based, relative to anchor date `2025-08-25`
  (update each year in the workflow settings)
- **Audience:** All contacts in "Funnel Leads" list
- **SMS pairing:** Configure Brevo to call the webhook endpoint
  `POST /webhook/brevo` with event `pre_email_send` + tag before
  each high-priority send (T-3 months, T-4 weeks, T-3 days)
- **Suppression:** Contacts tagged `opted_out_sms` should not receive
  the SMS pings — configure in Brevo segmentation
- **Unsubscribe:** All emails must include a compliant unsubscribe
  footer. Brevo handles this automatically.
- **Date updates:** This sequence must be reviewed and date references
  updated every January for the coming burn year.
