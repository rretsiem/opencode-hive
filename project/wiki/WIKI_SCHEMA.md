# Wiki Schema

This file defines conventions for the project wiki at `.opencode/wiki/`.
The wiki-curator agent reads this to understand page structure and naming.

## Page Templates

### Entity Page (modules, services, components)
- **Purpose**: One sentence
- **Key Files**: List with brief descriptions
- **Public API**: Main functions/classes others use
- **Dependencies**: What this module depends on
- **Dependents**: What depends on this module
- **Known Issues**: Current limitations or tech debt
- **Last Verified**: Date the page was confirmed against code

### Concept Page (patterns, domain terms)
- **Definition**: Clear explanation
- **Where Used**: List of entities/files using this concept
- **Examples**: Code snippets or references
- **Related Concepts**: Cross-links

### Architecture Decision
- **Date**: When decided
- **Context**: What prompted the decision
- **Decision**: What was chosen
- **Alternatives**: What was rejected and why
- **Consequences**: What this means for future work

## Naming Conventions
- Filenames: kebab-case matching the entity/concept name
- Cross-references: relative markdown links `[Name](../entities/name.md)`
- Dates in log.md: ISO-8601 format

## Freshness Rules
- Entity pages: re-verify when source files change significantly
- Architecture pages: re-verify on major refactors
- Mark stale pages: `⚠️ STALE — last verified [date]` at top of page
