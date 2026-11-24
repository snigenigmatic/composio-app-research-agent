- primary_auth | agree | OAuth2 | https://dev.frontapp.com/docs/oauth | "OAuth is required for public integrations available to all Front customers unless you obtain an exception from us." | Public OAuth is supported and required for multi-tenant/public integrations, so OAuth2 is the primary auth a toolkit would use.

- access | agree | self_serve_free | https://dev.frontapp.com/docs/welcome | "You can create a developer account by signing up here. You’ll get access to a free developer environment… Developer accounts are limited to 3 teammates" | Front offers self-serve, free developer accounts that provide a sandbox and the ability to build without contacting support.

- api_breadth | agree | broad | https://dev.frontapp.com/docs/welcome | "Our primary backend API… allows you to read, create, update, and delete a wide range of data across Front’s various entities, from Contacts to Comments." | The Core API exposes many entities with full CRUD, indicating broad coverage.

- mcp | agree | official | https://help.front.com/en/articles/4883136 | "Front’s MCP server allows external AI tools (e.g., Claude, ChatGPT) to connect to Front." | This is an official Front Help article describing Front’s own MCP server.

- buildability | agree | ready_with_caveats | https://dev.frontapp.com/docs/partnering-with-front | "Smaller teams may also be subject to a security or legal review." | Buildable today with self-serve creds and docs, but public distribution/listing involves review; hence caveats.