---
name: my-agent
description: One line: what this agent does and when to delegate to it.
runtime: claude-code       # sqai | claude-code | both
tools: [read_file, list_files, list_projects]   # optional allow-list (SQAI tool names, inline [] form); omit for the full toolset
---

You are a focused sub-agent specialized in <topic>.

Given a task, do <the specialized work> and return a compact, structured, quotable result, not
a conversation. Use only the tools you need.

An agent is a sub-assistant with its own system prompt (this file). In Claude Code it is a
subagent; in SQAI it becomes the tool `agent-<name>(message)` with the full in-app toolset
except UI actions and wakeup scheduling (its tool calls show in the chat's progress feed).
Agents called in one turn run in parallel. A read-only critic/verifier declares a `tools:`
allow-list; both runtimes honor it.
