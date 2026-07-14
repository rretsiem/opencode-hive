---
name: wiki-lint
description: Health-check the project wiki for stale pages, broken cross-references, contradictions, and orphan pages.
license: MIT
compatibility: opencode
metadata:
  audience: maintainers
  workflow: project-wiki
---

# Wiki Lint

## When to Use
- "Check the wiki health"
- "Lint the wiki"
- "Are there stale wiki pages?"
- After major refactors
- Monthly maintenance

## Workflow
1. Invoke the wiki-curator agent with the lint operation
2. The curator checks: orphan pages, missing from index, stale dates, broken cross-references, contradictions
3. Report findings categorized by severity
4. Ask user which issues to fix automatically vs flag for manual review
