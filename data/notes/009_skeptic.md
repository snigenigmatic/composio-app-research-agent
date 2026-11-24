- primary_auth | agree | - | https://www.developer.copper.com/introduction/authentication.html | "There are two ways to access the Copper Developer API: API keys and OAuth2.0." | Copper documents both API keys and OAuth2 and states OAuth2 is preferred for partner integrations, which is what a multi-tenant agent would use.

- access | disagree | self_serve_trial | https://support.copper.com/en/articles/8823462-api-docs-and-tips | "Available on our trial, professional and business plan" | This shows developers can self‑serve credentials during the free trial (not paid-only). The paid tiers enable ongoing use, but initial access is self‑serve via the trial.

- api_breadth | agree | - | https://www.developer.copper.com/leads/overview.html | "Fetch a Lead by ID • Create a New Lead • Update a Lead • Delete a Lead" | The docs expose full CRUD on core objects and many areas (Leads, People, Companies, Opportunities, Projects, Tasks, Activities, Custom Fields, Files, Webhooks), indicating a broad API surface.

- mcp | agree | - | https://www.copper.com/mcp | "Yes. Copper is launching an official MCP server, built and hosted by Copper. The beta launches in November 2026." | Vendor confirms an official, first‑party MCP server.

- buildability | agree | - | https://www.developer.copper.com/introduction/oauth/index.html | "To register your application, contact us (partners@copper.com)." | Buildable now, but caveats include manual OAuth app registration (not self‑serve) and plan gating for production use, so “ready_with_caveats” fits.