# Adding Specialist Agents

How to create new specialist agents and integrate them with the orchestrator and review system.

## When to Add a Specialist

Add a specialist when:
- A domain appears repeatedly in your work (frontend, database, infrastructure)
- The orchestrator is giving generic responses for domain-specific tasks
- You want domain-specific review coverage (e.g., SQL review for migration files)

Don't add a specialist when:
- The work is a one-off task
- An existing specialist can handle it (python-pro covers most backend work)
- The domain is too narrow to justify a persistent agent

## Step-by-Step

### 1. Create the Agent File

Start from an example in `examples/specialists/` or create a new `.md` file. The file needs YAML frontmatter and a system prompt.

**Frontmatter template**:

```yaml
---
description: "One-line description of expertise and when to invoke"
mode: subagent
hidden: true
model: YOUR_CODE_MODEL
temperature: 0.1
steps: 20
permission:
  edit: allow
  bash:
    "*": deny
    "ls *": allow
    "cat *": allow
    "head *": allow
    "grep *": allow
    "find *": allow
    # Add domain-specific commands:
    # "npm *": allow
    # "cargo *": allow
    # "kubectl *": allow
  task: deny
  skill: deny
---
```

**Key decisions**:
- Agent name comes from the filename (`my-specialist.md` = `my-specialist` agent)
- `mode: subagent` + `hidden: true` -- keeps it out of the Tab cycle and `@` autocomplete
- `model` -- use the CODE/MID role for code generation and the SUB role for analysis-only specialists
- `steps` -- 15-20 for focused tasks, 25+ for complex multi-file work
- `temperature` -- 0.1 for code, 0.2 for creative/architectural work
- `permission` -- controls tool access. OpenCode allows most unspecified permissions, so set `edit` explicitly: `allow` for implementers and `deny` for read-only agents. Bash patterns use `"glob": permission` format.
- `task: deny` -- prevents specialists from invoking other agents (flat tree)
- `skill: deny` -- hides the Skill tool when the specialist has no skill-driven workflow

OpenCode evaluates granular rules in order and the **last matching rule wins**.
Put `"*": deny` first, followed by the narrower allow rules.

### 2. Write the System Prompt

Below the frontmatter, write the agent's system prompt. Include:

```markdown
You are a [domain] specialist. [One sentence about core expertise.]

## Expertise
- [Bullet list of specific knowledge areas]

## Working Guidelines
1. Read existing code first -- match project conventions
2. Surgical changes -- only touch what the task requires
3. Run checks after every edit: [relevant check command]
4. [Domain-specific guidelines]

## Output Format
[How to structure responses -- findings, changes, verification]
```

Keep it under 100 lines. The system prompt is loaded into context on every invocation, so verbosity wastes tokens across all calls.

### 3. Place the File

**Global specialist** (available across all projects):
```bash
cp my-specialist.md ~/.config/opencode/agents/
```

**Project specialist** (only for one project):
```bash
cp my-specialist.md /path/to/project/.opencode/agents/
```

Global agents are better for language-level specialists (frontend-dev, database-dev). Project agents are better for project-specific knowledge (my-app-dev).

### 4. Register with the Matching Orchestrator

For a global specialist, edit `~/.config/opencode/agents/orchestrator.md`. For a
project specialist, edit `<target>/.opencode/agents/orchestrator.md`. Keep
project-only names out of the global orchestrator. Add the agent to the matching
`permission.task` map:

```yaml
permission:
  task:
    "*": deny
    "python-pro": allow
    "ops-specialist": allow
    "wiki-curator": allow
    "my-specialist": allow    # <-- add here
```

Without this, the orchestrator cannot invoke the specialist.

### 5. Create and Register a Read-Only Reviewer

Never give `review-lead` access to an edit-capable implementation agent. Copy a
matching `*-reviewer.md` example or create a reviewer with `edit: deny`, a
deny-first Bash allow list, `task: deny`, and `skill: deny`.

Install the reviewer at the same scope as its implementation specialist, then
edit the target project's `.opencode/agents/review-lead.md`:

**Add to task permissions**:
```yaml
permission:
  task:
    "*": deny
    "python-reviewer": allow
    "ops-reviewer": allow
    "my-reviewer": allow    # <-- add here
```

**Add to the domain routing table** in the system prompt:
```markdown
| `src/widgets/**`, `*.widget.ts` | Widgets | my-reviewer |
```

### 6. Verify

```bash
# Check the global or project file is in place
ls ~/.config/opencode/agents/my-specialist.md
# or: ls /path/to/project/.opencode/agents/my-specialist.md

# Start opencode and test
opencode
# Ask: "What agents are available?"
# Or: "Route this task to my-specialist: [task description]"
```

## Checklist

- [ ] Agent `.md` file created with frontmatter and system prompt
- [ ] `mode: subagent` and `hidden: true` set
- [ ] `model` assigned to appropriate cost tier
- [ ] `permission.edit` explicitly matches the agent's role
- [ ] `permission.bash` follows deny-by-default
- [ ] Placed in `~/.config/opencode/agents/` (global) or `.opencode/agents/` (project)
- [ ] Added to the global or project-local orchestrator matching its installation scope
- [ ] Separate reviewer created with `edit: deny` (if participating in reviews)
- [ ] Reviewer added to review-lead's task permissions and routing table
- [ ] Tested: orchestrator can invoke the specialist

## Tips

- **Don't over-specialize.** A "React specialist" is better than separate agents for "React hooks", "React testing", and "React performance". The specialist can handle all three.
- **Match model to output type.** Analysis-only specialists can use the analysis model. Give agents that generate code the strongest suitable coding model, whether subscription or usage-based.
- **Keep bash permissions tight.** Each allowed command is an attack surface. Only allow what the specialist actually needs.
- **Start with examples.** The `examples/specialists/` directory has working templates. Modify rather than starting from scratch.
