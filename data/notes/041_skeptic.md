primary_auth | agree | - | https://shopify.dev/docs/api/usage/authentication | "GraphQL Admin API | Your app, on behalf of a merchant | OAuth, usually token exchange | `X‑Shopify‑Access‑Token`." | Admin API calls for multi‑tenant apps use OAuth2 to obtain the access token sent in X‑Shopify‑Access‑Token.

access | agree | - | https://shopify.dev/docs/apps/launch/distribution | "Public distribution … Approval required — Yes." | Public apps that install on multiple merchants require Shopify’s App Store review; this gates production distribution across stores.

api_breadth | agree | - | https://shopify.dev/docs/api | "GraphQL Admin API reads and writes products, customers, orders, inventory, and the rest of the data behind the Shopify admin." | Docs describe full read/write coverage of the core and extended Admin data model, supporting a “broad” classification.

mcp | agree | - | https://shopify.dev/docs/agents/shop-mcp | "Shop MCP is a hosted Model Context Protocol (MCP) server from Shopify, accessed at `https://mcp.shop.com/`." | An official, vendor‑hosted MCP exists (buyer‑side). Separately, the merchant‑side “Shopify MCP” page states “Coming soon … isn’t publicly available yet,” confirming it’s official but not yet live.

buildability | agree | - | https://shopify.dev/docs/apps/launch/distribution | "Public distribution … Approval required — Yes." | Build is feasible now (dev stores and custom distribution are available), but shipping a multi‑merchant public app requires passing Shopify’s app review, so “ready_with_caveats” fits.