# Model Selection Guide

How to choose and assign models across your multi-agent system for optimal cost and quality.

## Discovering Available Models

Run this command to see every model available from your configured providers:

```bash
opencode models
```

This lists all models grouped by provider, with their IDs and capabilities. Use the exact model ID from this output when configuring agents.

## The Three-Tier System

Every model falls into one of three cost tiers. The goal is to use the cheapest model that delivers acceptable quality for each role.

### FREE Tier (Subscription / Zero Per-Token Cost)

Models included with a provider subscription that have no per-token charges. These handle the majority of agent work.

**Assigned to**: orchestrator, plan, review-lead, ops-specialist, wiki-curator

**Why**: Routing, planning, and review tasks are high-volume but don't require frontier intelligence. A good free model handles these with minimal quality loss compared to paid alternatives. Since the orchestrator processes every request, using a free model here has the largest cost impact.

### MID Tier (Pay-Per-Token Coding Models)

Models optimized for code generation, typically with per-token pricing. Used only where code quality directly impacts output.

**Assigned to**: python-pro, project-dev, frontend-dev, other implementation specialists

**Why**: Code generation benefits most from model quality. Implementation specialists write production code, so the quality investment pays off. These agents are invoked less frequently than the orchestrator (only when implementation is needed), keeping total cost manageable.

### PREMIUM Tier (Frontier Models)

The most capable (and expensive) models available. Never assigned as defaults.

**Assigned to**: Nothing by default. Manual override only.

**When to use**: Hard architectural decisions, subtle debugging, or when a MID-tier model keeps producing wrong code. Override by specifying the model directly in a prompt or changing the agent's model field temporarily.

## Placeholder Reference

These placeholders appear in agent frontmatter and `opencode.json`. Replace them with actual model IDs from `opencode models`:

| Placeholder | Tier | Where Used | Role |
|---|---|---|---|
| `YOUR_FREE_ROUTING_MODEL` | FREE | orchestrator.md | Fast routing and delegation decisions |
| `YOUR_FREE_STRONG_MODEL` | FREE | plan.md, review-lead.md, ops-specialist.md, wiki-curator.md | Analysis, investigation, review |
| `YOUR_FREE_FAST_MODEL` | FREE | opencode.json (`small_model`) | Quick summaries, compaction |
| `YOUR_PAID_CODEX_MODEL` | MID | python-pro.md, _project-dev-template.md, opencode.json | Code generation, editing, and variant config |

## Reasoning Variants

Some models support reasoning variants that control how much compute the model spends thinking before responding. Variants are specified with a colon suffix on the model ID:

```
YOUR_PAID_CODEX_MODEL:high     # More reasoning, better for complex code
YOUR_PAID_CODEX_MODEL:xhigh    # Maximum reasoning, for the hardest problems
```

Variants are defined in `opencode.json` under `provider.<name>.models.<id>.variants`:

```json
{
  "variants": {
    "high": {
      "reasoningEffort": "high",
      "textVerbosity": "low"
    },
    "xhigh": {
      "reasoningEffort": "xhigh",
      "textVerbosity": "low"
    }
  }
}
```

**When to use variants**:
- `:high` -- Default for implementation specialists. Good balance of quality and cost.
- `:xhigh` -- Use for debugging subtle issues, complex refactors, or architecture-level changes. Costs more tokens due to extended reasoning.
- No variant -- Plain model ID for tasks that don't benefit from extended reasoning (routing, simple edits).

## Assignment Matrix

| Agent | Tier | Variant | Rationale |
|---|---|---|---|
| orchestrator | FREE | none | Processes every request. Routing doesn't need reasoning. Cost-critical. |
| plan | FREE | none | Investigation is IO-bound (reading files), not reasoning-bound. |
| python-pro | PAID | :high | Writes production code. Reasoning improves correctness. |
| ops-specialist | FREE | none | Systems knowledge is pattern-matching, not deep reasoning. |
| wiki-curator | FREE | none | Writing documentation from read context. Not computationally hard. |
| review-lead | FREE | none | Routing + synthesis. Volume makes paid models expensive. |
| project-dev | PAID | :high | Same rationale as python-pro -- writes project-specific code. |
| frontend-dev | PAID | :high | Same rationale -- code generation benefits from quality. |

## Compaction & Context Tuning

The `compaction` settings in `opencode.json` control when Opencode compresses conversation history to free up context space. This matters more than you'd expect — some models degrade well before hitting their nominal context limit.

```json
{
  "compaction": {
    "auto": true,
    "prune": true,
    "reserved": 24000
  }
}
```

| Setting | Default | What It Does |
|---------|---------|--------------|
| `auto` | `true` | Compact automatically when context fills up |
| `prune` | `true` | Remove old tool outputs (biggest token saver) |
| `reserved` | `24000` | Token buffer — compaction triggers when this much space remains |

**Why `reserved: 24000` instead of 10000?**

Some models (GLM/ZhipuAI CodingPlan, smaller-context models) degrade at 50-60% context utilization — well before the technical limit. A larger reserve triggers compaction earlier, keeping the model in its effective range. Models with reliable full-context performance (Claude, GPT-4.1) can use `reserved: 10000` instead.

**Tuning for your models:**
- Models with 128K+ context and good long-range attention: `reserved: 10000`
- Models with known degradation before limit (GLM, some open-source): `reserved: 24000-40000`
- Models with 32K or smaller context: `reserved: 8000` (compaction too aggressive wastes context)

## Provider Timeout Settings

Slow providers or models with extended reasoning can hit default timeouts. The config includes provider-level timeouts:

```json
{
  "provider": {
    "openai": {
      "options": {
        "timeout": 600000,
        "chunkTimeout": 45000
      }
    }
  }
}
```

| Setting | Default | What It Does |
|---------|---------|--------------|
| `timeout` | `300000` (5 min) | Total request timeout in ms |
| `chunkTimeout` | `30000` (30s) | Max silence between streamed chunks — aborts if exceeded |

Increase `timeout` if reasoning models take long on complex prompts. Increase `chunkTimeout` if your provider is intermittently slow (unstable connection, overloaded endpoint). Set `timeout: false` to disable entirely (not recommended).

## Cost Optimization Tips

1. **Start with all FREE models.** Only upgrade to PAID when you notice quality gaps in generated code.

2. **Monitor token usage by agent.** If the orchestrator is consuming more tokens than specialists, it's doing too much work itself instead of delegating.

3. **Use `:high` not `:xhigh` by default.** The extra reasoning in `:xhigh` is rarely needed and doubles the thinking token cost.

4. **Don't assign PREMIUM models as defaults.** Override manually for specific hard problems. If you find yourself overriding frequently, the MID model may not be good enough for your codebase.

5. **Free models for read-only agents.** Any agent that only reads code (plan, review-lead) can use a free model without quality loss, since their output is analysis, not code.

6. **Recheck after provider updates.** Providers frequently add new models and change pricing. Run `opencode models` periodically and reassess assignments.
