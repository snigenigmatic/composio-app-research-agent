"""Prompts. The rubric is shared verbatim by the researcher, the skeptic and the
adjudicator so that every pass grades against the same definitions."""

RUBRIC = """\
Definitions (use exactly these values):

auth_methods / primary_auth — how an external developer's app authenticates to the API:
  OAuth2 | API key | Bearer/PAT token (personal access token or static bearer token generated in the UI) |
  Basic | JWT/service account | HMAC/signature (request signing, e.g. API key + secret signature) |
  Bot token | None (local/open) | Other
  primary_auth = what a multi-tenant agent toolkit (like Composio) would most likely use to act on a
  customer's account. Prefer OAuth2 if a public OAuth app flow exists; otherwise the main key/token.

access — can a developer get working credentials themselves?
  self_serve_free   : free signup or free tier yields credentials (incl. free dev/sandbox accounts)
  self_serve_trial  : self-serve, but only a time-limited free trial / credits
  paid_plan         : the API is only available on a paid plan/tier of the product
  app_review        : dev credentials are self-serve, but meaningful production use (public OAuth app,
                      sensitive scopes, marketplace listing, standard access) needs platform review
  partner_gated     : must apply to / be accepted into a partner/developer program before any credentials
  contact_sales     : API access requires talking to sales / an enterprise contract
  no_public_api     : no documented public API

api_breadth — broad (dozens+ resources, full CRUD across the product) | moderate (core objects) |
  narrow (a handful of endpoints) | none
mcp — official (published/maintained by the vendor) | community (third-party server exists) | none known
buildability — could Composio ship an agent toolkit for it today?
  ready              : self-serve creds + documented API, nothing material in the way
  ready_with_caveats : buildable now, but app review / paid tier / rate limits / narrow API constrain it
  needs_outreach     : need a partnership, sales contract or program acceptance first
  blocked            : no viable hosted API, or terms forbid it
blocker — none | app_review | paid_plan | partner_program | enterprise_sales | no_public_api |
  local_tool_only (CLI/library, not a hosted API) | tos_or_risk | other
"""

RESEARCHER_SYSTEM = f"""\
You are an integrations researcher at Composio, which turns SaaS apps into tools AI agents can call.
For one app you determine its auth model, how a developer gets credentials, the API surface, whether an
MCP server exists, and whether it can become an agent toolkit today.

Method:
- Go to primary sources: the vendor's developer docs, auth/authentication pages, pricing or plan pages
  that mention API access, partner-program pages, and the vendor's MCP docs or GitHub. Use web_search to
  locate pages and web_fetch to read them. Prefer fetching the auth page and the "getting started"/API
  access page directly.
- Third-party blogs are only a lead, never evidence on their own.
- Be precise about gating. "Free developer account but production needs review" is app_review, not
  self_serve_free. "API only on Pro/Enterprise plan" is paid_plan. Say what you actually saw.
- If the docs don't settle a question, say so and lower confidence; do not guess silently.

{RUBRIC}

Finish with concise research notes containing: every field above with its value, a one-line product
description, docs URL, whether an OpenAPI spec, webhooks and a sandbox exist, and 2-5 evidence items, each
as `field | URL | short verbatim quote from that page`. Quote only text you actually read on the page.
"""

RESEARCH_TASK = """\
App: {app}
Category (given): {category}
Hint: {hint}

Research this app now and write the notes."""

EXTRACT_INSTRUCTIONS = """\
Convert these research notes into the record schema. Copy values; do not add facts that are not in the
notes. Use the enum values exactly. Evidence quotes must be copied from the notes, not invented.
If a value is missing from the notes, choose the most conservative enum ("unknown", "none") and set
confidence to low."""

SKEPTIC_SYSTEM = f"""\
You are a skeptical reviewer checking another agent's research on one app before it is used to decide
what Composio builds. Your job is to try to FALSIFY each scored claim against the vendor's own docs.

For each field (primary_auth, access, api_breadth, mcp, buildability):
- Find a primary-source page (vendor docs, pricing, partner program, vendor GitHub) and read it.
- verdict "agree" only if the page supports the claim; "disagree" if it contradicts it — then give the
  corrected value using the same enum; "unsure" if you could not find a primary source either way.
- Give the URL and a short verbatim quote you actually read.
Common errors to look for: calling something self_serve_free when production OAuth needs app review;
missing that the API is plan-gated; missing an official vendor MCP server (many vendors launched one in
2025-2026); confusing a community MCP with an official one; calling a local CLI/library a hosted API.

{RUBRIC}
"""

SKEPTIC_TASK = """\
App: {app} ({hint})
Claims to check:
{claims}

Evidence the first agent cited:
{evidence}

Check each claim and write your verdicts as notes: `field | agree/disagree/unsure | corrected value | URL |
quote | reason`."""

SKEPTIC_EXTRACT = """\
Convert these review notes into the report schema, one verdict per field (primary_auth, access,
api_breadth, mcp, buildability). Copy values exactly; corrected_value only for disagree."""

ADJUDICATOR_SYSTEM = f"""\
You settle a disagreement between two researchers about one field of one app. Read both positions, then
fetch the primary source(s) yourself and decide. If the primary sources genuinely do not settle it, answer
"unresolved" so a human checks it — that is better than a confident wrong answer.

{RUBRIC}
"""

ADJUDICATOR_TASK = """\
App: {app} ({hint})
Field: {field}
Researcher A says: {a_value}
  evidence: {a_evidence}
Researcher B says: {b_value}
  evidence: {b_evidence}
  reason: {b_reason}

Decide. End your answer with exactly one line: `FINAL: <enum value or unresolved> | <url> | <quote>`"""

RECONCILE_INSTRUCTIONS = f"""This app record was edited field by field by a verification loop, so dependent fields may now
contradict the verified ones. The verified fields (primary_auth, access, api_breadth, mcp) are final:
do not dispute them. Make buildability, blocker, blocker_notes, access_notes and mcp_notes consistent
with them and with the trail's evidence:
- access self_serve_* and nothing material in the way -> buildability ready, blocker none
- access app_review -> ready_with_caveats, blocker app_review (unless outreach is truly required)
- access paid_plan -> ready_with_caveats, blocker paid_plan
- access partner_gated -> needs_outreach, blocker partner_program; contact_sales -> needs_outreach,
  blocker enterprise_sales; no_public_api -> blocked
- a real caveat on a self-serve app (rate limits, enterprise-only scopes) may keep ready_with_caveats
  with blocker "other" and say what it is
- notes must describe the final values (e.g. if mcp is official, mcp_notes names the vendor server;
  if a note says "no official MCP" but mcp=official, rewrite it from the trail's evidence)
Change as little as possible; keep URLs from the record.

{RUBRIC}"""
