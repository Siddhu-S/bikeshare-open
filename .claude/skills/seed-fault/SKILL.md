---
name: seed-fault
description: seed the fault described in argument into src/, run the test to ensure it fails, and then log change, failing test output, and hook stderr in docs/SEEDED_FAULTS.md. Use when prompted to seed, inject, or break something.
allowed-tools: Read, Edit, Bash(python -m pytest*), Bash(git diff*), Bash(git status*)
---

# Seeding fault: $ARGUMENTS

Work in this order. Do not fix the fault in this skill.

1. Run `git status` and mention if src/ or tests/ has anything modified, and if so then stop.
2. Make the change described in input as a single edit in src/, and use edit tool so PostToolUse leakage hook runs. Copy the stderr from the hook, and mention if it does not fire.
3. Run `python -m pytest tests/ -q` and copy the failing output verbatim. Mention if every test passes.
4. Show `git diff src/`.
5. Add a section to docs/SEEDED_FAULTS.md headed with the fault description, containing those three outputs pasted exactly.
6. Stop and wait. The user will ask for the fix separately and count turns.