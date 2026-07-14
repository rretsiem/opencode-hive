# OpenCode Hive

A multi-agent architecture for OpenCode.
This is a template -- not a project to develop, but a system to install into other projects.

## Directory Structure

- `global/` -- Files to install at `~/.config/opencode/` (agents, tools, scripts, rules, skills)
- `project/` -- Files to install at `.opencode/` in the target project
- `examples/` -- Optional specialist agents to pick based on project stack
- `docs/` -- Guides for model selection, adding specialists, architecture

## AI Setup Instructions

When a user asks you to "set this up", "install this", or "configure my project":

### Step 1: Discover Available Models
Run `opencode models` and present the output. Ask the user:
- "Which of these providers are subscription/free (no per-token cost)?"
- "Which provider/model do you want for code generation?"

Categorize into three tiers:
- **SUB**: Subscription models -- for routing, planning, review, wiki
- **MID**: Pay-per-token coding models -- for implementation specialists
- **PREMIUM**: Frontier models -- never assign as default, manual override only

### Step 2: Detect Target Project Stack
Ask the user for the target project path, then scan it:
```bash
ls <target>/*.py <target>/*.ts <target>/*.go <target>/*.rs 2>/dev/null | head -20
ls <target>/package.json <target>/pyproject.toml <target>/go.mod <target>/Cargo.toml 2>/dev/null
ls <target>/Dockerfile <target>/docker-compose* 2>/dev/null
```

### Step 3: Install Global Files
Copy each `global/` folder to `~/.config/opencode/`:
- `agents/*.md`, `tools/*.ts`, `scripts/*`, `skills/*/`, `rules/*.md`
- Merge `opencode.json` — don't overwrite existing MCP, LSP, or plugin config

**Ask before overwriting** any existing files.

### Step 4: Replace Model Placeholders
In all copied files, replace these four placeholders with real model IDs:
- `YOUR_ROUTING_MODEL` -> fast, reliable model for routing
- `YOUR_ANALYSIS_MODEL` -> strong model for planning and review
- `YOUR_FAST_MODEL` -> inexpensive model for titles and summaries
- `YOUR_CODE_MODEL` -> strongest available code-generation model

Every replacement must be a complete OpenCode model ID in
`provider/model-id` format. These role names do not require a particular
provider or billing model.

### Step 5: Install Project Files
Copy `project/` contents to `<target>/.opencode/`:
- `project/agents/*.md` -> `<target>/.opencode/agents/`
- `project/rules/*.md` -> `<target>/.opencode/rules/`
- `project/wiki/WIKI_SCHEMA.md` -> `<target>/.opencode/wiki/WIKI_SCHEMA.md`
- `project/.gitignore` -> `<target>/.opencode/.gitignore`

### Step 6: Select Example Specialists
Based on detected stack, copy matching agents from `examples/specialists/`:
- Python -> python-pro already global
- JS/TS -> copy `frontend-dev.md` and `frontend-reviewer.md`
- Backend -> copy `backend-dev.md` and `backend-reviewer.md`
- Docker/K8s -> copy `devops-engineer.md` and `devops-reviewer.md`
- SQL -> copy `database-dev.md` and `database-reviewer.md`

Add each implementation agent to `<target>/.opencode/agents/orchestrator.md`
under `permission.task` (e.g., `"frontend-dev": allow`). Add its read-only
reviewer to `<target>/.opencode/agents/review-lead.md`. Never allow an
edit-capable implementation agent from review-lead. Do not add project-only
agents to the global orchestrator.

### Step 7: Create Project-Specific Agent
Use `project/agents/_project-dev-template.md` as starting point:
1. Scan target project structure
2. Fill in project layout, conventions, dev commands, key files
3. Save as `<target>/.opencode/agents/<project-name>-dev.md`
4. Add to the project-local orchestrator's task permissions
5. If it needs review coverage, create a separate `<project-name>-reviewer.md`
   with `edit: deny` and add only that reviewer to review-lead

### Step 8: Customize Review Lead
Edit `<target>/.opencode/agents/review-lead.md`:
- Fill in the domain routing table with actual file patterns from the project
- Allow only matching `*-reviewer` agents in `permission.task`

### Step 9: Update Project Orchestrator Permissions
Edit `<target>/.opencode/agents/orchestrator.md`:
- Keep the built-in `explore` and `scout` permissions
- Add every installed specialist to `permission.task` (e.g., `"my-specialist": allow`)
- Add every new project-specific agent the same way
- Keep the global orchestrator limited to globally installed agents
- Without these project-local permissions, the orchestrator cannot delegate to your agents

### Step 10: Verify Setup
```bash
opencode models  # Confirm model IDs resolve
ls ~/.config/opencode/agents/  # Global agents present
ls <target>/.opencode/agents/  # Project agents present
```

Report the final agent inventory with models and cost tiers.
