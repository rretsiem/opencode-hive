# Opencode Hive

A multi-agent architecture for [Opencode](https://opencode.ai) with cost-optimized model routing, parallel specialist execution, and a self-maintaining project wiki.

## Why This Exists

Opencode has powerful features — subagents, custom tools, per-agent permissions, skill files, model variants — that I haven't seen used much in practice. Most setups are a single agent with one model. That works, but it leaves a lot on the table.

I built this because I wanted to use Opencode seriously without paying $200/month for Claude Max or ChatGPT Pro. My setup runs entirely on subscription plans: ChatGPT Plus ($20/month), [Minimax](https://platform.minimax.io/subscribe/token-plan?code=6u6t1KlmkF&source=link)\* ($20/month), and [Z.AI GLM Pro](https://z.ai/subscribe?ic=YBUR2UCCPY)\* ($90/quarter). Subscription models handle routing, planning, review, and even code generation. If you prefer pay-per-token for coding specialists, [OpenRouter](https://openrouter.ai) and [Opencode Zen](https://opencode.ai/docs/zen/) are good options — see [docs/model-selection.md](docs/model-selection.md#pay-per-token-alternative-openrouter--opencode-zen) for setup.

This is my configuration as a starting point. I write Python, so the included specialist is `python-pro`. For other languages, swap it for a specialist that matches your stack — see `examples/specialists/` for frontend, backend, database, and devops templates. Fork it, adjust it, make it yours.

\*Minimax and Z.AI links are referrals — 10% off for you.

## What This Is

An orchestrator delegates implementation to focused specialists based on the domain of each task. Lightweight subscription models handle routing and analysis. Stronger models — subscription or pay-per-token, your choice — handle code generation. Inspired by [Anthropic's multi-agent research](https://www.anthropic.com/engineering/multi-agent-research-system) and [Karpathy's LLM wiki concept](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Includes dev tools (skeleton, impact analysis, dead code detection), a self-maintaining project wiki, and parallel review with domain-specific specialists.

## Architecture

```
Tab cycle (primary agents — user switches between these):

  plan                          orchestrator
  (read-only, SUB model)       (router, SUB model)
  |                             |
  |-- reads code                |-- delegates to subagents:
  |-- produces plans            |
  |-- traces impact             +-- python-pro     (PAID model)
  |-- never modifies files      +-- ops-specialist  (SUB model)
                                +-- wiki-curator    (SUB model)
                                +-- [your specialists]

Project-level subagents (installed per-project):

  review-lead                   your-project-dev
  (SUB model, read-only)       (PAID model, full access)
  |                             |
  +-- routes diffs to           +-- knows your project's
      domain specialists            architecture & conventions
```

**Primary agents** appear in the Tab cycle -- the user switches between them directly. The `plan` agent investigates and plans; the `orchestrator` executes by delegating to specialists.

**Subagents** are hidden from the Tab cycle and invoked by primary agents via the Task tool. They do the actual work: writing code, reviewing diffs, maintaining the wiki.

**Smart routing**: The orchestrator reads the request, determines which specialist(s) are needed, and fans out in parallel. A Python refactor goes to `python-pro`. A deployment question goes to `ops-specialist`. A cross-cutting feature fans out to multiple specialists simultaneously.

## Quick Start

**Prerequisites**: [Opencode](https://opencode.ai) installed, at least one LLM provider configured.

### Option A: AI-Assisted Setup (recommended)

Open Opencode in this repository:

```bash
cd /path/to/opencode-hive
opencode
```

Then say:

> Set this up for my project at /path/to/my-project

Opencode reads the `AGENTS.md` file, discovers your available models, detects your project stack, and installs everything with the right model assignments. See [AGENTS.md](AGENTS.md) for the full setup protocol.

### Option B: Manual Setup

```bash
# 1. Copy global files
cp -r global/agents/ ~/.config/opencode/agents/
cp -r global/tools/ ~/.config/opencode/tools/
cp -r global/scripts/ ~/.config/opencode/scripts/
cp -r global/rules/ ~/.config/opencode/rules/
cp -r global/skills/ ~/.config/opencode/skills/
cp global/opencode.json ~/.config/opencode/opencode.json

# 2. Copy project files into your target project
cp -r project/agents/ /path/to/my-project/.opencode/agents/
cp -r project/rules/ /path/to/my-project/.opencode/rules/
cp -r project/wiki/ /path/to/my-project/.opencode/wiki/
cp project/.gitignore /path/to/my-project/.opencode/.gitignore

# 3. Replace model placeholders in all .md and .json files
# See "Model Selection" below for choosing models
```

## Model Selection

Run `opencode models` to see every model available from your configured providers. Assign each to a cost tier:

| Tier | Cost | Used By | Example Assignment |
|------|------|---------|-------------------|
| **SUB** | Subscription, no per-token cost | orchestrator, plan, review-lead, ops-specialist, wiki-curator | Models included with your provider subscription |
| **MID** | Subscription or pay-per-token | python-pro, project-dev, frontend-dev | Your strongest coding model |
| **PREMIUM** | Frontier pricing | Manual override only | Best available models, used sparingly |

Replace these placeholders in agent files and `opencode.json`:

| Placeholder | Tier | Role |
|---|---|---|
| `YOUR_FREE_ROUTING_MODEL` | SUB | Orchestrator routing decisions |
| `YOUR_FREE_STRONG_MODEL` | SUB | Planning, review, wiki curation |
| `YOUR_FREE_FAST_MODEL` | SUB | Quick summaries, small model tasks |
| `YOUR_PAID_CODEX_MODEL` | MID | Code generation and variant config in opencode.json |

Some agents use **reasoning variants** (e.g., `YOUR_PAID_CODEX_MODEL:high`). These configure the model to spend more compute on reasoning before responding. The `:high` variant is the default for coding tasks; `:xhigh` is available for the hardest problems. See [docs/model-selection.md](docs/model-selection.md) for a detailed guide.

The config also includes tuned **compaction settings** (`reserved: 24000`) that trigger context compression earlier than default — important for models like GLM/ZhipuAI that degrade before their nominal context limit. Provider **timeout settings** (`timeout: 600000`, `chunkTimeout: 45000`) handle slow providers and extended reasoning. See [docs/model-selection.md](docs/model-selection.md#compaction--context-tuning) for tuning guidance.

## Agents

### Primary Agents (Tab cycle)

| Agent | Model Tier | Role |
|---|---|---|
| **plan** | SUB | Read-only investigation and structured planning. Never modifies files. |
| **orchestrator** | SUB | Routes tasks to specialists. Reads code but delegates all implementation. |

### Global Subagents (installed in `~/.config/opencode/agents/`)

| Agent | Model Tier | Role |
|---|---|---|
| **python-pro** | PAID | Expert Python 3.12+ developer. Types, tests, modern patterns. |
| **ops-specialist** | SUB | Linux systems, systemd, deployment, logs, infrastructure. |
| **wiki-curator** | SUB | Maintains the project wiki. Bootstrap, ingest, query, lint. |

### Project Subagents (installed in `.opencode/agents/`)

| Agent | Model Tier | Role |
|---|---|---|
| **review-lead** | SUB | Multi-lens code review coordinator. Routes diffs to domain specialists. |
| **[project]-dev** | PAID | Your project specialist. Created from `_project-dev-template.md`. |

### Example Specialists (in `examples/specialists/`)

| Agent | Model Tier | Role |
|---|---|---|
| **frontend-dev** | PAID | React/Vue/Svelte, TypeScript, CSS, accessibility. |
| **backend-dev** | PAID | API design, business logic, security. Language-agnostic. |
| **database-dev** | PAID | Schema design, migrations, query optimization, indexing. |
| **devops-engineer** | PAID | Docker, Kubernetes, Terraform, CI/CD, observability. |

Copy the ones matching your stack into `~/.config/opencode/agents/` and add them to the orchestrator's `permission.task` allow list.

## Custom Tools and Scripts

Tools appear as native LLM tools in Opencode -- typed parameters, descriptions, auto-discovered from `~/.config/opencode/tools/`. Each tool wraps a Python script from `scripts/`.

| Tool | Script | Purpose |
|------|--------|---------|
| `skeleton` | `skeleton.py` | Strip method bodies from Python files. ~90% token reduction for understanding large files. |
| `impact` | `impact.py` | Find every usage of a symbol across the project. Run before renaming or refactoring. |
| `seek` | `seek.py` | Jump to the exact definition of a class or function project-wide. |
| `which_test` | `which_test.py` | Find tests that reference a given module. |
| `ghost` | `ghost.py` | Detect dead code -- functions and classes never used elsewhere. |
| `check` | `check.sh` | Run lint + format check + test suite in one command. |
| `wiki_search` | -- | Search wiki pages by content (no backing script, implemented in TypeScript). |

All Python scripts use only the standard library -- no external dependencies required. They work with any Python 3.10+ installation.

## Project Wiki (Karpathy LLM Wiki)

The project wiki is an LLM-maintained knowledge base that lives at `.opencode/wiki/` inside your project. Inspired by [Karpathy's proposal](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) for LLMs to maintain their own documentation, it accumulates understanding of your project over time.

### How It Works

1. **Bootstrap**: On first use, the wiki-curator scans your project and creates initial pages covering architecture, major modules, and conventions.
2. **Ingest**: After significant changes (PRs, new features, refactors), feed the source material to the wiki-curator. It extracts knowledge and updates relevant pages.
3. **Query**: Any agent can read the wiki before diving into source code. This saves tokens -- the wiki provides pre-distilled understanding.
4. **Lint**: Periodic health checks catch stale pages, broken cross-references, and gaps in coverage.

### Directory Structure

```
.opencode/wiki/
  index.md            # Table of contents with links to all pages
  log.md              # Changelog of wiki updates
  WIKI_SCHEMA.md      # Page templates and naming conventions
  entities/           # Module and service pages
  concepts/           # Patterns, domain terms, glossary
  architecture/       # System design and decisions
  sessions/           # Valuable query results filed as knowledge
```

### Skills

Two skills provide convenient entry points:
- **wiki-ingest**: "Add this PR to the wiki" -- delegates to wiki-curator's ingest operation
- **wiki-lint**: "Check the wiki health" -- delegates to wiki-curator's lint operation

See [docs/wiki-system.md](docs/wiki-system.md) for the full guide.

## Customization

### Add a Specialist

1. Copy a template from `examples/specialists/` or create a new `.md` file
2. Set the frontmatter: name, description, mode (`subagent`), model, tools, permissions
3. Place in `~/.config/opencode/agents/` (global) or `.opencode/agents/` (project-specific)
4. Add the agent name to orchestrator.md's `permission.task` section
5. Optionally add to review-lead.md's task permissions and domain routing table

See [docs/adding-specialists.md](docs/adding-specialists.md) for a detailed walkthrough.

### Create a Project Agent

1. Copy `project/agents/_project-dev-template.md`
2. Fill in: project name, layout, conventions, dev commands, key files
3. Save as `.opencode/agents/<project-name>-dev.md` in your target project
4. Add to orchestrator and review-lead permissions

### Add Rules

Create `.opencode/rules/my-rule.md` in your project. Rules are loaded into every session via the `instructions` config. Keep each rule file under 50 lines.

### Adjust Models

Change the `model` field in any agent's frontmatter. Use the format `model-id` for default settings or `model-id:variant` for reasoning variants (e.g., `model-id:high`).

## Example Workflows

### Plan a Feature

Switch to the **plan** agent (Tab cycle). Describe the feature. The plan agent investigates the codebase -- reading files, tracing call chains, checking tests -- and produces a structured implementation plan with specific file paths, risks, and specialist routing.

### Implement a Feature

Switch to the **orchestrator**. Paste the plan or describe the task. The orchestrator routes to the appropriate specialist(s), providing them with specific file paths and success criteria. For cross-cutting changes, multiple specialists run in parallel.

### Review Changes

Invoke the **review-lead** (via `@review-lead` or through the orchestrator). It analyzes the diff, categorizes changed files by domain, and dispatches specialists in parallel. Results are synthesized into one report with severity levels and a verdict.

### Maintain the Wiki

On first use: "Bootstrap the wiki for this project." The wiki-curator scans the project and creates initial pages. After PRs or major changes: "Ingest this PR into the wiki." Periodically: "Lint the wiki" to catch staleness and broken references.

## Troubleshooting

**Agent not in Tab cycle** -- Check that the agent's frontmatter has `mode: primary`. Subagents (`mode: subagent`) are hidden and invoked via the Task tool.

**Subagent can't be invoked** -- Check the calling agent's `permission.task` section. Agent names must match exactly. The orchestrator's task permissions are the most common place to add new specialists.

**Model not found** -- Run `opencode models` to verify the model ID exists and is available from your configured providers. Check for typos in the `model` field.

**Wiki not bootstrapping** -- Ensure `.opencode/wiki/` directory exists (even if empty). The wiki-curator checks for this directory to determine if it should bootstrap.

**Tools not appearing** -- Tool `.ts` files must be in `~/.config/opencode/tools/`. Verify with `ls ~/.config/opencode/tools/`. Opencode auto-discovers tools on startup.

**Scripts not found by tools** -- Tools look for scripts in two locations: `<project>/scripts/` first, then `~/.config/opencode/scripts/`. Ensure scripts are in at least one location and are executable.

## References

- [Opencode Documentation](https://opencode.ai/docs/)
- [Opencode Agents](https://opencode.ai/docs/agents/)
- [Opencode Custom Tools](https://opencode.ai/docs/custom-tools)
- [Opencode Models & Variants](https://opencode.ai/docs/models/)
- [Opencode Configuration](https://opencode.ai/docs/configuration/)
- [Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## License

MIT -- see [LICENSE](LICENSE).
