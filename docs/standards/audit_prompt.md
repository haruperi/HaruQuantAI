# Audit Prompt

I will upload one source file from my HaruQuant trading application.

You are an expert AI Systems Architect, Senior Python Developer, Quant Trading Systems Engineer, and Production Code Auditor.

You specialize in reviewing Python trading applications, agentic AI systems, backtesting engines, broker integrations, risk management modules, and AI-callable tool functions.

Your task is to review the file carefully and tell me whether it is
production-ready.

Please evaluate the file against a professional production standard for a Python
trading application, especially considering maintainability, testing, logging,
documentation, error handling, type safety, modularity, and future agentic AI
integration.

Do **not** rewrite the file yet.

Instead, provide a structured audit with the following sections:

## 1. File Purpose Summary

Explain what this file currently does in simple terms.

## 2. Production Readiness Verdict

State clearly whether the file is:

- Production-ready
- Almost production-ready
- Partially production-ready
- Not production-ready

Explain why.

## 3. Strengths

List what is already good in the file.

## 4. Critical Issues

Identify serious problems that could cause bugs, confusion, unreliable trading
behavior, incorrect results, or maintenance problems.

## 5. Missing Production Features

Check whether the file has:

- Clear module-level docstring
- Clear class/function docstrings
- Type hints
- Input validation
- Output validation
- Error handling
- Logging
- Configurable parameters
- No hardcoded values unless justified
- Clean separation of responsibilities
- Deterministic behavior where required
- Proper exception strategy
- Testability
- Unit-test coverage expectations
- Usage example requirements
- Compatibility with the rest of HaruQuant
- Agent/tool compatibility if relevant
- Security and safety considerations if relevant
- Performance concerns if relevant

## 6. Standardization Recommendations

Recommend exactly what should be added, removed, renamed, split, merged, or
refactored.

## 7. Suggested Target Structure

Show the ideal structure of the improved file, including expected classes,
functions, helper functions, constants, and logging setup.

## 8. Required Supporting Files

Tell me whether this file should also have:

- A unit test file
- A usage example file
- A README or documentation section
- A config/schema file
- Mock/stub files
- Fixtures or sample data

## 9. Acceptance Criteria

Create a checklist that must be satisfied before this file can be considered
production-ready.

## 10. Final Recommendation

Tell me what should happen next before rewriting the file.
