"""Thin LLM wrappers used by every pass. Two interchangeable backends:
OpenAI (Responses API + hosted web_search) and Anthropic (Messages API + web_search/web_fetch).
Pick with LLM_PROVIDER=openai|anthropic; RESEARCH_MODEL overrides the model.

- web_research(): one agentic turn with Anthropic-hosted web_search + web_fetch,
  resuming pause_turn, returning the final notes plus every URL the model touched.
- extract(): turn free-text notes into a validated pydantic record (structured outputs).
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Type, TypeVar

import anthropic
from pydantic import BaseModel

from . import env  # noqa: F401  (loads .env before the provider is chosen)

PROVIDER = os.environ.get("LLM_PROVIDER") or ("anthropic" if os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY") else "openai")
MODEL = os.environ.get("RESEARCH_MODEL") or ("claude-opus-5-5" if PROVIDER == "anthropic" else "gpt-5")
EFFORT = os.environ.get("RESEARCH_EFFORT", "medium")
MAX_SEARCHES = int(os.environ.get("RESEARCH_MAX_SEARCHES", "5"))
MAX_FETCHES = int(os.environ.get("RESEARCH_MAX_FETCHES", "6"))

T = TypeVar("T", bound=BaseModel)

_client: anthropic.AsyncAnthropic | None = None


def client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(max_retries=4, timeout=600.0)
    return _client


def web_tools(allowed_domains: list[str] | None = None) -> list[dict]:
    search = {"type": "web_search_20260209", "name": "web_search", "max_uses": MAX_SEARCHES}
    fetch = {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": MAX_FETCHES}
    if allowed_domains:
        search["allowed_domains"] = allowed_domains
    return [search, fetch]


@dataclass
class ResearchResult:
    text: str
    urls: list[str] = field(default_factory=list)
    searches: int = 0
    fetches: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = ""


def _collect(resp, out: ResearchResult) -> None:
    for block in resp.content:
        t = getattr(block, "type", "")
        if t == "server_tool_use":
            if block.name == "web_search":
                out.searches += 1
            elif block.name == "web_fetch":
                out.fetches += 1
                url = (block.input or {}).get("url")
                if url:
                    out.urls.append(url)
        elif t == "web_search_tool_result" and isinstance(block.content, list):
            for r in block.content:
                url = getattr(r, "url", None)
                if url:
                    out.urls.append(url)
    u = resp.usage
    out.input_tokens += (u.input_tokens or 0) + (getattr(u, "cache_read_input_tokens", 0) or 0)
    out.output_tokens += u.output_tokens or 0


async def _anthropic_web_research(system: str, prompt: str, *, max_continuations: int = 5) -> ResearchResult:
    """One research turn. The model searches/fetches on Anthropic's side; we only resume pauses."""
    out = ResearchResult(text="")
    messages: list[dict] = [{"role": "user", "content": prompt}]
    for _ in range(max_continuations + 1):
        async with client().beta.messages.stream(
            model=MODEL,
            max_tokens=32000,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": EFFORT},
            tools=web_tools(),
            messages=messages,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            resp = await stream.get_final_message()
        _collect(resp, out)
        out.stop_reason = resp.stop_reason or ""
        if resp.stop_reason == "pause_turn":
            messages = [messages[0], {"role": "assistant", "content": resp.content}]
            continue
        if resp.stop_reason == "refusal":
            out.text = "REFUSED"
            return out
        out.text = "\n".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return out
    out.text = "\n".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return out


async def _anthropic_extract(model_cls: Type[T], instructions: str, notes: str) -> T:
    """Structured-output extraction: notes -> validated pydantic model."""
    resp = await client().messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": f"{instructions}\n\n<notes>\n{notes}\n</notes>"}],
        output_format=model_cls,
    )
    if resp.parsed_output is None:
        raise ValueError(f"extraction failed: stop_reason={resp.stop_reason}")
    return resp.parsed_output


async def gather_limited(coros, limit: int):
    sem = asyncio.Semaphore(limit)

    async def run(c):
        async with sem:
            return await c

    return await asyncio.gather(*(run(c) for c in coros), return_exceptions=True)


# ---------------------------------------------------------------- OpenAI backend

_oai = None


def oai():
    global _oai
    if _oai is None:
        from openai import AsyncOpenAI
        _oai = AsyncOpenAI(max_retries=4, timeout=900.0)
    return _oai


def reset_clients() -> None:
    global _client, _oai
    _client = None
    _oai = None


async def _openai_web_research(system: str, prompt: str) -> ResearchResult:
    out = ResearchResult(text="")
    kw = {}
    if EFFORT:
        kw["reasoning"] = {"effort": EFFORT}
    resp = await oai().responses.create(
        model=MODEL,
        instructions=system,
        input=prompt,
        tools=[{"type": os.environ.get("OPENAI_SEARCH_TOOL", "web_search")}],
        max_output_tokens=32000,
        **kw,
    )
    for item in resp.output:
        if item.type == "web_search_call":
            action = getattr(item, "action", None)
            atype = getattr(action, "type", "search") if action is not None else "search"
            if atype == "search":
                out.searches += 1
            else:
                out.fetches += 1
                url = getattr(action, "url", None)
                if url:
                    out.urls.append(url)
        elif item.type == "message":
            for c in item.content:
                for ann in getattr(c, "annotations", None) or []:
                    url = getattr(ann, "url", None)
                    if url:
                        out.urls.append(url)
    out.text = resp.output_text or ""
    u = resp.usage
    if u:
        out.input_tokens = u.input_tokens or 0
        out.output_tokens = u.output_tokens or 0
    out.stop_reason = resp.status or ""
    return out


async def _openai_extract(model_cls: Type[T], instructions: str, notes: str) -> T:
    resp = await oai().responses.parse(
        model=MODEL,
        input=f"{instructions}\n\n<notes>\n{notes}\n</notes>",
        text_format=model_cls,
        reasoning={"effort": "low"},
    )
    if resp.output_parsed is None:
        raise ValueError(f"extraction failed: status={resp.status}")
    return resp.output_parsed


async def web_research(system: str, prompt: str) -> ResearchResult:
    if PROVIDER == "anthropic":
        return await _anthropic_web_research(system, prompt)
    return await _openai_web_research(system, prompt)


async def extract(model_cls: Type[T], instructions: str, notes: str) -> T:
    if PROVIDER == "anthropic":
        return await _anthropic_extract(model_cls, instructions, notes)
    return await _openai_extract(model_cls, instructions, notes)
