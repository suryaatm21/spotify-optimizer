---
applyTo: '**'
---

1. Prime Directive

Only work on one file at a time. Multiple simultaneous file edits increase risk of merge conflicts and confusion.

While coding, include explanations as comments or as inline chat suggestions to clarify your approach.

2. File & Complexity Levels

2.1 Simple Files (<200 lines)

You may generate or modify functions directly.

Always include docstrings and type hints for new functions or classes.

2.2 Large or Complex Files (>200 lines)

Mandatory Planning Phase before any edits:

List the functions or sections needing change (e.g., routes.py, models.py).

Define the order of edits (e.g., implement auth flows first, then data models).

Identify dependencies (e.g., User model relied on in auth.py).

Estimate number of separate edits required.

Present the plan as a code comment or chat message, then request approval before proceeding.

3. FastAPI-Specific Guidelines

Endpoint Handlers (routers/ files):

Each new route must include:

Path and HTTP method decorator (@router.get, @router.post, etc.).

Request and response Pydantic models.

Clear status codes and error handling.

Data Models (models.py):

Define SQLAlchemy or Tortoise ORM models with proper field types.

Include relationship declarations and back-populates if needed.

Dependency Injection (dependencies.py):

Use Depends for database sessions, authentication, and configuration.

Testing (tests/ folder):

Suggest pytest fixtures for client and database setup.

Write at least one positive and one negative test for each route.

4. Pull Request & Refactoring Protocol

Keep PRs small and focused—aim for one feature or bug fix per PR.

If refactoring, ensure backward compatibility unless explicitly planning a breaking change.

Include a brief summary of changes and instructions to test locally in PR description.

End of guidelines.
