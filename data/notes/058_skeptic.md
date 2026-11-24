- primary_auth | agree | None (local/open) | https://github.com/sherlock-project/sherlockproject.xyz/blob/master/installation.mdx | "That's it! You can now run sherlock from anywhere." | Official docs show a purely local CLI install/run with no keys, tokens, or OAuth.

- access | agree | no_public_api | https://github.com/sherlock-project/api | "python3 manage.py runserver 0.0.0.0:8000 … Start you browser and type 127.0.0.1:8000" | The only “API” provided is a self-hosted DRF app you run locally; there’s no hosted, sign‑up API.

- api_breadth | agree | none | https://github.com/sherlock-project/api | "Start you browser and type 127.0.0.1:8000" | Since the project only documents a local DIY server and no public endpoints, there is effectively no public API surface to rate for breadth.

- mcp | agree | none | https://github.com/sherlock-project | "Showing 5 of 5 repositories" (lists sherlock, sherlockproject.xyz, .github, build, api) | The official org lists no MCP server; any “Sherlock MCP” wrappers found are third‑party and not vendor‑maintained.

- buildability | agree | blocked | https://github.com/sherlock-project/sherlock | "To search for only one user: sherlock user123" | Sherlock is a local CLI tool with no hosted API/auth flow; for a multi‑tenant agent connector this is blocked (blocker: local_tool_only).