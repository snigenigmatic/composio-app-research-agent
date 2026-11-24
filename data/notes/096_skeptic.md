primary_auth | agree | Bearer/PAT token | https://docs.devin.ai/es/api-reference/authentication | `-H "Authorization: Bearer $DEVIN_API_KEY"` | Docs show bearer Authorization with cog_ tokens; service-user keys and PATs are the documented credentials a toolkit would use.

access | agree | paid_plan | https://docs.devin.ai/admin/billing/self-serve.md | “Slack, Linear, and MCP integrations” (under Pro includes) | MCP/API use is plan‑gated; Free doesn’t list MCP, while Pro explicitly includes MCP integrations, so working creds require a paid plan.

api_breadth | agree | broad | https://docs.devin.ai/api-reference/overview.md | “For managing resources… — sessions, knowledge, playbooks, secrets, and more… For cross‑organization management — analytics, audit logs, user management, billing, and infrastructure.” | The v3 org and enterprise scopes span many resource families across the product, indicating a broad API.

mcp | agree | official | https://docs.devin.ai/work-with-devin/devin-mcp | “Set up the official Devin MCP server…” | Vendor docs name and document the Devin MCP server with the base URL mcp.devin.ai, confirming it’s official.

buildability | agree | ready_with_caveats | https://docs.devin.ai/admin/billing/self-serve.md | “Slack, Linear, and MCP integrations” (under Pro includes) | Buildable now via documented REST API and MCP server with self‑serve keys, but requires a paid plan for MCP/API access (caveat).