---
name: my-rule
description: One line: what standing instruction this rule enforces.
runtime: both        # sqai | claude-code | both
---

Write the standing instruction here, in the imperative, short and unambiguous.

Example: "Always answer in the user's language. When editing a strategy, never change its
symbol or timeframe without confirming first."

A rule is a standing instruction: its `description` sits in the rule index of every SQAI
prompt and the body is loaded with `load_rule(name)`; `inline: true` in the frontmatter pastes
the body into every prompt instead, so keep such a body very short.
