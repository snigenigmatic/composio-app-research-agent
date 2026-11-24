"""Independent, non-LLM oracles used to cross-check the agent.

1. Composio toolkit catalog (via the Composio SDK): if Composio already ships a toolkit for the app,
   its declared auth_schemes are a second opinion on auth, and its existence proves buildability.
2. Official MCP Registry (registry.modelcontextprotocol.io): server names are reverse-DNS namespaces
   that the registry verifies against domain ownership, so `com.stripe/...` means Stripe published it.
   That makes "is there an official MCP?" checkable without trusting the model.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

# Composio auth scheme -> our AuthMethod enum
SCHEME_MAP = {
    "OAUTH2": "OAuth2",
    "OAUTH1": "OAuth2",  # closest bucket; noted separately
    "API_KEY": "API key",
    "BEARER_TOKEN": "Bearer/PAT token",
    "BASIC": "Basic",
    "BASIC_WITH_JWT": "JWT/service account",
    "GOOGLE_SERVICE_ACCOUNT": "JWT/service account",
    "SERVICE_ACCOUNT": "JWT/service account",
    "NO_AUTH": "None (local/open)",
}

# Display name -> extra candidate slugs/tokens for matching against the catalog and registry.
ALIASES = {
    "Zoho CRM": ["zoho", "zohocrm"],
    "Zoho Cliq": ["zohocliq", "cliq"],
    "Lark (Larksuite)": ["lark", "larksuite"],
    "WhatsApp Business": ["whatsapp"],
    "Meta Ads": ["metaads", "facebookads", "facebook"],
    "LinkedIn Ads": ["linkedinads", "linkedin"],
    "GoHighLevel": ["gohighlevel", "highlevel", "highlevellocation"],
    "Threads (Meta)": ["threads"],
    "Salesforce Commerce Cloud": ["salesforcecommercecloud", "commercecloud"],
    "Magento (Adobe Commerce)": ["magento", "adobecommerce"],
    "Amazon Selling Partner": ["amazonsellingpartner", "amazonsp", "spapi", "sellingpartner"],
    "MongoDB Atlas": ["mongodbatlas", "mongodb"],
    "Monday.com": ["monday", "mondaycom"],
    "Help Scout": ["helpscout"],
    "Paygent Connect": ["paygent", "paygentconnect"],
    "Otter AI": ["otter", "otterai"],
    "Mermaid CLI": ["mermaid", "mermaidcli"],
    "YouTube Transcript": ["youtubetranscript", "transcriptapi"],
    "Waterfall.io": ["waterfall", "waterfallio"],
    "systeme.io": ["systeme", "systemeio"],
    "Bright Data": ["brightdata"],
    "SE Ranking": ["seranking"],
    "Google Ads": ["googleads"],
    "QuickBooks": ["quickbooks", "intuit"],
}

# Vendor domains for official-MCP detection (reverse-DNS namespaces in the registry).
VENDOR_DOMAINS = {
    "GitHub": ["github.com", "io.github.github"],
    "Mermaid CLI": ["mermaid-js", "mermaidchart"],
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def candidates(app: str) -> list[str]:
    base = norm(re.sub(r"\(.*?\)", "", app))
    return list(dict.fromkeys([base, norm(app), *ALIASES.get(app, [])]))


# ---------------------------------------------------------------- Composio catalog

def composio_catalog(refresh: bool = False) -> list[dict]:
    """All toolkits in the Composio catalog, cached to data/cache/composio_toolkits.json."""
    path = CACHE / "composio_toolkits.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    from composio import Composio

    c = Composio(api_key=os.environ["COMPOSIO_API_KEY"])
    items, cursor = [], None
    while True:
        page = c.toolkits.list(limit=1000, cursor=cursor, managed_by="all")
        for it in page.items:
            items.append({
                "slug": it.slug,
                "name": it.name,
                "auth_schemes": it.auth_schemes or [],
                "managed_auth": it.composio_managed_auth_schemes or [],
                "no_auth": bool(it.no_auth),
                "tools_count": int(it.meta.tools_count or 0),
                "app_url": it.meta.app_url,
            })
        cursor = getattr(page, "next_cursor", None)
        if not cursor or not page.items:
            break
    path.write_text(json.dumps(items, indent=1), encoding="utf-8")
    return items


def composio_match(app: str, catalog: list[dict]) -> dict | None:
    cands = candidates(app)
    by_slug = {norm(t["slug"]): t for t in catalog}
    by_name = {norm(t["name"]): t for t in catalog}
    for c in cands:
        if c in by_slug:
            return by_slug[c]
        if c in by_name:
            return by_name[c]
    for c in cands:  # Composio also wraps vendor MCP servers as "<slug>_mcp" toolkits
        if c + "mcp" in by_slug:
            return by_slug[c + "mcp"]
    return None


def composio_auth(match: dict | None) -> list[str]:
    if not match:
        return []
    schemes = list(match["auth_schemes"])
    if match["no_auth"] and not schemes:
        schemes = ["NO_AUTH"]
    return sorted({SCHEME_MAP.get(s, "Other") for s in schemes})


# ---------------------------------------------------------------- MCP registry

def _registry_search(term: str) -> list[dict]:
    path = CACHE / f"mcpreg_{norm(term)}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    out, cursor = [], None
    for _ in range(4):  # up to 400 results per term
        url = f"https://registry.modelcontextprotocol.io/v0/servers?search={quote(term)}&limit=100"
        if cursor:
            url += f"&cursor={quote(cursor)}"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        d = r.json()
        for s in d.get("servers", []):
            srv = s.get("server", {})
            out.append({
                "name": srv.get("name", ""),
                "description": (srv.get("description") or "")[:200],
                "repo": (srv.get("repository") or {}).get("url", ""),
                "website": srv.get("websiteUrl", ""),
            })
        cursor = (d.get("metadata") or {}).get("nextCursor")
        if not cursor:
            break
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def vendor_tokens(app: str, hint: str) -> list[str]:
    """Tokens that identify the vendor in a reverse-DNS namespace or a GitHub org."""
    toks = set(candidates(app))
    m = re.match(r"(?:https?://)?(?:www\.|developers?\.|docs\.|api\.|developer-docs\.|help\.|core\.|open\.|api-docs\.|learn\.)?([a-z0-9-]+)\.", hint.lower())
    if m:
        toks.add(norm(m.group(1)))
    toks.update(norm(x) for x in VENDOR_DOMAINS.get(app, []))
    return [t for t in toks if len(t) >= 3]


def mcp_registry(app: str, hint: str) -> dict:
    """Return {'status': official|community|none, 'official': [...], 'community_count': n}."""
    term = re.sub(r"\(.*?\)", "", app).strip()
    servers = _registry_search(term)
    toks = vendor_tokens(app, hint)
    official, community = [], []
    app_toks = candidates(app)
    for s in servers:
        name = s["name"]
        ns = name.split("/")[0]                 # e.g. com.stripe or io.github.stripe
        ns_parts = [norm(p) for p in ns.split(".")]
        repo_org = ""
        m = re.match(r"https?://github\.com/([^/]+)/", s["repo"] or "")
        if m:
            repo_org = norm(m.group(1))
        text = norm(name + " " + s["description"])
        if not any(t in text for t in app_toks):
            continue  # search hit unrelated to this app
        # official if the domain-verified namespace or the GitHub org is the vendor's
        # owner of a reverse-DNS namespace: com.stripe -> stripe; io.github.stripe -> stripe;
        # app.vercel.foo / dev.workers.foo (sub-domains of hosting platforms) -> foo
        hosting = {"vercel", "netlify", "github", "pages", "herokuapp", "workers", "fly", "onrender",
                   "render", "smithery", "railway", "replit", "glama", "pipedream", "zapier", "composio"}
        vendor_ns = ""
        if len(ns_parts) >= 3 and ns_parts[1] in hosting:
            vendor_ns = ns_parts[2]
        elif len(ns_parts) >= 2:
            vendor_ns = ns_parts[1]
        if vendor_ns in toks or repo_org in toks:
            official.append(name)
        else:
            community.append(name)
    official = list(dict.fromkeys(official))
    community = list(dict.fromkeys(community))
    status = "official" if official else ("community" if community else "none")
    return {"status": status, "official": official[:5], "community_count": len(community),
            "community_examples": community[:3]}
