# Project Wiki System

An agent-maintained knowledge base for your project, inspired by [Karpathy's LLM wiki concept](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). It changes only when a user or agent explicitly invokes a wiki workflow.

## The Problem

Every new LLM session starts with zero understanding of your project. The model reads source files, builds a mental model, and then discards everything when the session ends. The next session repeats the same expensive exploration.

The wiki solves this by accumulating distilled knowledge in a structured format that persists across sessions. Instead of reading 50 source files to understand the auth module, an agent reads one wiki page that captures the key architecture, API surface, and known issues.

## Three Layers

### Layer 1: Schema (WIKI_SCHEMA.md)

Defines the page templates and naming conventions. Lives at `.opencode/wiki/WIKI_SCHEMA.md`. The wiki-curator reads this to understand how to structure new pages.

Four page types:
- **Entity pages** -- modules, services, components. Key files, public API, dependencies.
- **Concept pages** -- patterns, domain terms, glossary entries. Definition, usage, examples.
- **Architecture decisions** -- date, context, decision, alternatives, consequences.
- **Session pages** -- valuable query results filed as reusable knowledge.

### Layer 2: Content (wiki pages)

The actual knowledge, organized into subdirectories:

```
.opencode/wiki/
  index.md              # Table of contents linking all pages
  log.md                # Chronological record of wiki changes
  WIKI_SCHEMA.md        # Page templates (Layer 1)
  entities/             # Module and service pages
    auth-module.md
    api-gateway.md
  concepts/             # Patterns and domain terms
    event-sourcing.md
    retry-policy.md
  architecture/         # Design decisions and overview
    overview.md
    why-postgres.md
  sessions/             # Valuable query results filed as knowledge
    2026-03-auth-flow.md
    2026-04-rate-limiting.md
```

### Layer 3: Operations (wiki-curator agent)

The wiki-curator agent performs four operations on the wiki content:

1. **Bootstrap** -- Create the wiki from scratch by scanning the project
2. **Ingest** -- Add knowledge from a source (PR, file, conversation)
3. **Query** -- Answer questions using wiki content, updating gaps found along the way
4. **Lint** -- Health-check for staleness, broken links, and coverage gaps

## Operations in Detail

### Bootstrap

Triggered when `.opencode/wiki/index.md` doesn't exist. This works for a fresh
installation where `WIKI_SCHEMA.md` is already present. The wiki-curator:

1. Scans project structure: README, config files, directory layout
2. Reads key entrypoints and module headers
3. Creates `architecture/overview.md` with a high-level system description
4. Creates entity pages for major modules/services
5. Creates `index.md` linking all pages
6. Creates `log.md` with the bootstrap entry
7. References or creates `WIKI_SCHEMA.md`

Bootstrap is intentionally shallow -- it captures the structure and surface-level understanding. Deeper knowledge accumulates through ingest operations over time.

### Ingest

Adds knowledge from a specific source. The wiki-curator:

1. Reads the source material (code diff, PR description, document)
2. Determines which wiki pages are relevant (or creates new ones)
3. Updates content with new information
4. Adds cross-references to related pages
5. Updates `index.md` if it created new pages
6. Appends to `log.md` with date and description of changes

**Good ingest sources**:
- Pull request diffs (captures what changed and why)
- New module introductions
- Architecture decision discussions
- Refactoring results
- Bug postmortems

### Query

When asked a question about the project:

1. Searches wiki pages for relevant content
2. If the wiki has the answer, responds from wiki content (citing the page)
3. If the wiki is incomplete, reads source code to fill the gap
4. Updates the wiki with the newly discovered information

Every query that hits a gap improves the wiki for future queries.

### Lint

Periodic health check. The wiki-curator examines:

- **Orphan pages** -- Pages not linked from `index.md`
- **Broken cross-references** -- Links to pages that don't exist
- **Stale pages** -- Pages not updated for a long time relative to their source files
- **Coverage gaps** -- Source files or modules with no wiki representation
- **Contradictions** -- Information that conflicts between pages

Results are categorized by severity. The user decides which issues to fix automatically and which to flag for manual review.

## Integration with Other Agents

### Plan Agent

The plan agent checks for the wiki before investigating source code:

```
Request: "How does the auth module work?"

Without wiki:
  plan reads 8 source files -> 2000 tokens consumed

With wiki:
  plan reads wiki/entities/auth-module.md -> 200 tokens consumed
  plan reads 2 source files for details not in wiki -> 400 tokens consumed
```

### Review Lead

After reviewing a PR, the review-lead can flag wiki updates needed:

```markdown
## Wiki Impact
- Update wiki/entities/auth-module.md (new OAuth provider added)
- Create wiki/concepts/rate-limiting.md (new pattern introduced)
```

### Orchestrator

The orchestrator reads `wiki/index.md` during its discovery phase to understand project structure without scanning the filesystem.

## Skills

Two skills provide user-friendly entry points:

### wiki-ingest

Trigger phrases: "Add this to the wiki", "Ingest this PR", "Update the wiki"

The skill identifies the source, invokes the wiki-curator with the ingest operation, and reports which pages it created or updated.

### wiki-lint

Trigger phrases: "Check the wiki health", "Lint the wiki", "Are there stale pages?"

The skill invokes the wiki-curator with the lint operation and presents findings categorized by severity.

## Maintenance Tips

1. **Ingest after every significant PR.** The wiki is only as current as the last ingest. Make it a habit to "ingest this PR" after merging.

2. **Lint monthly.** Projects evolve faster than wikis. Monthly linting catches drift before it compounds.

3. **Keep entity pages short.** One screen per page is ideal. If a page grows past 100 lines, split it into sub-pages.

4. **Don't duplicate source code.** Wiki pages should reference file paths and line ranges, not copy code verbatim. Copied code goes stale immediately.

5. **Mark uncertainty.** If the wiki-curator isn't sure about something, it marks it `UNVERIFIED`. Address these during lint passes.

6. **Commit the wiki.** The `.opencode/wiki/` directory should be committed to version control. It's project documentation that benefits all contributors (human and AI).

7. **Review wiki diffs.** When the wiki-curator updates pages, review the diff before committing. The curator is good but not perfect -- catch any misunderstandings early.
