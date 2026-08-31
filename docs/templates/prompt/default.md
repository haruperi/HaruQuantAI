# Default Prompt Templates

This document is the canonical prompt-design standard for HaruQuantAI workflow prompts. It is a design standard, not a mechanically inherited runtime template. The Planner, Executor, Reviewer, and Reviewer close-out prompts in this directory use the MAIN structure by default because workflow handoffs are high-stakes, self-documenting deliverables.

## Prompt schema version

Current prompt schema version: `1`.

## 1. The MAIN

```markdown
# PROMPT

## 1. Role
Act as a [specific expert/professional role] with experience in [specific domain, audience, or problem type].
Your perspective should be: [Practical, analytical, customer-focused, technical, commercial, etc.]

## 2. Context
Background: [What is happening]
Project/topic: [What this is about]
Audience: [Who the output is for]
Overarching goal: [Business/project objective]
Current state: [What already exists or has been tried]
Known limitations: [Budget, time, technical constraints, regulatory issues, etc.]
Provided materials: [Files, links, notes, data, examples]

Use provided materials and repository/tool evidence explicitly authorized by the task. Clearly separate verified evidence, assumptions, and recommendations.

## 3. Instruction / Task
Your task is to: [Exactly what you want created, analysed, or solved]
Why this task matters: [What this specific deliverable enables]
Success looks like: [Describe the ideal outcome, deliverable, decision, or result]

Functional requirements:
- [Requirement]

Non-functional requirements:
- [Requirement]

## 4. Specification
Length: [Word count, number of options, level of detail]
Tone/style: [Professional, direct, simple, technical, persuasive, etc.]

Must include:
- [Required element]
- [Required element]

Avoid:
- [Unwanted content, tone, or structure]
- [Unwanted assumptions]

Rules:
- Do not write implementation code unless requested.
- Interactive task: if critical information is genuinely missing, ask.
- Orchestrated/headless task: do not wait conversationally; record the missing information and use the workflow's `BLOCKED` handoff.
- Correct your own output when it fails this prompt, but never cross the role authority defined in §5.

## 5. Authority and Boundaries
Allowed actions/writes: [Explicit authority]
Forbidden actions/writes: [Explicit boundaries]
Failure behavior: [How to stop safely]
Handoff authority: [What the role may populate for the next role]
Protected incoming-role rules: [What must never be weakened or rewritten]

## 6. Reasoning Guidance
Before giving the final answer, internally consider:
1. What is the real goal?
2. What information matters most?
3. What constraints must be respected?
4. What is the cleanest structure for the answer?
5. What risks, gaps, assumptions, or improvements should be mentioned?

Do not output private chain-of-thought. Provide concise conclusions, evidence, decisions, assumptions, risks, and verification results sufficient to audit the work.

## 7. Performance / Quality Criteria
The response is successful only if it:
- Solves the actual task directly
- Is specific, practical, and immediately usable
- Avoids vague advice, filler, and unsupported claims
- Separates confirmed information from assumptions and recommendations
- Follows the requested format exactly

The answer should be rejected (and self-corrected within role authority) if it:
- Is generic or bloated
- Ignores constraints or adds irrelevant sections
- Requires heavy rewriting before use
- Makes unsupported claims

## 8. Output Format
Return the answer using this exact structure:
1. [Section name]
2. [Section name]
3. [Section name]

[Or specify alternative: Markdown table / JSON / bullets / report / email / checklist]

## 9. Examples
Use the following examples as style, tone, structure, and quality guidance when examples materially improve control. Otherwise write `Not Applicable` rather than adding token-heavy examples that could anchor the role unnecessarily.

Example input:
[Insert example input]

Ideal output:
[Insert ideal response]

Why this output is good:
- [Specific quality to replicate]
- [Specific quality to replicate]

## 10. Final Quality Check
Before finalising, verify the answer against every criterion in §7 and the role authority in §5.
```

---

# 2. The MINIMAL

```markdown
# PROMPT

## Role
Act as [role] with expertise in [domain].

## Context
[Background, situation, audience, goal, current state, limitations, materials]

## Instruction
Your task is to [task].
Purpose: [why this matters]
Success looks like: [desired result]

## Specification
Format: [format]
Length: [length]
Tone: [tone]
Must include: [requirements]
Avoid: [restrictions]

If critical information is missing in an interactive task, ask. In a headless/orchestrated task, record the blocker and stop safely.

## Authority
Allowed: [actions/writes]
Forbidden: [actions/writes]

## Performance
The answer must be specific, accurate, actionable, well-structured, and free of unsupported claims.
It should be rejected (self-corrected within role authority) if it is vague, bloated, off-task, or ignores constraints.

## Example
Input: [Example input]
Output: [Example output]
```

---

## When to use which

- **MINIMAL** — iteration, exploration, quick turnarounds.
- **MAIN** — one-shot, high-stakes deliverables where a wrong output costs a full round-trip, or when handing the template to someone else (it is self-documenting).

A practical habit: draft with MINIMAL for most tasks, only promote to MAIN when the task turns out to need the extra control. The core Planner/Executor/Reviewer workflow uses MAIN by default.
