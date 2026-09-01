---
name: model-radar
description: "Research the current generation of AI models — capability and real cost — and route each of Peter's projects to the right one."
---

# Model Radar

Pick the right model per project on capability and real cost. Output is a published HTML artifact, updated in place. Default run is a **diff against the last snapshot**, not a full sweep.

## Non-negotiables

1. **Never quote a price from one source.** Every price that reaches the output is confirmed against at least two of: OpenRouter JSON, the first-party pricing page, Artificial Analysis. Prices move weekly and promos expire.
2. **Never quote a benchmark score without its version and date.** AA Intelligence Index v4.1.1 scores are not comparable to v4.0. Terminal-Bench 4.0 ≠ v2.1.
3. **The composite index is not the decision.** AA's Intelligence Index collapses 9 evals into one number. Route on the benchmark that matches the workload (§4), then use the composite only as a sanity check.
4. **Blended price is a lie for Peter's workloads.** AA assumes 3:1 input:output. RAG is input-heavy, agentic coding is output-heavy. Always recompute from raw in/out/cache rates (§5).
5. **Recommend a switch only if it clears the gate (§6).** A model that is 5% better and 10% cheaper is not worth a migration.

## 1. Load state

Before researching, recall the prior run so this is a diff:

- `mcp__AI_Brain__search_thoughts` for `"Model Radar snapshot"` — returns last run's date, the per-project routing table, prices, and index scores.
- The same snapshot holds the **artifact URL**. Republish to that URL (`Artifact` with `url:`, after `action: "read"`) so Peter keeps one bookmark. If no URL is stored, publish new and record it.

If no snapshot exists, do a full sweep and say so.

## 2. Pricing spine — OpenRouter JSON

Public, unauthenticated, machine-readable, includes cache and batch rates. This is the fastest way to see the whole market's real prices at once:

```bash
curl -s "https://openrouter.ai/api/v1/models" | python3 -c "
import json,sys
d=json.load(sys.stdin)['data']
want=['glm-5.3','claude-sonnet-5','claude-opus-5','claude-haiku','gemini-3.7','gpt-5.6','deepseek-v4','kimi-k3','qwen3.8','grok']
for m in d:
    if any(w in m['id'].lower() for w in want):
        p=m.get('pricing',{})
        f=lambda k:(round(float(p[k])*1e6,4) if p.get(k) else None)
        print(f\"{m['id']:<45} ctx={m.get('context_length')} in={f('prompt')} out={f('completion')} cache_r={f('input_cache_read')} cache_w={f('input_cache_write')}\")
"
```

`:batch` suffixed IDs give batch pricing. Note OpenRouter's rate can carry routing markup and, for open-weight models, varies by upstream provider — so confirm against first-party before recommending.

## 3. Source hierarchy

### Capability + cost, normalized (backbone)
| Source | URL | Good for | Failure mode |
|---|---|---|---|
| **Artificial Analysis** | `artificialanalysis.ai/models`; API `artificialanalysis.ai/api/v2` (`x-api-key`, free tier 100 req/24h, docs at `/data-api/docs`) | The only source measuring intelligence + speed + price on one axis. Index v4.1.1 = GDPval-AA v2, τ³-Banking, Terminal-Bench v2.1, SciCode, HLE, GPQA Diamond, CritPt, AA-Omniscience, AA-LCR | Opaque composite weighting; 3:1 blended price; ignores caching/batch; reasoning-effort settings are separate rows with very different cost; index version churn; commercially close to the vendors it rates |
| llm-stats.com | `llm-stats.com/leaderboards/llm-leaderboard` | Cross-check; hourly price revalidation | Operated by ZeroEval, a gateway vendor. Republishes vendor-reported benchmarks uncritically |
| Epoch AI | `epoch.ai/data/ai-benchmarking-dashboard`; bulk `epoch.ai/data/benchmark_data.zip`; `pip install epochai` | Bulk historical benchmark data, CC BY. Best for "how has this moved over time" | Mixed provenance — check the source column. **No pricing** |

### Adoption signal
- **OpenRouter rankings** `openrouter.ai/rankings` (1d/7d/30d/trending, CC BY 4.0). Real usage share — good early signal that a model actually works in production. Biased to cost-sensitive indie devs, coding agents, and roleplay; enterprise traffic goes direct and is invisible, so frontier models are under-represented.
- **Arena** `arena.ai/leaderboard` — **rebranded from lmarena.ai, which now 302s.** 15 arenas (Agent, Chat, Code, WebDev, Vision, Document, Search…). Blind pairwise human preference. Measures *likeability* — formatting, length, confidence — not correctness. No API, no cost signal. Use as a tiebreaker on subjective quality only.

