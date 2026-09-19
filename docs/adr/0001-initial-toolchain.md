# ADR-0001: Initial Toolchain
Status: Proposed — team confirmation required
Context: The Chapter 1 WealthPilot scaffold needs a language, a runtime, and a decision on whether the in-product language model is local or hosted.
Decision: Use Python 3.12 with a local virtual environment. Use a locally hosted model through LM Studio.
Rationale: Local hosting keeps investor profile data on the machine during the course prototype.
What would change this decision: Revisit during the Week 12 trade study if measured latency misses the success criterion.