# Model Selection Guide

How to choose and assign models across your multi-agent system for optimal cost and quality.

## Discovering Available Models

Run this command to see every model available from your configured providers:

```bash
opencode models
```

This lists all models grouped by provider, with their IDs and capabilities. Use the exact model ID from this output when configuring agents.

## Optional Cost Tiers

These tiers are budgeting labels, not model roles or provider requirements. A
routing model can be subscription, usage-based, or local; the same is true for
a coding model. Use the labels when they help describe marginal cost, and choose
the least expensive model that still performs its assigned role reliably.

### SUB Tier (Subscription — Included with Your Plan)

Models included with a provider subscription, or local models with no marginal
per-token bill. These are often useful for high-volume agent work.

**Assigned to**: orchestrator, plan, review-lead, read-only reviewers, ops-specialist, wiki-curator

**Why**: Routing, planning, and review are high-volume. If an economical model
is reliable enough for those roles, using it for the orchestrator has the
largest cost impact because the orchestrator processes every request.

### MID Tier (Coding Models — Subscription or Pay-Per-Token)

The label commonly used for your strongest coding model. It can be
subscription, usage-based, or local. The point is capability, not billing.

**Assigned to**: python-pro, project-dev, frontend-dev, other implementation specialists

**Why**: Code generation benefits most from model quality. Implementation specialists write production code, so the quality investment pays off. These agents run less often than the orchestrator (only when implementation is needed), keeping total cost manageable.

### PREMIUM Tier (Frontier Models)

The most capable (and expensive) models available. Never assigned as defaults.

**Assigned to**: Nothing by default. Manual override only.

**When to use**: Hard architectural decisions, subtle debugging, or when a MID-tier model keeps producing wrong code. Override by specifying the model directly in a prompt or changing the agent's model field temporarily.

## Placeholder Reference

These placeholders appear in agent frontmatter and `opencode.json`. Replace them with actual model IDs from `opencode models`:

| Placeholder | Suggested tier | Where Used | Role |
|---|---|---|---|
| `YOUR_ROUTING_MODEL` | SUB | orchestrator.md | Fast routing and delegation decisions |
| `YOUR_ANALYSIS_MODEL` | SUB | plan.md, review-lead.md, `*-reviewer.md`, ops-specialist.md, wiki-curator.md | Analysis, investigation, review |
| `YOUR_FAST_MODEL` | SUB | opencode.json (`small_model`) | Titles and other lightweight tasks |
| `YOUR_CODE_MODEL` | MID | python-pro.md, project agents, example specialists | Code generation and editing |

Placeholder names describe roles, not providers or prices. Each replacement
must use the exact `provider/model-id` shown by `opencode models`.

## Reasoning Variants

Some models support **reasoning effort** settings that control how much compute the model spends thinking before responding. Higher reasoning effort produces better results for complex tasks at the cost of more tokens.

**Optional agent frontmatter for a compatible OpenAI-style model:**

```yaml
model: YOUR_CODE_MODEL
reasoningEffort: high    # Only when the selected provider/model supports it
```

The `reasoningEffort` field is passed directly to the provider as a model option. It is intentionally absent from the provider-neutral agent templates. Add it—or use that provider's equivalent option—only after selecting a compatible model.

**Configure default variants in `opencode.json`** (optional):

```json
{
  "provider": {
    "openai": {
      "models": {
        "gpt-5.3-codex": {
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
      }
    }
  }
}
```

**When to use reasoning effort**:
- `high` -- Default for implementation specialists. Good balance of quality and cost.
- `xhigh` -- Use for debugging subtle issues, complex refactors, or architecture-level changes. Costs more tokens due to extended reasoning.
- `medium` or `low` -- For simpler tasks where full reasoning is overkill.

**Note**: Reasoning options and accepted values vary by provider and model. OpenCode also supplies built-in variants for many popular models. Check `opencode models` and the provider documentation before applying an option globally.

## Assignment Matrix

