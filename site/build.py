"""Render docs/index.html (single self-contained file) from data/results.json + site/insights.json.

python site/build.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data" / "results.json").read_text(encoding="utf-8"))
insights = json.loads((ROOT / "site" / "insights.json").read_text(encoding="utf-8"))
tpl = (ROOT / "site" / "template.html").read_text(encoding="utf-8")


def embed(obj) -> str:
    # safe inside <script type="application/json">
    return json.dumps(obj, ensure_ascii=False, default=dict).replace("</", "<\\/")


html = tpl.replace("/*DATA*/", embed(data)).replace("/*INSIGHTS*/", embed(insights))
out = ROOT / "docs"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(html, encoding="utf-8")
for f in ("results.json", "results.csv"):
    shutil.copy(ROOT / "data" / f, out / f)
(out / ".nojekyll").write_text("")
print(f"wrote {out / 'index.html'} ({len(html) // 1024} KB)")
