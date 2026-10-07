# Implementation plan: [Task / Feature Title]

Iteration: <n></n>. Status: PROPOSED | APPROVED | SUPERSEDED.
Date, source HEAD/fingerprint, working-tree status, owner approval reference:
<record evidence; do not infer approval>

## 1. Objective and acceptance boundary

- Goal: [Concise description of what is being built or fixed]
- Context / Problem Solved: [Why this change is needed based on codebase exploration]

## 2. Research, authority and implementation donors

- [Actual code/docs/tests/dependencies, conflicts, commands and known gaps]

## 3. File Changes (ALLOWED_WRITE_PATHS)

- Modify: path/to/existing_file.ext
  - [Brief note on what function/logic changes and the affected classes/methods (created/edited)]
- Create: path/to/new_file.ext
  - [Brief note on purpose of the new file and list the classes/methods to be created]
- Delete / Deprecate: path/to/old_file.ext (if applicable)

## 4. Step-by-Step Task Breakdown

- [ ] Step 1: [Setup dependencies, configuration, or core interfaces]
- [ ] Step 2: [Implement primary business logic or component]
- [ ] Step 3: [Wire up routes, UI, or event handlers]
- [ ] Step 4: [Write unit/integration tests]

## 5. Verification & Testing

- Automated Tests: [Commands or test suites to run, e.g., npm test / pytest]
- Automated Usage examples: [Commands for scripts (if applicable)]
- Manual / Browser Verification: [UI checks, expected visual states, or headless browser test steps (if applicable)]

## 6. Risks and Resetting

- [Residual risks introduced by this task (if any)]
- [Logical needed follow-up plans (if any)]
- [How to undo changes and reset this task back to pre-implementation stage]

## 7. Walkthrough and owner gates

- [Output location (if any)]
- [Proposed commit subject, plan approval and separate commit gate]

**IMPORTANT NOTES _(for agents only_):**

- Stop before unapproved implementation; Wait for exactly "APPROVED: EXECUTE" with nothing else.
Any extra text means adjusting the plan first or addressing that issue first.
- Only one "APPROVED: EXECUTE" for what is listed in this task only do not treat historical approval as current.
Any blockers during implementation will need their own "APPROVED: EXECUTE" after updating the implementation plan.
- If its a follow up task of the same Implementation, no need to create a implementation plan file, append at the end
of the same document with the 7 headings above and Iteration: 2/3/4 etc.
- No essays, everything should be brief and straight to the point.