| Agent | Tier | Reasoning | Rationale |
|-------|------|-----------|-----------|
| orchestrator | SUB | none | Processes every request. Routing doesn't need reasoning. Cost-critical. |
| plan | SUB | none | Investigation is IO-bound (reading files), not reasoning-bound. |
| python-pro | MID | high when supported | Writes production code. Reasoning can improve correctness. |
| ops-specialist | SUB | none | Systems knowledge is pattern-matching, not deep reasoning. |
| wiki-curator | SUB | none | Writing documentation from read context. Not computationally hard. |
| review-lead | SUB | none | Routing and synthesis are high-volume tasks. |
| project-dev | MID | high when supported | Same rationale as python-pro -- writes project-specific code. |
| frontend-dev | MID | high when supported | Same rationale -- code generation benefits from quality. |



## Compaction & Context Tuning

The `compaction` settings in `opencode.json` control when OpenCode compresses conversation history to free up context space. This matters more than you'd expect — some models degrade well before hitting their nominal context limit.

```json
{
  "compaction": {
    "auto": true,
    "prune": true,
    "reserved": 24000
}
```

| Setting | Default | What It Does |
|---------|---------|--------------|
| `auto` | `true` | Compact automatically when context fills up |
| `prune` | `true` | Remove old tool outputs (biggest token saver) |
| `reserved` | `24000` | Token buffer — compaction triggers when this much space remains |

**Why `reserved: 24000` instead of 10000?**

It is a conservative template default that leaves room for compaction before the context window is exhausted. It is not optimal for every model; measure real sessions and adjust it to the selected model's context window and long-context behavior.

**Tuning for your models:**
- Models with large context windows and reliable long-range attention: start around `reserved: 10000`
- Models that become unreliable late in the context window: try `reserved: 24000-40000`
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

1. **Start with models already covered by your subscriptions.** Move a role to a usage-based model when you identify a concrete quality or capability gap.

2. **Monitor token usage by agent.** If the orchestrator is consuming more tokens than specialists, it's doing too much work itself instead of delegating.

3. **Use `high` reasoning effort, not `xhigh`, by default.** The extra reasoning in `xhigh` is rarely needed and doubles the thinking token cost.

4. **Don't assign PREMIUM models as defaults.** Override manually for specific hard problems. If you find yourself overriding frequently, the MID model may not be good enough for your codebase.

5. **Subscription models for read-only agents.** Any agent that only reads code (plan, review-lead) works fine on a subscription model, since its output is analysis, not code.

6. **Recheck after provider updates.** Providers frequently add new models and change pricing. Run `opencode models` periodically and reassess assignments.

## Pay-Per-Token Alternative: OpenRouter & OpenCode Zen

If you want pay-per-token models instead of (or alongside) subscriptions, two options work well with OpenCode:

### OpenRouter

[OpenRouter](https://openrouter.ai) aggregates 300+ models from all major providers. You pick the model and pay per token.

Add to `opencode.json`:

```json
{
  "provider": {
    "openrouter": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "OpenRouter",
      "options": {
        "baseURL": "https://openrouter.ai/api/v1",
        "apiKey": "{env:OPENROUTER_API_KEY}"
      },
      "models": {
        "<vendor>/<model-id>": {
          "name": "Your coding model"
        }
      }
    }
  }
}
```

Set `export OPENROUTER_API_KEY=sk-or-v1-...` in your shell. Model IDs follow the format `openrouter/vendor/model-name`.

### OpenCode Zen

[OpenCode Zen](https://opencode.ai/docs/zen/) is OpenCode's optional model gateway. Run `/connect` in OpenCode, select "OpenCode Zen", and follow the authentication flow. Models use the `opencode/model-id` format.

### Mixing Subscription and Pay-Per-Token

You can use subscription models for the SUB tier and pay-per-token for the MID tier in the same setup. Set each agent's `model` field to the right provider:

```
orchestrator.md   → model: <subscription-provider>/<routing-model>
python-pro.md     → model: <usage-provider>/<coding-model>
```
