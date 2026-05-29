# Codex Local Configuration

This directory mirrors the Claude Speckit skills from `.claude/skills/` for Codex-oriented workflows.

## What Maps From `.claude`
- `.claude/skills/*/SKILL.md` -> `.codex/skills/*/SKILL.md`
- `CLAUDE.md` project guidance -> `AGENTS.md`

## What Does Not Map Directly
`.claude/settings.local.json` stores Claude-specific command permission allowlists. Codex permissions are controlled by the active sandbox and approval settings for the running session, not by a repo-local `settings.local.json` file.

## Speckit Skills
The mirrored skills describe Speckit commands such as:
- `speckit-specify`
- `speckit-plan`
- `speckit-tasks`
- `speckit-implement`
- `speckit-analyze`
- `speckit-checklist`
- `speckit-clarify`
- `speckit-constitution`
- `speckit-taskstoissues`
- `speckit-git-*`

If your Codex client supports repo-local skills, point it at `.codex/skills`. Otherwise, install or copy these skills into your Codex skills directory.
