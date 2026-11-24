primary_auth | agree |  | https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/ | "Netlify uses OAuth2 for authentication." | Vendor docs explicitly state OAuth2; PATs are also supported but OAuth2 is the recommended flow for public integrations.

access | agree |  | https://docs.netlify.com/manage/accounts-and-billing/user-settings/ | "When you register an application, Netlify will provide a client ID and secret you can use in your application settings." | Indicates self-serve registration for OAuth apps; no app review is mentioned and free accounts can also generate PATs.

api_breadth | agree |  | https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/ | "manage atomic deploys of your sites and apps, manage form submissions, inject JavaScript snippets, manage DNS" | Docs (plus linked OpenAPI) cover many resource families (sites, deploys, DNS, forms, snippets, env vars), consistent with a broad API.

mcp | agree |  | https://www.netlify.com/press/netlify-launches-official-mcp-server-setting-the-standard-for-agent-native-development/ | "today launched its official Netlify Model Context Protocol (MCP) Server" | Confirms an official vendor-maintained MCP server.

buildability | agree |  | https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/ | "You can register a new application in your Netlify user settings for OAuth applications." | Self-serve creds + documented REST API; no partner/app review gating noted; standard rate limits are published.