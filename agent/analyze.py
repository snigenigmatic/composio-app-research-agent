"""Aggregate per-app JSON into data/results.json (+ results.csv) and pattern stats for the page.

python -m agent.analyze
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .pipeline import DATA, VER, apps, read
from .schema import SCORED_FIELDS

ROOT = DATA.parent


def build() -> dict:
    rows = []
    for a in apps():
        fin = read("final", a["id"])
        p1 = read("pass1", a["id"])
        orc = read("oracles", a["id"]) or {}
        rec = fin or p1
        if not rec:
            rows.append({"id": a["id"], "app": a["app"], "category": a["category"], "missing": True})
            continue
        sk = read("skeptic", a["id"]) or {}
        r = {k: v for k, v in rec.items() if not k.startswith("_")}
        r.update({
            "id": a["id"],
            "hint": a["hint"],
            "stage": "final" if fin else "pass1",
            "pass1": {f: p1[f] for f in SCORED_FIELDS} if p1 else {},
            "changed": [f for f in SCORED_FIELDS if p1 and rec[f] != p1[f]],
            "trail": rec.get("_trail", []),
            "needs_human": rec.get("_needs_human", []),
            "skeptic": [{k: v.get(k) for k in ("field", "verdict", "corrected_value", "url", "reason")}
                        for v in sk.get("verdicts", [])],
            "composio": orc.get("composio"),
            "mcp_registry": {k: orc.get("mcp_registry", {}).get(k) for k in ("status", "official", "community_count")},
            "evidence_check": orc.get("evidence", []),
            "oracle_flags": orc.get("flags", []),
            "cost": {k: rec.get("_meta", {}).get(k) for k in ("searches", "fetches", "in_tok", "out_tok", "secs")},
        })
        rows.append(r)
    return {"apps": rows, "stats": stats([r for r in rows if not r.get("missing")])}


def stats(rows: list[dict]) -> dict:
    cats = list(dict.fromkeys(r["category"] for r in rows))
    s: dict = {"n": len(rows), "categories": cats}
    s["primary_auth"] = Counter(r["primary_auth"] for r in rows).most_common()
    s["any_auth"] = Counter(m for r in rows for m in set(r["auth_methods"])).most_common()
    s["oauth_any"] = sum("OAuth2" in r["auth_methods"] for r in rows)
    s["multi_auth"] = sum(len(set(r["auth_methods"])) > 1 for r in rows)
    s["access"] = Counter(r["access"] for r in rows).most_common()
    s["buildability"] = Counter(r["buildability"] for r in rows).most_common()
    s["blocker"] = Counter(r["blocker"] for r in rows if r["blocker"] != "none").most_common()
    s["mcp"] = Counter(r["mcp"] for r in rows).most_common()
    s["api_breadth"] = Counter(r["api_breadth"] for r in rows).most_common()
    s["openapi"] = Counter(r["openapi_spec"] for r in rows).most_common()
    s["webhooks"] = Counter(r["webhooks"] for r in rows).most_common()
    s["sandbox"] = Counter(r["sandbox"] for r in rows).most_common()

    by_cat: dict = defaultdict(lambda: defaultdict(Counter))
    for r in rows:
        for f in ("access", "buildability", "primary_auth", "mcp", "blocker"):
            by_cat[r["category"]][f][r[f]] += 1
    s["by_category"] = {c: {f: dict(v) for f, v in d.items()} for c, d in by_cat.items()}

    # self-serve share per category = self_serve_free + self_serve_trial
    s["self_serve_share"] = {c: round(100 * (d["access"].get("self_serve_free", 0) + d["access"].get("self_serve_trial", 0))
                                      / sum(d["access"].values())) for c, d in by_cat.items()}
    s["ready_share"] = {c: round(100 * d["buildability"].get("ready", 0) / sum(d["buildability"].values()))
                        for c, d in by_cat.items()}

    # Composio overlap
    in_comp = [r for r in rows if r.get("composio")]
    composio_checked = any("composio" in (read("oracles", r["id"]) or {}) and (read("oracles", r["id"]) or {}).get("composio") is not None for r in rows)
    s["in_composio"] = len(in_comp) if composio_checked else None
    s["easy_wins_new"] = [r["app"] for r in rows if r["buildability"] == "ready" and not r.get("composio")]
    s["outreach"] = [{"app": r["app"], "blocker": r["blocker"], "notes": r["blocker_notes"]}
                     for r in rows if r["buildability"] == "needs_outreach"]
    s["blocked"] = [{"app": r["app"], "blocker": r["blocker"], "notes": r["blocker_notes"]}
                    for r in rows if r["buildability"] == "blocked"]

    # Verification stats
    disputes = Counter(t["field"] for r in rows for t in r["trail"])
    changed = Counter(f for r in rows for f in r["changed"])
    s["verify"] = {
        "skeptic_disagree": Counter(v["field"] for r in rows for v in r["skeptic"] if v["verdict"] == "disagree"),
        "skeptic_unsure": Counter(v["field"] for r in rows for v in r["skeptic"] if v["verdict"] == "unsure"),
        "oracle_flags": Counter(fl["field"] for r in rows for fl in r["oracle_flags"]),
        "disputed_fields": disputes,
        "changed_fields": changed,
        "apps_changed": sum(bool(r["changed"]) for r in rows),
        "needs_human": [{"app": r["app"], "fields": r["needs_human"]} for r in rows if r["needs_human"]],
    }
    ev = [e for r in rows for e in r["evidence_check"]]
    s["evidence"] = {
        "total": len(ev),
        "reachable": sum(e["status"] == 200 for e in ev),
        "blocked_bot": sum(e["status"] in (401, 403, 429) for e in ev),
        "dead": sum(e["status"] in (404, 410) for e in ev),
        "quote_found": sum(e["quote_found"] is True for e in ev),
        "quote_missing": sum(e["quote_found"] is False for e in ev),
        "quote_unverifiable": sum(e["quote_found"] is None for e in ev),
    }
    cost = [r["cost"] for r in rows if r["cost"].get("in_tok")]
    s["cost_pass1"] = {k: sum((c.get(k) or 0) for c in cost) for k in ("searches", "fetches", "in_tok", "out_tok")}
    s["confidence"] = Counter(r["confidence"] for r in rows).most_common()
    s["low_confidence"] = [r["app"] for r in rows if r["confidence"] == "low"]
    s["registry_official"] = sum((r["mcp_registry"] or {}).get("status") == "official" for r in rows)
    s["oauth_app_review"] = sum(r["primary_auth"] == "OAuth2" and r["access"] == "app_review" for r in rows)
    keyish = [r for r in rows if r["primary_auth"] in ("API key", "Bearer/PAT token", "Basic", "Bot token")]
    s["keyish"] = {"n": len(keyish), "self_serve": sum(r["access"].startswith("self_serve") for r in keyish)}
    tok = {"in": 0, "out": 0, "searches": 0}
    for r in rows:
        for st in ("pass1", "skeptic"):
            m = (read(st, r["id"]) or {}).get("_meta", {})
            tok["in"] += m.get("in_tok") or 0
            tok["out"] += m.get("out_tok") or 0
            tok["searches"] += m.get("searches") or 0
    s["tokens"] = tok
    sc = VER / "score.json"
    s["human_score"] = json.loads(sc.read_text()) if sc.exists() else None
    return s


def main() -> None:
    out = build()
    (DATA / "results.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=dict), encoding="utf-8")
    cols = ["id", "app", "category", "one_liner", "primary_auth", "auth_methods", "access", "access_notes", "api_styles",
            "api_breadth", "openapi_spec", "webhooks", "sandbox", "mcp", "mcp_notes", "buildability", "blocker",
            "blocker_notes", "docs_url", "confidence"]
    with open(DATA / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols + ["evidence_urls"])
        for r in out["apps"]:
            if r.get("missing"):
                continue
            w.writerow([("; ".join(r[c]) if isinstance(r[c], list) else r[c]) for c in cols]
                       + ["; ".join(e["url"] for e in r["evidence"])])
    s = out["stats"]
    print(json.dumps({k: s[k] for k in ("n", "primary_auth", "access", "buildability", "blocker", "mcp", "in_composio")},
                     indent=1, default=dict))


if __name__ == "__main__":
    main()
