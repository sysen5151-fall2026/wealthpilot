# Coursework acceptance run

The execution method and limits are in SPEC.md. Original human-review procedures are preserved in reference-real-participant-procedure.md; their blank forms are not completed human records.

1. From the project folder run `.venv/bin/python -m pytest -q -rs`.
2. Run `.venv/bin/python scripts/coursework_exercise.py`.
3. Read evidence/acceptance/coursework-role-report.json: ten role protocols, two separate operator processes and two deliberate corruption/recovery exercises.
4. Push the package, including .github, through a repository writer. Show the actual new GitHub Actions run only after it passes.

Local verification: 131 passed, 0 skipped. Cloud requirement relationships and team rule approval are not established by these tests.
