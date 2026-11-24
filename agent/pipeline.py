"""Research pipeline: python -m agent.pipeline <stage> [--only 1,2,3] [--concurrency N]

Stages (run in order; each is resumable and writes JSON per app):
  research    pass 1  - researcher agent (Claude + web_search/web_fetch) -> data/pass1/<id>.json
  oracles     check   - Composio toolkit catalog + MCP registry + evidence-URL fetch -> data/oracles/<id>.json
  skeptic     pass 2  - independent skeptic agent tries to falsify each scored field -> data/skeptic/<id>.json
  adjudicate  pass 3  - adjudicator agent settles every disputed field -> data/final/<id>.json
  reconcile   pass 4  - consistency loop: rule checks + re-align dependent fields with verified ones
  sample      human   - writes verification/human_sample.csv (stratified 2 per category) for hand checking
  score       report  - scores pass1 vs final against verification/human_labels.csv
  all         research, oracles, skeptic, adjudicate
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import random
import re
import sys
import time
from pathlib import Path

from . import llm, prompts
from .schema import SCORED_FIELDS, AppRecord, Reconciled, SkepticReport

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VER = ROOT / "verification"
for d in ["pass1", "oracles", "skeptic", "final", "notes", "logs"]:
    (DATA / d).mkdir(parents=True, exist_ok=True)


from .env import load_env  # noqa: E402


def apps(only: set[int] | None = None) -> list[dict]:
    rows = list(csv.DictReader(open(DATA / "apps.csv", encoding="utf-8")))
    for r in rows:
        r["id"] = int(r["id"])
    return [r for r in rows if not only or r["id"] in only]


def rpath(stage: str, app_id: int) -> Path:
    return DATA / stage / f"{app_id:03d}.json"


def read(stage: str, app_id: int) -> dict | None:
    p = rpath(stage, app_id)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def write(stage: str, app_id: int, obj: dict) -> None:
    rpath(stage, app_id).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(DATA / "logs" / "run.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ------------------------------------------------------------------ pass 1: research

async def research_one(a: dict) -> None:
    if read("pass1", a["id"]):
        return
    t0 = time.time()
    res = await llm.web_research(prompts.RESEARCHER_SYSTEM, prompts.RESEARCH_TASK.format(**a))
    (DATA / "notes" / f"{a['id']:03d}_pass1.md").write_text(res.text, encoding="utf-8")
    rec = await llm.extract(AppRecord, prompts.EXTRACT_INSTRUCTIONS
                            + f"\nApp: {a['app']}. Category: {a['category']}.", res.text)
    out = rec.model_dump()
    out["category"] = a["category"]  # keep the given taxonomy
    out["_meta"] = {"id": a["id"], "hint": a["hint"], "searches": res.searches, "fetches": res.fetches,
                    "urls_seen": list(dict.fromkeys(res.urls))[:40], "in_tok": res.input_tokens,
                    "out_tok": res.output_tokens, "secs": round(time.time() - t0, 1), "model": llm.MODEL}
    write("pass1", a["id"], out)
    log(f"pass1 {a['id']:3d} {a['app']:<28} auth={rec.primary_auth:<16} access={rec.access:<16} "
        f"build={rec.buildability} ({res.searches}s/{res.fetches}f, {out['_meta']['secs']}s)")


# ------------------------------------------------------------------ oracles (no LLM)

def check_url(url: str, quote: str) -> dict:
    import requests
    from bs4 import BeautifulSoup
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (research-verifier)"},
                         allow_redirects=True)
        status = r.status_code
        found = None
        if status == 200 and ("html" in r.headers.get("content-type", "") or "text" in r.headers.get("content-type", "")):
            text = BeautifulSoup(r.text, "html.parser").get_text(" ")
            t = re.sub(r"\W+", " ", text).lower()
            q = re.sub(r"\W+", " ", quote).lower().strip()
            words = q.split()
            if len(words) >= 3:
                # grounded if any 5-word window of the quote appears on the page
                n = min(5, len(words))
                found = any(" ".join(words[i:i + n]) in t for i in range(len(words) - n + 1))
            if len(t) < 1500:  # JS-rendered shell: cannot judge
                found = None
        return {"url": url, "status": status, "quote_found": found}
    except Exception as e:  # noqa: BLE001
        return {"url": url, "status": 0, "quote_found": None, "error": type(e).__name__}


def oracles_one(a: dict, catalog: list[dict] | None) -> None:
    from . import oracles as orc
    p1 = read("pass1", a["id"])
    if not p1:
        return
    out: dict = {"id": a["id"], "app": a["app"]}
    m = orc.composio_match(a["app"], catalog) if catalog is not None else None
    out["composio"] = ({"slug": m["slug"], "auth": orc.composio_auth(m), "tools": m["tools_count"]}
                       if m else None)
    try:
        out["mcp_registry"] = orc.mcp_registry(a["app"], a["hint"])
    except Exception as e:  # noqa: BLE001
        out["mcp_registry"] = {"status": "error", "error": str(e)}
    out["evidence"] = [check_url(e["url"], e["quote"]) | {"field": e["field"]} for e in p1["evidence"]]

    flags = []
    comp = out["composio"]
    if comp and comp["auth"] and p1["primary_auth"] not in comp["auth"]:
        flags.append({"field": "primary_auth", "why": f"Composio toolkit '{comp['slug']}' uses {comp['auth']}"})
    if comp and comp["tools"] > 0 and p1["buildability"] == "blocked":
        flags.append({"field": "buildability", "why": f"Composio already ships '{comp['slug']}' ({comp['tools']} tools)"})
    reg = out["mcp_registry"]
    if reg.get("status") == "official" and p1["mcp"] != "official":
        flags.append({"field": "mcp", "why": f"MCP registry lists vendor-namespaced server(s) {reg['official'][:2]}"})
    elif reg.get("status") in ("community", "none") and p1["mcp"] == "official":
        flags.append({"field": "mcp", "why": "official MCP claimed, but no vendor-namespaced server in the MCP Registry "
                                             f"({reg.get('community_count', 0)} third-party entries); needs confirmation from a vendor page"})
    for ev in out["evidence"]:
        if ev["status"] in (404, 410) or ev.get("error") == "ConnectionError":
            flags.append({"field": ev["field"], "why": f"cited URL dead ({ev['status'] or ev.get('error')}): {ev['url']}"})
        elif ev["quote_found"] is False:
            flags.append({"field": ev["field"], "why": f"quote not found on cited page: {ev['url']}"})
    out["flags"] = flags
    write("oracles", a["id"], out)
    log(f"oracle {a['id']:3d} {a['app']:<28} composio={comp['slug'] if comp else '-':<18} "
        f"mcp_reg={reg.get('status')} flags={len(flags)}")


# ------------------------------------------------------------------ pass 2: skeptic

async def skeptic_one(a: dict) -> None:
    if read("skeptic", a["id"]):
        return
    p1 = read("pass1", a["id"])
    if not p1:
        return
    claims = "\n".join(f"- {f}: {p1[f]}" for f in SCORED_FIELDS)
    claims += f"\n(context: access_notes={p1['access_notes']!r}; blocker={p1['blocker']}; mcp_notes={p1['mcp_notes']!r})"
    ev = "\n".join(f"- {e['field']} | {e['url']} | {e['quote']}" for e in p1["evidence"]) or "(none)"
    res = await llm.web_research(prompts.SKEPTIC_SYSTEM,
                                 prompts.SKEPTIC_TASK.format(claims=claims, evidence=ev, **a))
    (DATA / "notes" / f"{a['id']:03d}_skeptic.md").write_text(res.text, encoding="utf-8")
    rep = await llm.extract(SkepticReport, prompts.SKEPTIC_EXTRACT, res.text)
    out = rep.model_dump()
    out["_meta"] = {"searches": res.searches, "fetches": res.fetches, "in_tok": res.input_tokens,
                    "out_tok": res.output_tokens}
    write("skeptic", a["id"], out)
    dis = [v["field"] for v in out["verdicts"] if v["verdict"] == "disagree"]
    log(f"skeptic {a['id']:3d} {a['app']:<28} disagree={dis}")


# ------------------------------------------------------------------ pass 3: adjudicate

ENUMS = {f: set(AppRecord.model_fields[f].annotation.__args__) for f in SCORED_FIELDS}  # type: ignore[union-attr]


async def adjudicate_one(a: dict) -> None:
    if read("final", a["id"]):
        return
    p1, sk, orc = read("pass1", a["id"]), read("skeptic", a["id"]), read("oracles", a["id"])
    if not (p1 and sk):
        return
    final = {k: v for k, v in p1.items() if k != "_meta"}
    trail = []
    disputes: dict[str, dict] = {}
    for v in sk["verdicts"]:
        if v["field"] in SCORED_FIELDS and v["verdict"] == "disagree" and v.get("corrected_value") != p1[v["field"]]:
            disputes[v["field"]] = {"b_value": v.get("corrected_value") or "?", "b_evidence": f"{v.get('url')} | {v.get('quote')}",
                                    "b_reason": v["reason"], "source": "skeptic"}
    for fl in (orc or {}).get("flags", []):
        f = fl["field"]
        if f in SCORED_FIELDS and f not in disputes:
            disputes[f] = {"b_value": "(see oracle)", "b_evidence": fl["why"], "b_reason": "independent oracle conflict",
                           "source": "oracle"}
    needs_human = []
    for f, d in disputes.items():
        a_ev = "; ".join(f"{e['url']} | {e['quote']}" for e in p1["evidence"] if e["field"] == f) or "(none cited)"
        res = await llm.web_research(prompts.ADJUDICATOR_SYSTEM, prompts.ADJUDICATOR_TASK.format(
            field=f, a_value=p1[f], a_evidence=a_ev, **d, **a))
        m = re.search(r"FINAL:\s*([^|\n]+)\|?\s*([^|\n]*)\|?\s*(.*)", res.text)
        decision = m.group(1).strip().strip("`*") if m else "unresolved"
        entry = {"field": f, "pass1": p1[f], "challenger": d["b_value"], "source": d["source"],
                 "decision": decision, "url": (m.group(2).strip() if m else ""), "quote": (m.group(3).strip() if m else "")}
        if decision in ENUMS[f]:
            final[f] = decision
        else:
            needs_human.append(f)
            entry["decision"] = "unresolved"
        trail.append(entry)
    final["_trail"] = trail
    final["_needs_human"] = needs_human
    final["_meta"] = p1["_meta"]
    write("final", a["id"], final)
    changed = [t["field"] for t in trail if t["decision"] not in ("unresolved", t["pass1"])]
    log(f"adjud  {a['id']:3d} {a['app']:<28} disputes={list(disputes)} changed={changed} human={needs_human}")


# ------------------------------------------------------------------ pass 4: reconcile (consistency loop)

EXPECT = {"self_serve_free": "ready", "self_serve_trial": "ready", "app_review": "ready_with_caveats",
          "paid_plan": "ready_with_caveats", "partner_gated": "needs_outreach", "contact_sales": "needs_outreach",
          "no_public_api": "blocked"}


def inconsistencies(r: dict) -> list[str]:
    out = []
    if r["buildability"] == "ready" and r["blocker"] != "none":
        out.append("ready but has a blocker")
    if r["buildability"] != "ready" and r["blocker"] == "none":
        out.append("not ready but no blocker")
    if r["access"] in ("partner_gated", "contact_sales", "no_public_api") and r["buildability"] in ("ready", "ready_with_caveats"):
        out.append(f"access {r['access']} but buildability {r['buildability']}")
    if r["access"] in ("app_review", "paid_plan") and r["buildability"] == "ready":
        out.append(f"access {r['access']} but buildability ready")
    notes = r["mcp_notes"].lower()
    if r["mcp"] == "official" and (not notes or any(w in notes for w in ("no official", "third-party", "third‑party", "community", "cdata"))):
        out.append("mcp_notes do not support mcp=official")
    if r["mcp"] != "official" and "official" in notes and "no official" not in notes:
        out.append("mcp_notes claim official but mcp is not")
    return out


async def reconcile_one(a: dict) -> None:
    r = read("final", a["id"])
    if not r or r.get("_reconciled") is not None:
        return
    issues = inconsistencies(r)
    changed = [t for t in r["_trail"] if t["decision"] not in ("unresolved", t["pass1"])]
    if not issues and not changed:
        r["_reconciled"] = {}
        write("final", a["id"], r)
        return
    view = {k: v for k, v in r.items() if k not in ("_meta", "_reconciled")}
    rec = await llm.extract(Reconciled, prompts.RECONCILE_INSTRUCTIONS + f"\nDetected issues: {issues or 'none'}",
                            json.dumps(view, ensure_ascii=False, indent=1))
    before = {k: r[k] for k in ("buildability", "blocker")}
    for k in ("buildability", "blocker", "blocker_notes", "access_notes", "mcp_notes"):
        r[k] = getattr(rec, k)
    if rec.buildability != before["buildability"]:
        r["_trail"].append({"field": "buildability", "pass1": before["buildability"], "challenger": rec.buildability,
                            "source": "consistency", "decision": rec.buildability, "url": "", "quote": rec.reason})
    r["_reconciled"] = {"issues": issues, "reason": rec.reason, "before": before}
    write("final", a["id"], r)
    log(f"recon  {a['id']:3d} {a['app']:<28} issues={issues} build {before['buildability']}->{rec.buildability} "
        f"blocker {before['blocker']}->{rec.blocker}")


# ------------------------------------------------------------------ repair: api_styles extraction defect

async def styles_one(a: dict) -> None:
    """Pass-1 notes rarely named the API style (the rubric didn't ask), so extraction defaulted to ['None'] for
    apps with a documented API. Re-read the saved notes (no new web research) and fill it in."""
    from typing import List, Literal

    from pydantic import BaseModel

    class Styles(BaseModel):
        api_styles: List[Literal["REST", "GraphQL", "SOAP", "gRPC", "WebSocket", "SDK/CLI only", "None"]]

    r = read("final", a["id"])
    if not r or r["api_styles"] != ["None"] or r["api_breadth"] == "none":
        return
    notes = "\n\n".join((DATA / "notes" / f"{a['id']:03d}_{k}.md").read_text(encoding="utf-8")
                        for k in ("pass1", "skeptic") if (DATA / "notes" / f"{a['id']:03d}_{k}.md").exists())
    notes += "\nEvidence URLs: " + " ".join(e["url"] for e in r["evidence"]) + f"\nDocs: {r['docs_url']}"
    st = await llm.extract(Styles, f"Which API styles does {a['app']} offer to external developers, per these notes? "
                           "A documented HTTP/JSON API with resource endpoints is REST. Use 'None' only if there is no API.", notes)
    r["api_styles"] = st.api_styles
    r.setdefault("_repairs", []).append({"field": "api_styles", "from": ["None"], "to": st.api_styles})
    write("final", a["id"], r)
    log(f"styles {a['id']:3d} {a['app']:<28} -> {st.api_styles}")


# ------------------------------------------------------------------ human sample + scoring

def sample() -> None:
    rows = apps()
    rnd = random.Random(154)
    picked = []
    for cat in dict.fromkeys(r["category"] for r in rows):
        picked += rnd.sample([r for r in rows if r["category"] == cat], 2)
    VER.mkdir(exist_ok=True)
    path = VER / "human_sample.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "app", "hint", "field", "allowed_values", "truth", "source_url", "note"])
        for r in picked:
            for fld in SCORED_FIELDS:
                w.writerow([r["id"], r["app"], r["hint"], fld, " | ".join(sorted(ENUMS[fld])), "", "", ""])
    print(f"wrote {path} ({len(picked)} apps x {len(SCORED_FIELDS)} fields). Fill 'truth' WITHOUT looking at agent output,"
          " then save as verification/human_labels.csv")


def score() -> None:
    labels = list(csv.DictReader(open(VER / "human_labels.csv", encoding="utf-8")))
    res = {"pass1": [0, 0], "final": [0, 0]}
    rows = []
    for l in labels:
        if not l["truth"].strip():
            continue
        i = int(l["id"])
        truth = {t.strip() for t in l["truth"].split("|")}  # '|' = more than one acceptable answer
        for stage in ("pass1", "final"):
            rec = read(stage, i)
            ok = rec is not None and rec[l["field"]] in truth
            res[stage][0] += ok
            res[stage][1] += 1
        rows.append({"id": i, "app": l["app"], "field": l["field"], "truth": l["truth"],
                     "pass1": read("pass1", i)[l["field"]], "final": read("final", i)[l["field"]],
                     "source_url": l["source_url"], "note": l["note"]})
    out = {"accuracy": {k: {"correct": v[0], "total": v[1], "pct": round(100 * v[0] / max(v[1], 1), 1)}
                        for k, v in res.items()}, "rows": rows}
    (VER / "score.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out["accuracy"], indent=1))


# ------------------------------------------------------------------ main

async def run_stage(stage: str, rows: list[dict], conc: int) -> None:
    fn = {"research": research_one, "skeptic": skeptic_one, "adjudicate": adjudicate_one, "reconcile": reconcile_one, "styles": styles_one}[stage]
    results = await llm.gather_limited([fn(a) for a in rows], conc)
    for a, r in zip(rows, results):
        if isinstance(r, Exception):
            log(f"ERROR {stage} {a['id']} {a['app']}: {type(r).__name__}: {str(r)[:300]}")


def main() -> None:
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["research", "oracles", "skeptic", "adjudicate", "reconcile", "styles", "sample", "score", "all"])
    ap.add_argument("--only", help="comma-separated app ids")
    ap.add_argument("--concurrency", type=int, default=6)
    args = ap.parse_args()
    only = {int(x) for x in args.only.split(",")} if args.only else None
    rows = apps(only)
    stages = ["research", "oracles", "skeptic", "adjudicate", "reconcile", "styles"] if args.stage == "all" else [args.stage]
    for st in stages:
        log(f"== stage {st} on {len(rows)} apps")
        if st == "oracles":
            import os
            catalog = None
            if os.environ.get("COMPOSIO_API_KEY"):
                from . import oracles as orc
                try:
                    catalog = orc.composio_catalog()
                    log(f"composio catalog: {len(catalog)} toolkits")
                except Exception as e:  # noqa: BLE001
                    log(f"Composio catalog unavailable ({type(e).__name__}: {str(e)[:120]}); continuing without it")
            else:
                log("COMPOSIO_API_KEY not set: skipping Composio catalog oracle")
            for a in rows:
                oracles_one(a, catalog)
        elif st == "sample":
            sample()
        elif st == "score":
            score()
        else:
            llm.reset_clients()  # fresh client per event loop
            asyncio.run(run_stage(st, rows, args.concurrency))


if __name__ == "__main__":
    sys.exit(main())
