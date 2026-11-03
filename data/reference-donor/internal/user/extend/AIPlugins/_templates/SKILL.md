---
name: my-skill
description: One line: what this skill does and when to use it; the model matches requests against it.
runtime: both        # sqai | claude-code | both
---

# My skill

A skill is loaded on demand (`load_skill`) when the task matches `description`. The body is
the steps, the tools and the gotchas.

## Steps

1. First do X with the built-in tools (`list_projects`, `read_file`, `write_file`,
   `set_task_config`, `open_project`, ...); in Claude Code Bash/Edit/WebFetch are available
   too. Do not build skills around `invoke_ui_action`/`invoke_ui_flow`: UI control is locked
   until the user types `/drive-ui`; only navigation refs work without it.
2. Then do Y.
3. Report the result.

`runtime: sqai` when the steps only use in-app tools; `claude-code` when they need a terminal
(shell, git, subagents); `both` if either works. SQAI offers only `both`/`sqai` skills; the
terminal sees all.
