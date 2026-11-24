primary_auth | agree | Bearer/PAT token | https://coda.io/developers/apis/v1 | "headers = {'Authorization': 'Bearer <your API token>'}" | The official API reference shows Bearer authentication using a user-generated API token.

access | agree | self_serve_free | https://help.coda.io/hc/en-us/articles/39555941038349-Does-Coda-have-an-API | "Coda has a public API available to all users." | This indicates self-serve access for all users (free and paid) without partner gating or sales.

api_breadth | agree | broad | https://help.coda.io/hc/en-us/articles/39555941038349-Does-Coda-have-an-API | "The Coda REST API allows users to programmatically interact with Coda docs in a number of ways, including:" … "Inserting and updating rows" … "Publishing a doc." | The help article enumerates many capabilities across docs, tables/rows, pages, and publishing—consistent with a broad API.

mcp | agree | official | https://help.coda.io/hc/en-us/articles/44722661982989-Connect-to-the-Coda-MCP | "Server URL: https://coda.io/apis/mcp" | Coda documents and hosts its own MCP server, confirming an official MCP.

buildability | agree | ready_with_caveats | https://help.coda.io/hc/en-us/articles/39555760015757-Overview-Doc-limits | "On all plan types, docs larger than 125 MB* may not be able to access the Coda API." | The API is buildable with self-serve tokens and docs, but caveats include doc-size API lockouts, rate limits, and some write actions requiring Doc Maker role. ([help.coda.io](https://help.coda.io/hc/en-us/articles/39555760015757-Overview-Doc-limits?utm_source=openai))