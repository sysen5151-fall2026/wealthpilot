# Cloud model checklist before recording

The 2026-11-08 verification attempt reached the Innoslate sign-in screen. No cloud model was changed during this repository update. Compare this list with the current Financial Project before saying the model and product agree.

1. Confirm the selected classroom demonstration function was F.6. If it was another function, the video must follow that classroom choice instead.
2. Show the physical first-level IDEF0: F.1–F.6 should have the actual performing assets C.1–C.6 at the bottom mechanism side. The previous functional-only mechanism deferral is not the Milestone 2 physical view.
3. Show F.6's second-level IDEF0 with F.6.1–F.6.5, C.6.1–C.6.5, the data from F.5 and the Explanation Rules and Plan Save Request controls.
4. Verify the internal explanation path F.6.1 → F.6.2 and IO.6.1 F.6.2 → F.6.3, IO.6.2 F.6.3 → F.6.4, IO.6.3 F.6.4 → F.6.5. Use the cloud model's exact conduit IDs; repository docstrings currently name IF.6.1–IF.6.4.
5. Show a function hierarchy containing F.6 and its five children, and an asset hierarchy containing C.6 and its five components. Module docstrings are not a replacement for these model diagrams.
6. Open a parent system functional requirement, such as 1.4.7, and its component requirement CS6.1.4.4. Verify the actual derivation/allocation relationship and the satisfaction relation to the responsible component. Open input/output requirements and conduit requirements under the component specification as well.
7. Check the proposed system-wide allocation in `requirements-flowdown.md` against the exact current NFR-04 and CS6.2.4 statements. Show the actual relationship and the recorded equivalence rationale; do not present a proposal as an existing cloud link.
8. Reconcile F.6's current name with `Manage Investment Plan Delivery` in the code; older reports used `Explain, Present and Save Investment Plan`. Use one current name consistently rather than silently mixing baselines.
9. Do not claim performance, novice comprehension or complete stakeholder acceptance has been verified. Their missing evidence is separate from successful F.6 software tests.

Prepare the model tabs before starting the recording. Retain a dated export if the connection is unreliable, but identify an export as such; do not present a hand-drawn reconstruction as a live Innoslate view.