### Task-specific benchmarks — pick by workload
| Workload | Benchmark | URL |
|---|---|---|
| Agentic coding | SWE-bench Verified / Multilingual / Bash Only | `swebench.com` |
| Terminal/agent tasks | Terminal-Bench 4.0 | `tbench.ai/leaderboard`; repo moved to `github.com/harbor-framework/terminal-bench` |
| Function calling reliability | BFCL V4 (updated Apr 2026) | `gorilla.cs.berkeley.edu/leaderboard`; raw responses at `github.com/HuanzhiMao/BFCL-Result` |
| Multi-turn tool + user interaction | τ²-bench / τ³ | `github.com/sierra-research/tau2-bench` (τ³ on `dev/tau3`) |
| Long-context reasoning (closest thing to a RAG proxy) | AA-LCR | `artificialanalysis.ai/evaluations/artificial-analysis-long-context-reasoning`; open at HF `ArtificialAnalysis/AA-LCR` |
| Abstract reasoning, **with cost-per-task plotted** | ARC-AGI-2/3 | `arcprize.org/leaderboard` |
| Legal / finance / medical domain accuracy | Vals AI (current through Aug 2026) | `vals.ai/benchmarks` — commercial vendor; some benchmarks co-branded with the vendor measured (e.g. Harvey). Read with that conflict in mind |

**There is no consensus end-to-end RAG benchmark in 2026.** AA-LCR tests long-context reasoning, not retrieval quality, and its 100 questions top out at 100k tokens — well below the 1M windows now shipping. For COPA Commander, treat leaderboards as a shortlist filter and settle it with an eval on real COPA questions (§7).

### First-party pricing — verified URLs, with the traps
| Vendor | Use this | Trap |
|---|---|---|
| Anthropic | `platform.claude.com/docs/en/about-claude/pricing` | `anthropic.com/pricing` returns **406** to fetchers |
| OpenAI | `openai.com/api/pricing/` | — |
| Google | `ai.google.dev/gemini-api/docs/pricing` | Contains **time-limited promos** with expiry dates — read the fine print |
| xAI | `docs.x.ai/docs/models` | — |
| Mistral | `mistral.ai/pricing/api` | `mistral.ai/pricing` is the consumer Vibe subscription — wrong page |
| Z.ai (GLM) | `docs.z.ai/guides/overview/pricing` | Promo pricing with hard expiry dates |
| Moonshot / Kimi | `platform.kimi.ai/docs/pricing/chat` | `platform.moonshot.ai` **302s to kimi.ai** |
| Alibaba Qwen | `alibabacloud.com/help/en/model-studio/billing-for-model-studio` | Prices are **region-scoped** (Singapore/Intl vs mainland). `/model-studio/models` is a catalog with no prices |
| DeepSeek | `api-docs.deepseek.com/quick_start/pricing` (JS-rendered — fall back to OpenRouter JSON) | `platform.deepseek.com/api-docs/pricing` is a **stale 2024 page**. Never use it |
| Meta Llama | **No first-party price exists.** `llama.developer.meta.com/pricing` 404s | Source per-provider (Together, Groq, Fireworks, Bedrock) via OpenRouter |

### Do not use — verified stale as of 2026-08-31
- **Aider polyglot leaderboard** (`aider.chat/docs/leaderboards`) — newest entry `gpt-5 (high)`, 2025-08-23. **12 months stale.** Epoch's mirror inherits the same ceiling.
- **LiveBench** (`livebench.ai`) — repo active but question set still dated `2025-04-25`. Its whole premise is monthly refresh; contamination risk is now high.
- Re-check both on each run; if either resumes, restore it.

## 4. Workload archetypes → what actually matters

Map the project to an archetype before looking at any leaderboard.

| Archetype | Peter's projects | Dominant metric | Dominant cost lever |
|---|---|---|---|
| **Grounded RAG Q&A** | COPA Commander | AA-LCR, hallucination/faithfulness, instruction-following | Input tokens + **cache read rate** — usually 10–20x the lever that headline input price is |
| **Bulk summarization / transcript** | Ask COPA U, Sekai | Cheap adequate quality; long context | **Batch discount** (often 50%) |
| **Background analysis jobs** | Already.dev (Trigger.dev) | Reasoning depth, structured output reliability | **Batch** — latency doesn't matter, so never pay interactive rates |
| **Agentic coding** | Peter's own dev loop | SWE-bench Verified, Terminal-Bench 4.0 | Output tokens; scaffold matters as much as model |
| **Tool-calling agent** | Unreleased AI customer support | BFCL V4, τ³ | Reliability >> price — a failed tool call costs more than the token savings |
| **Realtime voice** | AI customer support | **TTFT and tok/s, not intelligence** | Latency; a smarter slow model is the wrong answer |
| **Light classification / metadata** | OurChannel, Haro Haps | Almost nothing — any current small model clears the bar | Raw input price; pick the cheapest that passes |

