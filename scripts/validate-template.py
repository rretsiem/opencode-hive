#!/usr/bin/env python3
"""Validate the Hive template against the installed OpenCode release."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDERS = {
    "YOUR_ROUTING_MODEL",
    "YOUR_ANALYSIS_MODEL",
    "YOUR_FAST_MODEL",
    "YOUR_CODE_MODEL",
}
BUILTIN_SUBAGENTS = {"general", "explore", "scout"}
HIVE_AGENTS = {
    "orchestrator",
    "plan",
    "go-pro",
    "python-pro",
    "python-reviewer",
    "ops-specialist",
    "ops-reviewer",
    "wiki-curator",
    "review-lead",
    "_project-dev-template",
}
REQUIRED_INSTALLED_AGENTS = HIVE_AGENTS - {"_project-dev-template"}
EXPLICIT_PERMISSIONS = {
    "edit",
    "task",
    "skill",
    "webfetch",
    "websearch",
    "external_directory",
    "question",
    "doom_loop",
    "lsp",
}


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def copy_template(home: Path, project: Path) -> None:
    config = home / ".config" / "opencode"
    shutil.copytree(ROOT / "global", config)
    destination = project / ".opencode"
    shutil.copytree(ROOT / "project", destination)


def validate_examples(home: Path, project: Path) -> None:
    destination = home / ".config" / "opencode" / "agents"
    for example in sorted((ROOT / "examples").glob("**/*.md")):
        installed = destination / example.name
        shutil.copy2(example, installed)
        try:
            config = resolved_config(home, project)
            agents = config.get("agent", {})
            if not isinstance(agents, dict) or example.stem not in agents:
                fail(f"example agent {example} was not discovered")
            validate_agents(config)
        finally:
            installed.unlink(missing_ok=True)


def resolved_config(home: Path, project: Path) -> dict[str, object]:
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    # OpenCode follows the XDG base-directory variables when they are set.
    # Override them together with HOME so validation cannot accidentally read
    # the runner's real configuration instead of the temporary Hive install.
    environment["XDG_CONFIG_HOME"] = str(home / ".config")
    environment["XDG_DATA_HOME"] = str(home / ".local" / "share")
    environment["XDG_CACHE_HOME"] = str(home / ".cache")
    environment["XDG_STATE_HOME"] = str(home / ".local" / "state")
    result = subprocess.run(
        ["opencode", "debug", "config"],
        cwd=project,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        fail(f"opencode debug config exited {result.returncode}: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        fail(f"OpenCode returned invalid configuration JSON: {error}")


def validate_placeholders() -> None:
    discovered: set[str] = set()
    for directory in ("global", "project", "examples", "docs"):
        for path in (ROOT / directory).rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json"}:
                continue
            discovered.update(re.findall(r"YOUR_[A-Z_]+MODEL", path.read_text()))
    unknown = discovered - PLACEHOLDERS
    if unknown:
        fail(f"unknown model placeholders: {sorted(unknown)}")
    missing = PLACEHOLDERS - discovered
    if missing:
        fail(f"unused model placeholders: {sorted(missing)}")


def validate_agents(config: dict[str, object], *, installed: bool = False) -> None:
    agents = config.get("agent")
    if not isinstance(agents, dict):
        fail("resolved config contains no agents")
    default = config.get("default_agent")
    resolved_default = agents.get(default) if isinstance(default, str) else None
    default_mode = resolved_default.get("mode") if isinstance(resolved_default, dict) else None
    if default_mode != "primary":
        fail(
            "default_agent does not resolve to a primary agent "
            f"(default={default!r}, mode={default_mode!r}, "
            f"available={sorted(agents)})"
        )

    available = set(agents) | BUILTIN_SUBAGENTS
    if installed:
        missing_hive = REQUIRED_INSTALLED_AGENTS - set(agents)
        if missing_hive:
            fail(f"installed configuration is missing Hive agents: {sorted(missing_hive)}")

    for name, value in agents.items():
        if not isinstance(value, dict):
            fail(f"agent {name} did not resolve to an object")
        if installed and name not in HIVE_AGENTS:
            continue
        if value.get("hidden") and value.get("mode") != "subagent":
            fail(f"hidden agent {name} is not a subagent")
        permission = value.get("permission", {})
        if not isinstance(permission, dict):
            fail(f"agent {name} has no explicit permission map")
        absent = EXPLICIT_PERMISSIONS - set(permission)
        if absent:
            fail(f"agent {name} omits explicit permissions: {sorted(absent)}")
        task = permission.get("task")
        if isinstance(task, dict):
            missing = {
                target
                for target, action in task.items()
                if target != "*" and action != "deny" and target not in available
            }
            if missing:
                fail(f"agent {name} allows missing task targets: {sorted(missing)}")

        if name.endswith("reviewer") and permission.get("edit") != "deny":
            fail(f"reviewer {name} must deny edits")

    for name in ("orchestrator", "plan", "review-lead"):
        agent = agents.get(name)
        if isinstance(agent, dict) and agent.get("permission", {}).get("edit") != "deny":
            fail(f"read-only agent {name} must deny edits")

    curator = agents.get("wiki-curator", {})
    edit = curator.get("permission", {}).get("edit") if isinstance(curator, dict) else None
    if edit != {"*": "deny", ".opencode/wiki/**": "allow"}:
        fail("wiki-curator edit permission is not restricted to .opencode/wiki/**")

    orchestrator = agents.get("orchestrator", {})
    routing = orchestrator.get("permission", {}).get("task", {})
    if not isinstance(routing, dict) or any(routing.get(name) != "allow" for name in ("explore", "scout")):
        fail("orchestrator must allow built-in explore and scout")

    review_lead = agents.get("review-lead", {})
    review_tasks = review_lead.get("permission", {}).get("task", {})
    if isinstance(review_tasks, dict):
        unsafe = {
            name
            for name, action in review_tasks.items()
            if name != "*" and action != "deny" and not name.endswith("reviewer")
        }
        if unsafe:
            fail(f"review-lead can invoke edit-capable agents: {sorted(unsafe)}")


def contains_placeholder(value: object) -> bool:
    if isinstance(value, str):
        return bool(re.search(r"YOUR_[A-Z_]+MODEL", value))
    if isinstance(value, dict):
        return any(contains_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_placeholder(item) for item in value)
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        help="Validate the Hive installation resolved for an existing project",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if shutil.which("opencode") is None:
        fail("opencode is not installed")
    if args.target:
        target = args.target.expanduser().resolve()
        if not target.is_dir():
            fail(f"target project does not exist: {target}")
        config = resolved_config(Path.home(), target)
        if contains_placeholder(config):
            fail("installed configuration still contains model placeholders")
        validate_agents(config, installed=True)
        print(f"OpenCode Hive installation validation passed: {target}")
        return
    validate_placeholders()
    with tempfile.TemporaryDirectory(prefix="opencode-hive-") as temporary:
        base = Path(temporary)
        home = base / "home"
        project = base / "project"
        home.mkdir()
        project.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        copy_template(home, project)
        validate_agents(resolved_config(home, project))
        validate_examples(home, project)
    print("OpenCode Hive template validation passed")


if __name__ == "__main__":
    main()
