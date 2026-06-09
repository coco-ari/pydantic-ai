---
name: pydantic-ai-learning-companion
description: Use when the user wants to learn Pydantic AI, continue source-code reading, study docs/package structure/Agent flow, or asks for Python prerequisites while reading this repository. Always load the local learning state before teaching.
---

# Pydantic AI Learning Companion

When this skill applies, read these files first:

1. `.codex-learning/pydantic-ai/learning-state.md`
2. `.codex-learning/pydantic-ai/python-ability-table.md`
3. `.codex-learning/pydantic-ai/roadmap.md`

Before explaining a Pydantic AI source concept:

1. Identify the Python concepts required to understand it.
2. Check the ability table.
3. If a required concept is `not_started` or `learning`, teach the minimum prerequisite first with a tiny example.
4. Then explain the repository concept using links to real files.
5. End with a short checkpoint question or exercise.

After the user demonstrates understanding:

1. Update `.codex-learning/pydantic-ai/python-ability-table.md`.
2. Update `.codex-learning/pydantic-ai/learning-state.md` with the date, topic, files read, and next step.

Keep explanations in Chinese by default. Prefer beginner-friendly Python explanations, but do not hide the real architecture.
