# Extension authoring

- Python module docstrings throughout `app/extend` must be at most 20 physical
  lines, including delimiters and blank lines.
- Use a short summary and brief bullets where helpful. No `Description:`,
  `Purpose:`, `Key Capabilities:`, `Python API Usage:`, or `CLI Usage:` sections
  are required here. This overrides the root module-docstring format only.
- Put explanations beside the relevant code.
- For indicators only, follow `blocks/indicators/template.py` for section order;
  include optional patterns only when the indicator needs them. The indicator
  template structure does not apply to other extension types.
- Logging, typing, verification, approval, and Git rules from the root
  `AGENTS.md` continue to apply.
- Apply this docstring format when creating or editing Python modules; existing
  files are not automatically migrated by this rule.
