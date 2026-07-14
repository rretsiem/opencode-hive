# OpenCode Hive

A multi-agent architecture for [OpenCode](https://opencode.ai) with cost-optimized model routing, parallel specialist execution, and a self-maintaining project wiki.

## Why This Exists

OpenCode has powerful features — subagents, custom tools, per-agent permissions, skill files, model variants — that I haven't seen used much in practice. Most setups are a single agent with one model. That works, but it leaves a lot on the table.

I built this to use OpenCode seriously without assigning the most expensive model to every task. Subscription models can handle routing, planning, review, and code generation; usage-based or local models can be mixed in where they provide better quality or economics. The template uses role-based placeholders so it is not coupled to the providers or models I happened to use when it was created.

This is my configuration as a starting point. I write Python, so the included specialist is `python-pro`. For other languages, swap it for a specialist that matches your stack — see `examples/specialists/` for frontend, backend, database, and devops templates. Fork it, adjust it, make it yours.

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
  |-- traces impact             +-- python-pro     (CODE model)
  |-- never modifies files      +-- ops-specialist  (SUB model)
                                +-- wiki-curator    (SUB model)
                                +-- [your specialists]

Project-level subagents (installed per-project):

  review-lead                   your-project-dev
  (SUB model, read-only)       (CODE model, full access)
  |                             |
  +-- routes diffs to           +-- knows your project's
      domain specialists            architecture & conventions
```

**Primary agents** appear in the Tab cycle -- the user switches between them directly. The `plan` agent investigates and plans; the `orchestrator` executes by delegating to specialists.

**Subagents** are hidden from the Tab cycle and invoked by primary agents via the Task tool. They do the actual work: writing code, reviewing diffs, maintaining the wiki.

**Smart routing**: The orchestrator reads the request, determines which specialist(s) are needed, and fans out in parallel. A Python refactor goes to `python-pro`. A deployment question goes to `ops-specialist`. A cross-cutting feature fans out to multiple specialists simultaneously.

## Quick Start

**Prerequisites**: [OpenCode](https://opencode.ai) installed, at least one LLM provider configured.

### Option A: AI-Assisted Setup (recommended)

Open OpenCode in this repository:

```bash
cd /path/to/opencode-hive
opencode
```

Then say:

> Set this up for my project at /path/to/my-project

OpenCode reads the `AGENTS.md` file, discovers your available models, detects your project stack, and installs everything with the right model assignments. See [AGENTS.md](AGENTS.md) for the full setup protocol.

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

# 4. Add stack-specific implementation/reviewer pairs, then edit the
# project-local orchestrator.md and review-lead.md allow lists

# 5. Verify the installed template
python3 scripts/validate-template.py
```

## Model Selection

Run `opencode models` to see every model available from your configured providers. Assign each to a cost tier:

| Tier | Cost | Used By | Example Assignment |
|------|------|---------|-------------------|
| **SUB** | Subscription, no per-token cost | orchestrator, plan, review-lead, reviewers, ops-specialist, wiki-curator | Models included with your provider subscription |
| **MID** | Subscription or pay-per-token | python-pro, project-dev, frontend-dev | Your strongest coding model |
| **PREMIUM** | Frontier pricing | Manual override only | Best available models, used sparingly |

Replace these placeholders in agent files and `opencode.json`:

| Placeholder | Tier | Role |
|---|---|---|
| `YOUR_ROUTING_MODEL` | SUB | Orchestrator routing decisions |
| `YOUR_ANALYSIS_MODEL` | SUB | Planning, review, wiki curation |
| `YOUR_FAST_MODEL` | SUB | Titles and other lightweight tasks |
| `YOUR_CODE_MODEL` | MID | Code generation and editing |

Reasoning controls are provider-specific model options, not part of these model IDs. Add `reasoningEffort`, `thinking`, or a built-in variant only after selecting a model that supports it. See [docs/model-selection.md](docs/model-selection.md) for details.

The config includes conservative **compaction settings** (`reserved: 24000`). Treat them as starting points and tune them for the context window of the models you select. Provider-specific timeout examples are covered in [docs/model-selection.md](docs/model-selection.md#provider-timeout-settings).

## Agents

### Primary Agents (Tab cycle)

| Agent | Model Tier | Role |
|---|---|---|
| **plan** | SUB | Read-only investigation and structured planning. Never modifies files. |
| **orchestrator** | SUB | Routes tasks to specialists. Reads code but delegates all implementation. |

### Global Subagents (installed in `~/.config/opencode/agents/`)

| Agent | Model Tier | Role |
|---|---|---|
| **python-pro** | MID | Expert Python 3.12+ developer. Types, tests, modern patterns. |
| **python-reviewer** | SUB | Read-only Python correctness and test review. |
| **ops-specialist** | SUB | Linux systems, systemd, deployment, logs, infrastructure. |
| **ops-reviewer** | SUB | Read-only operational and deployment review. |
| **wiki-curator** | SUB | Maintains the project wiki. Bootstrap, ingest, query, lint. |

### Project Subagents (installed in `.opencode/agents/`)

| Agent | Model Tier | Role |
|---|---|---|
| **review-lead** | SUB | Multi-lens code review coordinator. Routes diffs only to read-only reviewers. |
| **orchestrator** | SUB | Project-local router override and task allow list. |
| **[project]-dev** | MID | Your project specialist. Created from `_project-dev-template.md`. |

### Example Specialists (in `examples/specialists/`)

| Domain | Implementation agent | Read-only reviewer |
|---|---|---|
| Frontend | `frontend-dev` | `frontend-reviewer` |
| Backend | `backend-dev` | `backend-reviewer` |
| Database | `database-dev` | `database-reviewer` |
| DevOps | `devops-engineer` | `devops-reviewer` |

Copy both files for each domain you use. Add implementation agents to the
project-local orchestrator's `permission.task` allow list and reviewer agents
to `review-lead`'s allow list. Review workflows never delegate to edit-capable
implementation agents.

The orchestrator can also use OpenCode's built-in `explore` agent for fast,
read-only code discovery and `scout` for external documentation or dependency
source research.

## Custom Tools and Scripts

Tools appear as native LLM tools in OpenCode -- typed parameters, descriptions, auto-discovered from `~/.config/opencode/tools/`. Each tool wraps a Python script from `scripts/`.

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
2. Set the frontmatter: description, mode (`subagent`), model, and permissions. The filename is the agent name; use `permission` rather than the deprecated boolean `tools` config.
3. Place in `~/.config/opencode/agents/` (global) or `.opencode/agents/` (project-specific)
4. Add the implementation agent to `.opencode/agents/orchestrator.md`
5. Create or copy a separate read-only reviewer and add only that reviewer to `review-lead.md`

See [docs/adding-specialists.md](docs/adding-specialists.md) for a detailed walkthrough.

### Create a Project Agent

1. Copy `project/agents/_project-dev-template.md`
2. Fill in: project name, layout, conventions, dev commands, key files
3. Save as `.opencode/agents/<project-name>-dev.md` in your target project
4. Add it to the project-local orchestrator. If it needs review coverage, create a separate read-only reviewer for `review-lead`.

### Add Rules

Create `.opencode/rules/my-rule.md` in your project. Rules are loaded into every session via the `instructions` config. Keep each rule file under 50 lines.

### Adjust Models

Change the `model` field in any agent's frontmatter using the format `provider/model-id`. For supported reasoning models, set the provider option separately (for example, `reasoningEffort: high`).

## Example Workflows

### Plan a Feature

Switch to the **plan** agent (Tab cycle). Describe the feature. The plan agent investigates the codebase -- reading files, tracing call chains, checking tests -- and produces a structured implementation plan with specific file paths, risks, and specialist routing.

### Implement a Feature

Switch to the **orchestrator**. Paste the plan or describe the task. The orchestrator routes to the appropriate specialist(s), providing them with specific file paths and success criteria. For cross-cutting changes, multiple specialists run in parallel.

### Review Changes

Invoke the **review-lead** (via `@review-lead` or through the orchestrator). It analyzes the diff, categorizes changed files by domain, and dispatches read-only reviewers in parallel. Results are synthesized into one report with severity levels and a verdict; implementation agents are never used for review.

### Maintain the Wiki

On first use: "Bootstrap the wiki for this project." The wiki-curator scans the project and creates initial pages. After PRs or major changes: "Ingest this PR into the wiki." Periodically: "Lint the wiki" to catch staleness and broken references.

## Troubleshooting

**Agent not in Tab cycle** -- Check that the agent's frontmatter has `mode: primary`. Subagents (`mode: subagent`) are hidden and invoked via the Task tool.

**Subagent can't be invoked** -- Check the calling agent's `permission.task` section. Agent names must match exactly. The orchestrator's task permissions are the most common place to add new specialists.

**Project agent unavailable** -- Add project-only agents to `.opencode/agents/orchestrator.md`, not the global orchestrator. OpenCode merges the project-local definition for that project.

**Model not found** -- Run `opencode models` to verify the model ID exists and is available from your configured providers. Check for typos in the `model` field.

**Wiki not bootstrapping** -- Ensure `.opencode/wiki/` directory exists (even if empty). The wiki-curator checks for this directory to determine if it should bootstrap.

**Tools not appearing** -- Tool `.ts` files must be in `~/.config/opencode/tools/`. Verify with `ls ~/.config/opencode/tools/`. OpenCode auto-discovers tools on startup.

**Scripts not found by tools** -- Global tools execute their trusted implementations from `~/.config/opencode/scripts/`. Ensure that directory was copied during installation and its scripts are readable.

**Template validation fails** -- Run `python3 scripts/validate-template.py` from this repository with the current `opencode` executable on `PATH`. The validator reports unresolved agents, unsafe review permissions, invalid task targets, and model-placeholder drift.

## References

- [OpenCode Documentation](https://opencode.ai/docs/)
- [OpenCode Agents](https://opencode.ai/docs/agents/)
- [OpenCode Custom Tools](https://opencode.ai/docs/custom-tools)
- [OpenCode Models & Variants](https://opencode.ai/docs/models/)
- [OpenCode Configuration](https://opencode.ai/docs/config/)
- [Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## License

MIT -- see [LICENSE](LICENSE).
