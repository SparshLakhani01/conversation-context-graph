#!/usr/bin/env python3
"""Generate a SYNTHETIC dataset of business conversations.

Every person, company, deal, date, and dollar figure in this file is
invented for demonstration purposes. No real CRM data, no real people,
no real companies. The word SYNTHETIC is attached to the output files
and to every record they contain.

World (all fictional):
  - Vendor: Meridian (a fictional software company)
  - Harborview Medical: prospect, deal DEAL-001 ($96,000/yr, close Dec 12)
  - Beacon Freight: customer, deal DEAL-002 (renewal $145,000/yr, Jan 31)
  - Larkspur Outdoors: prospect, deal DEAL-003 (6-week pilot, 20 users)
  - Ironwood Components: customer with NO open deal (support only)

Output: data/messages.json and data/entities.json
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- registry
PEOPLE = [
    {"id": "P01", "name": "Rachel Kim", "title": "VP Finance",
     "company": "C01", "aliases": ["Rachel", "Rachel Kim"]},
    {"id": "P02", "name": "David Osei", "title": "Director of Operations",
     "company": "C01", "aliases": ["David", "David Osei"]},
    {"id": "P03", "name": "Priya Raman", "title": "Account Executive",
     "company": "C00", "aliases": ["Priya", "Priya Raman"]},
    {"id": "P04", "name": "Tom Alvarez", "title": "Sales Engineer",
     "company": "C00", "aliases": ["Tom", "Tom Alvarez"]},
    {"id": "P05", "name": "Grace Nolan", "title": "CFO",
     "company": "C02", "aliases": ["Grace", "Grace Nolan"]},
    {"id": "P06", "name": "Sam Okafor", "title": "VP Operations",
     "company": "C02", "aliases": ["Sam", "Sam Okafor"]},
    {"id": "P07", "name": "Ingrid Sorensen", "title": "Head of IT",
     "company": "C03", "aliases": ["Ingrid", "Ingrid Sorensen"]},
    {"id": "P08", "name": "Paul Whitaker", "title": "Procurement Manager",
     "company": "C03", "aliases": ["Paul", "Paul Whitaker"]},
]

COMPANIES = [
    {"id": "C00", "name": "Meridian", "aliases": ["Meridian"]},
    {"id": "C01", "name": "Harborview Medical",
     "aliases": ["Harborview", "Harborview Medical"]},
    {"id": "C02", "name": "Beacon Freight",
     "aliases": ["Beacon", "Beacon Freight"]},
    {"id": "C03", "name": "Larkspur Outdoors",
     "aliases": ["Larkspur", "Larkspur Outdoors"]},
    {"id": "C04", "name": "Ironwood Components",
     "aliases": ["Ironwood", "Ironwood Components"]},
]

DEALS = [
    {"id": "D01", "name": "Harborview Medical annual contract",
     "company": "C01", "aliases": ["Harborview deal", "DEAL-001"]},
    {"id": "D02", "name": "Beacon Freight renewal and expansion",
     "company": "C02", "aliases": ["Beacon renewal", "DEAL-002"]},
    {"id": "D03", "name": "Larkspur Outdoors pilot",
     "company": "C03", "aliases": ["Larkspur pilot", "DEAL-003"]},
]

# fact_id -> (statement, [entity ids the fact is about])
FACTS = {
    "F01": ("The Harborview Medical deal is worth $96,000 per year.",
            ["C01", "D01"]),
    "F02": ("Rachel Kim asked for quarterly billing terms for the Harborview Medical deal.",
            ["P01", "C01", "D01"]),
    "F03": ("The Harborview Medical deal is expected to close on December 12.",
            ["C01", "D01"]),
    "F04": ("David Osei is the champion for the Harborview Medical deal.",
            ["P02", "C01", "D01"]),
    "F05": ("A security review is still pending for the Harborview Medical deal.",
            ["C01", "D01"]),
    "F06": ("Harborview Medical is considering a 2-year term.",
            ["C01", "D01"]),
    "F07": ("Harborview Medical has 340 staff across 3 clinics.",
            ["C01"]),
    "F08": ("David Osei is Director of Operations at Harborview Medical.",
            ["P02", "C01"]),
    "F09": ("Rachel Kim is VP Finance at Harborview Medical.",
            ["P01", "C01"]),
    "F10": ("The Beacon Freight renewal is worth $145,000 per year.",
            ["C02", "D02"]),
    "F11": ("The Beacon Freight renewal date is January 31.",
            ["C02", "D02"]),
    "F12": ("Beacon Freight is considering an expansion adding the analytics module and 25 seats.",
            ["C02", "D02"]),
    "F13": ("Beacon Freight's expansion spend needs board approval.",
            ["P05", "C02", "D02"]),
    "F14": ("Sam Okafor wants the Beacon Freight renewal signed before the holidays, by December 19.",
            ["P06", "C02", "D02"]),
    "F15": ("Grace Nolan is CFO at Beacon Freight.",
            ["P05", "C02"]),
    "F16": ("Sam Okafor is VP Operations at Beacon Freight.",
            ["P06", "C02"]),
    "F17": ("Beacon Freight was affected by a service outage on October 28 that was resolved in 2 hours.",
            ["C02"]),
    "F18": ("The Larkspur Outdoors pilot runs for 6 weeks.",
            ["C03", "D03"]),
    "F19": ("The Larkspur Outdoors pilot includes 20 users.",
            ["C03", "D03"]),
    "F20": ("The Larkspur Outdoors pilot's success criterion is cutting invoice processing time by 30%.",
            ["C03", "D03"]),
    "F21": ("Ingrid Sorensen is evaluating the Larkspur Outdoors pilot.",
            ["P07", "C03", "D03"]),
    "F22": ("Larkspur Outdoors will decide on the pilot by January 9.",
            ["C03", "D03"]),
    "F23": ("Paul Whitaker handles vendor onboarding paperwork at Larkspur Outdoors.",
            ["P08", "C03"]),
    "F24": ("Ingrid Sorensen is Head of IT at Larkspur Outdoors.",
            ["P07", "C03"]),
    "F25": ("Paul Whitaker is Procurement Manager at Larkspur Outdoors.",
            ["P08", "C03"]),
    "F26": ("The Larkspur Outdoors pilot starts on November 17.",
            ["C03", "D03"]),
    "F27": ("Ironwood Components has no open deal with Meridian; the relationship is support-only.",
            ["C04"]),
    "F28": ("Ironwood Components renewed its contract back in June.",
            ["C04"]),
    "F29": ("Priya Raman is the Meridian account executive for these accounts.",
            ["P03", "C00"]),
    "F30": ("Tom Alvarez is the Meridian sales engineer supporting these deals.",
            ["P04", "C00"]),
}

# ---------------------------------------------------------------- messages
# (timestamp, channel, sender, participants, subject, body, [fact ids])
RAW = [
    # ---- Harborview Medical / DEAL-001 ----
    ("2026-10-01T09:15:00", "email", "Priya Raman", ["David Osei"],
     "Great meeting you yesterday",
     "Hi David, great speaking yesterday. To recap, Harborview Medical has 340 staff across 3 clinics, "
     "and you kindly agreed to champion this internally. I will send over the proposal draft this week. "
     "Thanks again for the time.", ["F04", "F07", "F08"]),
    ("2026-10-02T14:40:00", "email", "David Osei", ["Priya Raman"],
     "Re: Great meeting you yesterday",
     "Hi Priya, happy to help move this forward. Looping in Rachel Kim, our VP Finance, who will need "
     "to approve the commercial terms. She is the right person for pricing and billing questions.",
     ["F09"]),
    ("2026-10-03T11:05:00", "slack", "Tom Alvarez", ["Priya Raman"],
     "#harborview",
     "Quick note: David Osei confirmed as our champion on the Harborview deal. He runs operations and "
     "has the ear of the executive team. Good sign.", ["F04"]),
    ("2026-10-06T16:20:00", "meeting", "Priya Raman", ["David Osei", "Tom Alvarez"],
     "Discovery recap notes",
     "Discovery recap. Harborview Medical is evaluating a 2-year term. Proposed pricing is $96,000 per "
     "year. David asked for a security overview document before the next meeting.", ["F01", "F06"]),
    ("2026-10-08T10:02:00", "email", "Rachel Kim", ["Priya Raman"],
     "Billing terms question",
     "Hi Priya, thanks for the proposal. Before we go further, could we do quarterly billing instead of "
     "annual prepay? Our finance team strongly prefers quarterly billing for new vendors. Best, Rachel.",
     ["F02", "F09"]),
    ("2026-10-09T09:30:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#harborview",
     "Heads up: Rachel Kim asked for quarterly billing on the Harborview deal. I need to check with our "
     "finance team whether we can accommodate that before I reply.", ["F02"]),
    ("2026-10-13T15:45:00", "email", "Priya Raman", ["Rachel Kim"],
     "Re: Billing terms question",
     "Hi Rachel, good news: we can offer quarterly billing for Harborview Medical. I have updated the "
     "proposal to reflect quarterly billing terms. Let me know if anything else needs adjusting.",
     ["F02"]),
    ("2026-10-15T13:00:00", "meeting", "Tom Alvarez", ["David Osei", "Priya Raman"],
     "Security review kickoff notes",
     "Security review kicked off today. Harborview IT sent over their vendor questionnaire. The security "
     "review is now pending on their side; we expect their questions within a week.", ["F05"]),
    ("2026-10-20T08:55:00", "email", "David Osei", ["Priya Raman"],
     "Security review status",
     "Hi Priya, quick update: the security review is still pending. Our IT team is backlogged this month, "
     "but they have the questionnaire and are working through it.", ["F05"]),
    ("2026-10-27T17:10:00", "slack", "Tom Alvarez", ["Priya Raman"],
     "#harborview",
     "Chasing Harborview IT again today. The security review is still pending and it is now the gating "
     "item for the December timeline.", ["F05"]),
    ("2026-11-03T10:30:00", "email", "Priya Raman", ["David Osei"],
     "Timeline check",
     "Hi David, checking in on timing. We are targeting a December 12 close for the Harborview deal. "
     "Can you confirm that date still works on your side?", ["F03"]),
    ("2026-11-05T12:15:00", "email", "David Osei", ["Priya Raman"],
     "Re: Timeline check",
     "Hi Priya, December 12 works if the security review clears by November 24. I will push IT for an "
     "answer this week. Otherwise we may slip into January.", ["F03", "F05"]),
    ("2026-11-10T09:20:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#harborview",
     "Update: David confirmed the December 12 close target for Harborview, contingent on the security "
     "review. Keeping the forecast as-is for now.", ["F03"]),
    ("2026-11-12T14:00:00", "email", "Rachel Kim", ["Priya Raman"],
     "Budget confirmation",
     "Hi Priya, confirming that $96,000 per year fits our budget, and quarterly billing is confirmed on "
     "our side. Looking forward to getting this wrapped up.", ["F01", "F02"]),
    ("2026-10-19T11:25:00", "email", "David Osei", ["Rachel Kim"],
     "Vendor evaluation update",
     "Hi Rachel, quick internal update: I am championing the Meridian evaluation. They proposed $96,000 "
     "per year and we are leaning toward a 2-year term. The security review is the main open item.",
     ["F06", "F04", "F01"]),
    ("2026-11-06T16:40:00", "email", "Rachel Kim", ["David Osei"],
     "Re: Budget confirmation",
     "David, finance has confirmed the budget for $96,000 per year. I have told Priya we can proceed once "
     "the security review is done.", ["F01", "F09"]),
    ("2026-11-12T18:05:00", "email", "Priya Raman", ["David Osei"],
     "Checking on the security review",
     "Hi David, just checking whether there is any news on the security review. It is still showing as "
     "pending on our tracker, and December 12 depends on it.", ["F05", "F03"]),
    # ---- Beacon Freight / DEAL-002 ----
    ("2026-10-02T09:00:00", "email", "Sam Okafor", ["Priya Raman"],
     "Renewal conversation",
     "Hi Priya, our renewal is coming up and I would like to discuss an expansion alongside it. Can we "
     "set up a call next week? Best, Sam.", ["F16"]),
    ("2026-10-05T15:30:00", "meeting", "Priya Raman", ["Sam Okafor", "Grace Nolan"],
     "Renewal meeting notes",
     "Renewal meeting. The Beacon Freight renewal is $145,000 per year, and the renewal date is "
     "January 31. Sam raised the expansion idea; Grace will review the numbers.", ["F10", "F11"]),
    ("2026-10-07T11:10:00", "email", "Grace Nolan", ["Priya Raman"],
     "Introduction",
     "Hi Priya, I am Grace Nolan, CFO at Beacon Freight. Sam speaks highly of the partnership. Any "
     "expansion spend will need board approval, so please factor that into the timeline.",
     ["F13", "F15"]),
    ("2026-10-09T13:45:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#beacon",
     "Beacon expansion scope is now clear: the analytics module plus 25 additional seats. Tom, can you "
     "prep a demo of the analytics module for Sam's team?", ["F12"]),
    ("2026-10-14T10:20:00", "email", "Sam Okafor", ["Priya Raman"],
     "Timing",
     "Hi Priya, I would like the renewal signed before the holidays, ideally by December 19. Can we "
     "work toward that? The team wants this settled before year end.", ["F14"]),
    ("2026-10-16T09:35:00", "email", "Tom Alvarez", ["Sam Okafor"],
     "Analytics module demo",
     "Hi Sam, the analytics module demo is scheduled for next Tuesday. I will cover the reporting "
     "features your team asked about, including the 25-seat expansion setup.", ["F12"]),
    ("2026-10-21T16:00:00", "meeting", "Tom Alvarez", ["Sam Okafor", "Grace Nolan"],
     "Demo debrief notes",
     "Demo debrief. The analytics module demo went well. Grace reiterated that the expansion needs board "
     "approval, and the board meets in December.", ["F12", "F13"]),
    ("2026-10-28T07:50:00", "slack", "Tom Alvarez", ["Priya Raman"],
     "#beacon-support",
     "Incident: service outage this morning affected Beacon Freight. Resolved in 2 hours. Root cause was "
     "a database failover. Postmortem to follow.", ["F17"]),
    ("2026-10-29T12:30:00", "email", "Priya Raman", ["Grace Nolan"],
     "Outage postmortem and renewal recap",
     "Hi Grace, attaching the postmortem for the October 28 outage, which affected Beacon Freight and "
     "was resolved in 2 hours. Separately, recapping the renewal at $145,000 per year.",
     ["F10", "F17"]),
    ("2026-11-04T15:15:00", "email", "Grace Nolan", ["Priya Raman"],
     "Board timing",
     "Hi Priya, the board meets on December 9. The expansion decision will come after that meeting, "
     "since the expansion spend needs board approval.", ["F13"]),
    ("2026-11-06T10:05:00", "slack", "Sam Okafor", ["Priya Raman"],
     "#beacon",
     "Pushing internally for a December 19 signature on the renewal. Grace is aligned on the renewal "
     "itself; only the expansion waits on the board.", ["F14", "F13"]),
    ("2026-11-11T09:45:00", "email", "Priya Raman", ["Sam Okafor"],
     "Renewal paperwork",
     "Hi Sam, the renewal paperwork is ready for review. Confirming the renewal date of January 31 and "
     "the $145,000 per year figure. Let me know when you have had a chance to review.",
     ["F11", "F10"]),
    ("2026-11-13T14:30:00", "meeting", "Priya Raman", ["Grace Nolan", "Sam Okafor"],
     "Renewal check-in notes",
     "Check-in: Grace confirmed the $145,000 per year renewal. The expansion, adding the analytics "
     "module and 25 seats, is pending board approval.", ["F10", "F13", "F12"]),
    ("2026-10-23T08:40:00", "email", "Grace Nolan", ["Sam Okafor"],
     "Board process",
     "Sam, for the expansion I need a one-page justification before the December board meeting. The "
     "analytics module and 25 seats are the scope. Board approval is required for this spend.",
     ["F13", "F12"]),
    ("2026-11-11T17:25:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#sales",
     "Sam is pushing for a December 19 signature on the Beacon renewal. Renewal itself is straightforward; "
     "expansion is the only piece waiting on the board.", ["F14"]),
    # ---- Larkspur Outdoors / DEAL-003 ----
    ("2026-10-05T13:20:00", "email", "Ingrid Sorensen", ["Priya Raman"],
     "Pilot inquiry",
     "Hi Priya, we are interested in running a pilot. I lead IT at Larkspur Outdoors and would own the "
     "evaluation on our side. Can you share what a pilot typically looks like?", ["F24"]),
    ("2026-10-08T15:00:00", "meeting", "Priya Raman", ["Ingrid Sorensen", "Tom Alvarez"],
     "Pilot scoping notes",
     "Pilot scoping: the Larkspur Outdoors pilot runs for 6 weeks with 20 users, starting November 17. "
     "Ingrid will lead the evaluation.", ["F18", "F19", "F26", "F21"]),
    ("2026-10-12T10:50:00", "email", "Tom Alvarez", ["Ingrid Sorensen"],
     "Pilot plan",
     "Hi Ingrid, attaching the pilot plan. The agreed success criterion is cutting invoice processing "
     "time by 30% over the 6 weeks of the pilot.", ["F20", "F18"]),
    ("2026-10-15T09:15:00", "email", "Paul Whitaker", ["Priya Raman"],
     "Vendor onboarding",
     "Hi Priya, I am Paul Whitaker, Procurement Manager at Larkspur Outdoors. I handle vendor onboarding "
     "paperwork, and I will need your security documentation to get started.", ["F23", "F25"]),
    ("2026-10-19T12:00:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#larkspur",
     "Larkspur update: Ingrid Sorensen is evaluating the pilot, and the decision is due by January 9. "
     "Paul is handling the onboarding paperwork in parallel.", ["F21", "F22", "F23"]),
    ("2026-10-22T14:35:00", "email", "Ingrid Sorensen", ["Priya Raman"],
     "Pilot users",
     "Hi Priya, confirming 20 users for the pilot, drawn from finance and warehouse operations. Let me "
     "know if you need the list of names.", ["F19"]),
    ("2026-10-26T11:20:00", "email", "Paul Whitaker", ["Tom Alvarez"],
     "Onboarding paperwork submitted",
     "Hi Tom, the vendor onboarding paperwork has been submitted to our legal team. I handle the "
     "paperwork on our side, so come to me with any questions.", ["F23"]),
    ("2026-10-30T16:10:00", "meeting", "Priya Raman", ["Ingrid Sorensen", "Paul Whitaker"],
     "Pilot scope lock notes",
     "Pilot scope locked: 6 weeks, 20 users, starting November 17. Success means cutting invoice "
     "processing time by 30%. Ingrid owns the evaluation.", ["F18", "F20", "F19", "F26", "F21"]),
    ("2026-11-02T09:40:00", "slack", "Tom Alvarez", ["Priya Raman"],
     "#larkspur",
     "Reminder: the Larkspur pilot starts November 17. Ingrid is leading the evaluation and has the "
     "technical checklist.", ["F26", "F21"]),
    ("2026-11-07T13:25:00", "email", "Ingrid Sorensen", ["Priya Raman"],
     "Decision meeting",
     "Hi Priya, I have set the internal decision meeting for January 9. We will decide on the pilot by "
     "January 9, based on the invoice processing results.", ["F22", "F20"]),
    ("2026-11-10T10:15:00", "email", "Paul Whitaker", ["Priya Raman"],
     "Onboarding approved",
     "Hi Priya, good news: the vendor onboarding paperwork is approved. We are clear to start the pilot "
     "on November 17.", ["F23", "F26"]),
    ("2026-11-13T08:30:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#larkspur",
     "Kickoff reminder: 20 users confirmed for the Larkspur pilot, starting November 17. Ingrid has the "
     "agenda.", ["F19", "F26"]),
    ("2026-10-28T15:05:00", "email", "Ingrid Sorensen", ["Paul Whitaker"],
     "Evaluation criteria",
     "Hi Paul, for the pilot evaluation I will measure whether we cut invoice processing time by 30%. "
     "That is the success criterion we agreed with Meridian.", ["F20", "F21"]),
    ("2026-11-08T11:45:00", "email", "Tom Alvarez", ["Ingrid Sorensen"],
     "Pilot tech checklist",
     "Hi Ingrid, attaching the technical checklist for the 6 weeks pilot with 20 users. Everything is "
     "ready for the November 17 start.", ["F18", "F19", "F26"]),
    ("2026-11-14T16:55:00", "slack", "Paul Whitaker", ["Priya Raman"],
     "#larkspur",
     "Confirming onboarding is done on my side. The pilot starts November 17 and I have handed the "
     "paperwork file to Ingrid.", ["F23", "F26"]),
    # ---- Ironwood Components (no open deal) ----
    ("2026-10-06T10:30:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#support",
     "Ironwood Components opened a support ticket: their report export is slow. No open deal here, just "
     "support. Can you take a look?", ["F27"]),
    ("2026-10-12T09:20:00", "email", "Tom Alvarez", ["Priya Raman"],
     "Ironwood ticket resolved",
     "Hi Priya, the Ironwood ticket is resolved. For the record, Ironwood Components has no open deal "
     "with us; the relationship is support-only.", ["F27"]),
    ("2026-10-20T13:15:00", "slack", "Tom Alvarez", ["Priya Raman"],
     "#support",
     "Note for the forecast: Ironwood Components renewed back in June and there is nothing open. "
     "Support-only account.", ["F28", "F27"]),
    ("2026-11-09T15:40:00", "email", "Priya Raman", ["Tom Alvarez"],
     "Ironwood QBR",
     "Hi Tom, the Ironwood QBR is scheduled for next month. No expansion discussion planned; this is a "
     "support-only relationship with no open deal.", ["F27"]),
    # ---- Internal / pipeline (distractors and cross-deal context) ----
    ("2026-10-01T08:00:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#sales",
     "Quick intro for the channel: I am the Meridian account executive covering Harborview Medical, "
     "Beacon Freight, and Larkspur Outdoors this quarter.", ["F29"]),
    ("2026-10-03T08:45:00", "slack", "Tom Alvarez", ["Priya Raman"],
     "#sales",
     "And I am the sales engineer supporting all three deals. Ping me for demos, security reviews, or "
     "pilot setup.", ["F30"]),
    ("2026-10-10T12:00:00", "email", "Priya Raman", ["Tom Alvarez"],
     "Weekly pipeline",
     "Hi Tom, weekly pipeline: Harborview at $96,000 per year, Beacon renewal at $145,000 per year, and "
     "the Larkspur pilot running 6 weeks. Harborview security review is the main risk.", 
     ["F01", "F10", "F18", "F05"]),
    ("2026-10-17T17:30:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#sales",
     "Forecast discussion: Harborview closing December 12, Beacon renewal January 31, Larkspur decision "
     "January 9. All three need attention this month.", ["F03", "F11", "F22"]),
    ("2026-10-24T09:10:00", "email", "Tom Alvarez", ["Priya Raman"],
     "Security review status",
     "Hi Priya, security review status across deals: Harborview is still pending, Beacon cleared theirs "
     "last year, and Larkspur's onboarding covers security. Harborview is the only pending one.",
     ["F05"]),
    ("2026-10-31T16:20:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#sales",
     "End of month note: Rachel Kim's quarterly billing request for Harborview is approved. That removes "
     "the last commercial blocker.", ["F02"]),
    ("2026-11-01T11:00:00", "meeting", "Priya Raman", ["Tom Alvarez"],
     "Pipeline review notes",
     "Pipeline review. Champions and evaluators: David Osei champions Harborview, Sam Okafor drives "
     "Beacon, and Ingrid Sorensen is evaluating the Larkspur pilot.", ["F04", "F21"]),
    ("2026-11-05T10:25:00", "slack", "Priya Raman", ["Tom Alvarez"],
     "#sales",
     "Grace Nolan's board meets December 9, which gates the Beacon expansion decision. The renewal "
     "itself is not gated.", ["F13"]),
    ("2026-11-14T15:00:00", "meeting", "Priya Raman", ["Tom Alvarez"],
     "Weekly pipeline notes",
     "Weekly pipeline: Harborview $96,000 per year closing December 12, Beacon renewal $145,000 per year "
     "on January 31, Larkspur decision January 9. Ironwood has nothing open.",
     ["F01", "F10", "F03", "F11", "F22", "F27"]),
]


def build_messages():
    messages = []
    for i, (ts, channel, sender, participants, subject, body, facts) in enumerate(RAW, start=1):
        for fid in facts:
            assert fid in FACTS, f"unknown fact {fid} in message {i}"
        messages.append({
            "id": f"MSG-{i:03d}",
            "timestamp": ts,
            "channel": channel,
            "sender": sender,
            "participants": participants,
            "subject": subject,
            "body": body,
            "facts": facts,
            "synthetic": True,
        })
    return messages


def main():
    messages = build_messages()
    entities = {
        "synthetic": True,
        "people": PEOPLE,
        "companies": COMPANIES,
        "deals": DEALS,
        "facts": {fid: {"statement": stmt, "entities": ents}
                  for fid, (stmt, ents) in FACTS.items()},
    }
    with open(os.path.join(HERE, "messages.json"), "w") as f:
        json.dump({"synthetic": True, "messages": messages}, f, indent=2)
    with open(os.path.join(HERE, "entities.json"), "w") as f:
        json.dump(entities, f, indent=2)
    print(f"wrote {len(messages)} synthetic messages to data/messages.json")
    print(f"registry: {len(PEOPLE)} people, {len(COMPANIES)} companies, "
          f"{len(DEALS)} deals, {len(FACTS)} facts")
    # sanity: every fact is stated by at least one message
    stated = {fid for m in messages for fid in m["facts"]}
    missing = set(FACTS) - stated
    assert not missing, f"facts never stated: {missing}"
    print(f"all {len(FACTS)} facts are stated by at least one message")


if __name__ == "__main__":
    main()
