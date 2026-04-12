---
name: wiki-ingest
description: Ingest a source into the project wiki. Point at a file, PR, or doc and the wiki-curator extracts knowledge and updates relevant pages.
---

# Wiki Ingest

## When to Use
- "Add this to the wiki"
- "Ingest this PR/file/doc into the wiki"
- "Update the wiki with these changes"
- "What did this PR change?" (ingest + query)

## Workflow
1. Identify the source to ingest (user provides file path, PR number, or topic)
2. If `.opencode/wiki/` doesn't exist, ask: "No wiki found. Bootstrap one by scanning the project?"
3. Invoke the wiki-curator agent with the ingest operation
4. Report what pages were created or updated

## Bootstrap (First Run)
If no wiki exists, the wiki-curator will:
1. Scan the project structure
2. Read key files (README, AGENTS.md, main entrypoints)
3. Create architecture/overview.md
4. Create entity pages for major modules
5. Initialize index.md and log.md
