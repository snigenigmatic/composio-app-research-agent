primary_auth | agree | - | https://www.twilio.com/docs/iam/oauth-apps/oauth-access-token | "Pass the access_token returned by the Token API as a Bearer token in the Authorization header of your Twilio API requests." | Twilio supports OAuth 2.0 (Authorization Code and Client Credentials) for calling its APIs, which is the preferred multi-tenant auth for delegated access.

access | agree | - | https://www.twilio.com/docs/usage/trials | "You can sign up for a Twilio free trial account without a credit card. Trial accounts expire after 30 days." | Working credentials are self‑serve via a free, time‑limited trial; no partner program or app review is required to obtain keys or register an OAuth app.

api_breadth | agree | - | https://www.twilio.com/docs/ai/mcp | "gives AI coding agents direct, structured access to Twilio's full API surface—over 1,800 endpoints across 30+ products" | The vendor states thousands of endpoints across many products, indicating a broad API surface.

mcp | agree | - | https://www.twilio.com/docs/ai/mcp | "The server is hosted by Twilio at `mcp.twilio.com/docs`" | Confirms an official, vendor‑hosted MCP server (Public Beta).

buildability | agree | - | https://www.twilio.com/docs/usage/trials | "You can send messages and make calls only to verified phone numbers." | It’s buildable now with self‑serve creds and docs, but trial restrictions (verified recipients, 30‑day limit) and the need to upgrade to a paid plan for unrestricted use are material caveats.