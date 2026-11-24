# Hand check: how to label

1. Open `human_sample.csv` (20 apps x 5 fields, stratified 2 per category, seed 154).
2. For each row, read the vendor's own docs (start from `hint`) and write the correct value in `truth`,
   using exactly one of `allowed_values`. If two values are both defensible, write both separated by `|`
   (e.g. `self_serve_free|app_review`) and say why in `note`.
3. Put the page you relied on in `source_url`.
4. **Do not open data/pass1, data/final, the notes or the page before you finish.** Blind labels are the
   point: they're the yardstick that pass 1 and the verified output are both scored against.
5. Save as `human_labels.csv`, then run `python -m agent.pipeline score`.

## Definitions (same rubric the agents use)

```
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
```

## Who labelled

The labels in `human_labels.csv` were produced blind by Claude Sonnet (an independent model family from the gpt-5 research pipeline) at the user request, not by a human, on 2026-11-24. They come from vendor docs on the web, without reading the pipeline outputs.
