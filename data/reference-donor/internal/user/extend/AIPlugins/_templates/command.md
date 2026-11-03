---
name: my-command
description: One line: what this slash command does.
runtime: both              # sqai | claude-code | both
argument-hint: <project>   # shown to the user; the expected arguments
---

You are handling the `/my-command` slash command with arguments: **$ARGUMENTS**
(positional arguments: `$1`, `$2`, ...).

1. Explain the task in one line.
2. Perform it with the available tools.
3. Return a concise result.

A command is a prompt template: in SQAI the user types `/my-command <args>` and this file (with
`$ARGUMENTS` / `$1...` substituted) becomes the prompt; in Claude Code it is a native slash
command. Keep it self-contained.
