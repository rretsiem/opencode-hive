# Template Validation

The repository includes a compatibility check for the current OpenCode release:

```bash
python3 scripts/validate-template.py
```

The validator creates disposable global and project installations, runs
`opencode debug config`, and inspects the resolved configuration. It does not
write to your real OpenCode configuration.

It checks that:

- all Markdown agent frontmatter is accepted by OpenCode;
- `default_agent` resolves to a primary agent;
- hidden agents are subagents;
- allowed Task targets exist, including built-in `explore` and `scout`;
- primary planning and orchestration agents cannot edit;
- `wiki-curator` can edit only `.opencode/wiki/**`;
- only the four documented model placeholders appear.

## Continuous Integration

`.github/workflows/validate.yml` installs the latest published `opencode-ai`
package and runs the validator on every push and pull request. Tracking the
latest release is intentional: this repository is a template, so the check
should expose upstream schema or behavior changes quickly.

If a new OpenCode release breaks validation, reproduce locally with the latest
CLI, inspect `opencode debug config`, and update the template and documentation
together.
