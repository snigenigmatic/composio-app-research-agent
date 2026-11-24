# App research agent: 100 apps → agent-toolkit readiness

An agent pipeline that researches, for each app: auth method(s), self-serve vs gated access, API surface,
existing MCP servers, and whether it can become an agent toolkit today (plus the blocker if not). It then
verifies its own answers with independent loops and a blind, independently labelled sample (Claude Sonnet, a different model family; see verification/HAND_CHECK.md).

- **Case study (live):** https://snigenigmatic.github.io/composio-app-research-agent/
- **Results for machines:** [`docs/results.json`](docs/results.json) · [`docs/results.csv`](docs/results.csv)

## How it works

```
apps.csv ─► 1 Researcher ─► 2 Oracles (no LLM) ─► 3 Skeptic ─► 4 Adjudicator ─► 5 Human sample
            LLM + web search  Composio catalog,      tries to      settles each      20 apps × 5 fields,
            → typed record    MCP Registry,          falsify each   disputed field   labelled blind,
            + evidence quotes evidence-URL fetch     scored field   or → human queue  scores pass 1 vs final
```

| Stage | File | What it does |
|---|---|---|
| research | `agent/pipeline.py` `research_one` | Researcher agent with hosted web search writes notes with `field \| URL \| quote` evidence, then a structured-output call turns them into an `AppRecord` (`agent/schema.py`). |
| oracles | `agent/oracles.py` | **Composio SDK** `toolkits.list()`: is there already a Composio toolkit, and which auth schemes does it use? **MCP Registry**: domain-verified namespaces (`com.stripe/…`) prove an *official* MCP. **Evidence check**: fetch every cited URL and test whether the quote is actually on the page. Any conflict becomes a flag. |
| skeptic | `research` prompt `SKEPTIC_*` | A second, independent agent run that tries to falsify each scored field against primary docs. |
| adjudicate | `adjudicate_one` | For every field the skeptic or an oracle disputes, a third run reads both sides plus the sources and decides, or marks it `unresolved` for a human. |
| sample / score | `sample`, `score` | Stratified sample of 20 apps (2 per category). A labeller (here, a blind Claude Sonnet run) records the truth (`verification/HAND_CHECK.md`), then `score` computes pass-1 vs final accuracy. |

Every intermediate is kept: `data/pass1/`, `data/oracles/`, `data/skeptic/`, `data/final/` (JSON per
app) and `data/notes/` (the agents' raw notes), so any answer can be traced.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env    # OPENAI_API_KEY (default backend) or ANTHROPIC_API_KEY, plus COMPOSIO_API_KEY
python -m agent.pipeline all --only 81,15,84 --concurrency 3   # 3 apps end to end
python -m agent.pipeline all --concurrency 8                   # all 100 (resumable)
python -m agent.pipeline sample                                # blank worksheet for the blind check
python -m agent.pipeline score                                 # after verification/human_labels.csv exists
python -m agent.analyze                                        # data/results.json + results.csv + stats
python site/build.py                                           # docs/index.html (the case study)
```

The LLM backend is switchable. `LLM_PROVIDER=openai` (Responses API + hosted `web_search`, default model
`gpt-5`) or `LLM_PROVIDER=anthropic` (Messages API + `web_search`/`web_fetch`, default `claude-opus-5-5`).
`RESEARCH_MODEL` and `RESEARCH_EFFORT` override the model and reasoning effort.
This run used OpenAI `gpt-5`.

Stages skip apps that already have output, so a crashed run resumes where it stopped. Delete
`data/<stage>/<id>.json` to redo one app.
