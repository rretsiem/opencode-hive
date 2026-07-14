# Architecture

The design decisions behind this multi-agent system and why they exist.

## Design Principles

1. **Route efficiently, execute capably.** A fast model handles routing. Stronger models handle implementation. Either can come from a subscription, usage-based provider, or local runtime; the role matters more than the billing model.

2. **Flat agent tree.** One orchestrator, multiple specialists. No chains of delegation (orchestrator -> sub-orchestrator -> specialist). Deep trees lose context and multiply latency. If a task needs two domains, fan out to both specialists in parallel.

3. **Explicit least privilege.** OpenCode allows most unspecified permissions by default, so every Hive agent explicitly sets its write, shell, delegation, and skill boundaries. The plan agent cannot write files. The orchestrator cannot run arbitrary bash. Specialists get only their domain-specific commands. This prevents accidental damage from model hallucinations.

4. **Orchestrator is read-only.** The orchestrator reads code to understand routing decisions but never writes files. This separation prevents the common failure mode where a "smart" orchestrator tries to implement something itself instead of delegating to a specialist with better context and tools.

5. **Step limits are budgets.** Each agent has a `steps` limit that caps tool invocations per task. This prevents runaway agents from consuming infinite tokens. Specialists get 15-20 steps (focused tasks), the orchestrator gets 30 (needs to read + delegate + synthesize).

6. **Primary vs hidden agents.** Primary agents appear in the Tab cycle for direct user interaction. Hidden subagents are invoked programmatically via the Task tool. Users should only interact with `plan` and `orchestrator` directly.

7. **Tools are typed wrappers.** Custom tools (TypeScript files in `tools/`) provide typed parameters and descriptions that the model can reason about. The underlying scripts (Python in `scripts/`) do the actual work. This separation means scripts can be tested independently and tools provide the LLM-friendly interface.

## Inspiration

This architecture draws from Anthropic's [Building effective agents](https://www.anthropic.com/engineering/multi-agent-research-system) research, which demonstrated that multi-agent systems outperform single-agent approaches on complex tasks when:

- Each agent has a focused role with clear boundaries
- The routing agent is lightweight and cheap to run
- Specialists have domain-specific knowledge baked into their system prompts
- Parallel execution reduces wall-clock time for multi-domain tasks

The key insight is that **model intelligence matters most at the implementation layer**, not the routing layer. Routing is pattern matching ("Python code? -> python-pro"). Implementation requires deeper reasoning about code structure, edge cases, and testing. Assigning a fast model to routing and the strongest suitable model to implementation concentrates quality and compute where they matter most.

## Agent Communication

Agents communicate through the Task tool, which provides structured invocation:

```
orchestrator
  |
  |-- Task("python-pro", "Refactor the auth module: ...")
  |-- Task("ops-specialist", "Update the systemd unit: ...")
  |
  Results flow back to orchestrator
  |
  orchestrator synthesizes and responds to user
```

Each specialist receives:
- A task description from the orchestrator
- Access to the full project filesystem (within their permission bounds)
- No knowledge of other specialists running in parallel

Specialists return their results to the orchestrator, which synthesizes findings and presents a unified response to the user.

## The Wiki Layer

The project wiki (`.opencode/wiki/`) is shared memory across sessions. Without it, every new session starts from zero understanding of the project.

```
Session 1: wiki-curator bootstraps from source code
Session 2: plan agent reads wiki before investigating -> faster
Session 3: wiki-curator ingests changes from Session 2 -> wiki grows
Session N: wiki becomes primary context, source code is secondary
```

Over time, the wiki reduces the token cost of understanding the project. Instead of reading hundreds of source files, agents read a few wiki pages that distill the key knowledge. This compounds -- each session makes future sessions cheaper and faster.

## Permission Model

OpenCode defaults most unspecified permissions to `allow` (`doom_loop` and
`external_directory` default to `ask`). Hive therefore makes consequential
permissions explicit and uses deny-first allow lists for granular actions:

```yaml
permission:
  edit: allow            # Explicit for implementation agents
  bash:
    "*": deny           # Nothing allowed by default
    "git *": allow      # Explicit allow for specific commands
    "ls *": allow
    "pytest *": allow
    "systemctl *": ask  # Requires user confirmation
  task:
    "*": deny           # Can't invoke any agents by default
    "python-pro": allow # Explicit allow for specific agents
    "ops-specialist": allow
```

Three permission levels:
- **allow** -- Execute without confirmation
- **ask** -- Execute only after user confirms
- **deny** -- Block entirely

Granular rules are evaluated in order and the last matching rule wins. The
catch-all must therefore come first. Read-only agents use `edit: deny`;
`wiki-curator` uses a path-scoped edit rule that only allows
`.opencode/wiki/**`. Agents that cannot delegate or load skills explicitly set
`task: deny` and `skill: deny`, which also keeps unavailable choices out of the
model's tool descriptions.

This prevents:
- Specialists invoking other specialists (no cascading delegation)
- Read-only agents accidentally writing files
- Agents running destructive commands (rm, git push --force) without explicit permission

## File Layout

```
~/.config/opencode/              # Global (all projects)
  opencode.json                  # Model config, compaction, watcher
  agents/                        # Agent definitions
    orchestrator.md
    plan.md
    python-pro.md
    ops-specialist.md
    wiki-curator.md
  tools/                         # Typed tool wrappers (TypeScript)
    skeleton.ts
    impact.ts
    seek.ts
    which_test.ts
    ghost.ts
    check.ts
    wiki_search.ts
  scripts/                       # Tool implementations (Python)
    skeleton.py
    impact.py
    seek.py
    which_test.py
    ghost.py
    check.sh
  rules/                         # Global rules loaded every session
    token-efficiency.md
    git-workflow.md
  skills/                        # Skill definitions
    wiki-ingest/SKILL.md
    wiki-lint/SKILL.md

<project>/.opencode/             # Project-specific
  agents/
    review-lead.md
    <project>-dev.md
  rules/
    _project-conventions.md
  wiki/
    WIKI_SCHEMA.md
    index.md                     # Created by wiki-curator
    log.md                       # Created by wiki-curator
    entities/                    # Created by wiki-curator
    concepts/
    architecture/
```

## Why Not a Single Agent?

A single agent with a large system prompt can handle many tasks, but it has structural problems:

1. **Cost**: Every request pays for the full system prompt. A routing-focused orchestrator has a small prompt; specialists load their domain knowledge only when needed.

2. **Quality**: A 200-line system prompt dilutes model attention. A 50-line focused specialist prompt keeps the model on-task.

3. **Permissions**: A single agent needs all permissions (write files, run tests, execute bash, manage deployments). Splitting into specialists means each gets only what it needs.

4. **Parallelism**: A single agent processes sequentially. Multiple specialists can run in parallel for multi-domain tasks.

5. **Maintenance**: Adding a new domain means editing one large prompt. With specialists, you add a new file.
