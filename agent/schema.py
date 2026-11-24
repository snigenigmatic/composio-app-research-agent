"""Record schema shared by the researcher, the verifiers and the site builder.

Every field the page shows comes from one of these models, so an agent
consuming data/results.json can rely on the enums below.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

AuthMethod = Literal[
    "OAuth2",
    "API key",
    "Bearer/PAT token",
    "Basic",
    "JWT/service account",
    "HMAC/signature",
    "Bot token",
    "None (local/open)",
    "Other",
]

Access = Literal[
    "self_serve_free",      # sign up and get credentials yourself, free tier/forever-free
    "self_serve_trial",     # self-serve, but only on a time-limited trial
    "paid_plan",            # API exists but only on a paid plan/tier
    "app_review",           # self-serve dev creds, but production scopes need platform review/approval
    "partner_gated",        # partner program / application required before any credentials
    "contact_sales",        # enterprise / talk-to-sales before you get API access
    "no_public_api",        # no documented public API
]

Buildability = Literal[
    "ready",                # could ship an agent toolkit today with self-serve creds
    "ready_with_caveats",   # buildable, but review/paid tier/limits constrain it
    "needs_outreach",       # need a partnership/sales conversation first
    "blocked",              # no viable API (or ToS forbids)
]

Blocker = Literal[
    "none",
    "app_review",
    "paid_plan",
    "partner_program",
    "enterprise_sales",
    "no_public_api",
    "local_tool_only",      # a CLI/library, not a hosted API: needs a sandbox, not auth
    "tos_or_risk",          # trading/financial/ToS restrictions
    "other",
]

Tri = Literal["yes", "no", "unknown"]


class Evidence(BaseModel):
    field: str = Field(description="Which field this supports, e.g. auth_methods, access, api_surface, mcp")
    url: str
    quote: str = Field(description="Short verbatim snippet (<= 25 words) from the page that supports the claim")


class AppRecord(BaseModel):
    app: str
    category: str
    one_liner: str = Field(description="What the product does, <= 15 words")
    auth_methods: List[AuthMethod]
    primary_auth: AuthMethod = Field(description="The auth an agent toolkit would most likely use")
    access: Access
    access_notes: str = Field(description="One sentence: how a developer actually gets credentials")
    api_styles: List[Literal["REST", "GraphQL", "SOAP", "gRPC", "WebSocket", "SDK/CLI only", "None"]]
    api_breadth: Literal["broad", "moderate", "narrow", "none"]
    openapi_spec: Tri
    webhooks: Tri
    sandbox: Tri = Field(description="Is there a free sandbox / test mode / dev account?")
    mcp: Literal["official", "community", "none"]
    mcp_notes: str = Field(description="Name/URL of the MCP server if any, else empty")
    buildability: Buildability
    blocker: Blocker
    blocker_notes: str = Field(description="One sentence on the main blocker, or empty when none")
    docs_url: str
    evidence: List[Evidence]
    confidence: Literal["high", "medium", "low"]


# Fields that verification scores. Kept small and categorical on purpose:
# these are the answers a toolkit PM acts on.
SCORED_FIELDS = ["primary_auth", "access", "api_breadth", "mcp", "buildability"]


class FieldVerdict(BaseModel):
    field: str
    verdict: Literal["agree", "disagree", "unsure"]
    corrected_value: Optional[str] = Field(default=None, description="Only when verdict is disagree: the value you believe is right, using the same enum")
    url: Optional[str] = None
    quote: Optional[str] = None
    reason: str


class SkepticReport(BaseModel):
    app: str
    verdicts: List[FieldVerdict]


class Reconciled(BaseModel):
    buildability: Buildability
    blocker: Blocker
    blocker_notes: str
    access_notes: str
    mcp_notes: str
    reason: str = Field(description="One sentence: what was inconsistent and what you changed")
