primary_auth | agree | - | https://www.zoho.com/cliq/help/restapi/v2/ | “Request Header: Authorization: Zoho-oauthtoken …” | The REST docs show OAuth 2.0 with the access token sent in the Authorization header using the Zoho-oauthtoken scheme, confirming OAuth2 as the primary auth.

access | agree | - | https://www.zoho.com/cliq/plan-comparison.html?zredirect=f | “API support | Yes | Yes | Yes | Yes” | The plan comparison indicates API support on the Free tier; combined with self‑serve client registration in the Zoho API Console, this fits self_serve_free.

api_breadth | agree | - | https://www.zoho.com/cliq/help/restapi/v3/introduction/ | “v3 introduces CRUD API endpoints for bots, slash commands, message actions, widgets, schedulers, and more” | The v3 docs describe many modules with CRUD coverage across core product areas, supporting a broad API.

mcp | agree | - | https://www.zoho.com/cliq/help/platform/zoho-cliq-mcp.html | “Any AI model or agent can use our official MCP server to access your Cliq data” | This is an official Zoho page explicitly labeling the Cliq MCP server as “official,” so the MCP status is official.

buildability | agree | - | https://www.zoho.com/cliq/help/restapi/v3/registerclient/ | “Upon successful registration… you will receive a Client ID and Client Secret. These credentials are used to obtain an access token” | Creds are self‑serve and the API is fully documented (OAS available), so Composio could ship now without material blockers.