## 5. Cost math

Compute effective $ per 1M tokens **on the project's actual shape**, never AA's blended figure:

```
effective = (in_tok × in_rate × (1 − cache_hit_rate))
          + (in_tok × cache_read_rate × cache_hit_rate)
          + (out_tok × out_rate)
          × (0.5 if batch-eligible else 1.0)
```

- Estimate `in_tok:out_tok` from the project, not from a default. RAG runs 50:1 or worse; agentic coding runs closer to 1:2.
- Assume a realistic `cache_hit_rate` for RAG with a stable system prompt and corpus — it is the single biggest lever and headline prices hide it.
- **Reasoning models bill their thinking tokens as output.** A model with a low output rate that thinks for 3,000 tokens can cost more per task than an expensive model that answers directly. Where available, compare **cost per completed task** (ARC Prize plots this natively; AA publishes cost-per-task articles) rather than cost per token.
- Check promo expiry dates and state them. A recommendation resting on a promo that lapses in three weeks is not a recommendation.

## 6. The switch gate

Recommend moving an existing project only if **A and B and C**:

- **A. Material win.** ≥40% effective cost reduction at current volume, **or** a capability gap on the archetype's own benchmark that's outside noise (≥3 points on AA index, or a clear win on the task-specific board).
- **B. Volume justifies it.** Annualized saving exceeds a day of Peter's time. Below that, say "not worth the migration" explicitly.
- **C. No disqualifying non-price factor:**
  - **Data residency and jurisdiction** — GLM (Z.ai), Qwen (Alibaba), DeepSeek, Kimi are Chinese providers. For COPA member data and anything with PII this may be a hard no regardless of price. **Raise it every time, don't assume.**
  - Rate limits and uptime track record.
  - Latency, if the archetype is interactive.
  - Tool-calling / structured-output reliability, if the project depends on it.
  - Provider durability — will this API exist in a year.

For a **new** build, the gate is lower: prefer the cheapest model that clears the archetype's capability bar, and note the fallback.

Always state a **fallback model** alongside the recommendation. Cheap fast models get deprecated and rate-limited; the design should tolerate a swap.

## 7. Verify before switching

A leaderboard shortlists; it never decides. Before Peter migrates a live project, propose a concrete A/B on his own data — e.g. 30–50 real COPA questions scored against known-good answers for Commander. Offer to build it. Say plainly when a recommendation is leaderboard-only and unverified on his workload.

## 8. Output — HTML artifact

Load `artifact-design` before writing. Publish with the `Artifact` tool; **republish to the stored URL** so Peter keeps one bookmark. Structure:

1. **Verdict line** — what, if anything, should change since last run. If nothing, say so in one sentence and stop the reader there.
2. **Routing table** — project · archetype · current model · recommended model · effective $/1M on that project's shape · Δ vs last run · switch? (yes / no / watch).
3. **What changed since `<last snapshot date>`** — new releases, price moves, deprecations, promo expiries. This is the section Peter reads.
4. **Watch list** — models close to clearing the gate, and what would tip them.
5. **Sources and dates** — every price with its source and retrieval date, every score with its benchmark version. Flag anything unverified.

Keep it scannable. Peter is deciding, not studying.

## 9. Save the snapshot

End every run with `mcp__AI_Brain__capture_thought`, type `reference`, titled `Model Radar snapshot — YYYY-MM-DD`, containing: the routing table, every price with source, index scores with version, the artifact URL, promo expiry dates to re-check, and source-health flags (anything newly stale or moved). Next run diffs against this. Also `remember_fact` any durable decision ("COPA Commander runs on X as of <date>").

## Verification checklist

Before publishing:
- [ ] Every recommended model's price confirmed from ≥2 sources
- [ ] Every benchmark score carries version + date
- [ ] Effective cost computed on the project's real token shape, not blended
- [ ] Cache and batch rates factored where applicable
- [ ] Promo expiry dates checked and stated
- [ ] Data-residency raised for every non-US provider recommended
- [ ] Switch gate applied — no recommendation below threshold
- [ ] Stale sources (Aider, LiveBench) re-checked, not silently used
- [ ] Artifact republished to the stored URL, not a new one
- [ ] Snapshot saved to AI Brain