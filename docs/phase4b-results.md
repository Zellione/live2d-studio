# Phase 4B — standalone creation pipeline

Work in progress from `53ad920`, explicitly authorized on 2026-11-03. Production
deployment remains disabled. This report distinguishes implementation milestones
from the independent-character acceptance criterion, which is still under test.

The `create` CLI orchestrates ingestion, offline See-through, semantic import/SAM,
source restoration, quality review, procedural facial preparation, PSD2Live project
creation, role-derived authoring, expressions/idle, Cubism export, actual installed
Core/browser validation and standalone preview. Python calls authenticated loopback
MCP directly; no coding agent is a runtime dependency. The user's explicitly
exported token was verified by a standalone `mcp-check`; no profile secrets read.

Each completed stage has content hashes and a separate directory. Resume verifies
those hashes and skips unchanged stages, including GPU work. Failures retain their
own artifacts and retry in new directories. A per-run lock rejects concurrent
writers. Changing source/rights requires a new run. Old fixtures and accepted
Girl2 projects/recipes are untouched.

The semantic checkpoint rejects hard structural/source failures before any editor
mutation; otherwise it requires a reviewer record bound to the exact quality report.
Review includes semantic ownership, concealed face, source preservation and visible
limbs. Clothing names cannot prove limb anatomy. Final animation review is separate;
numeric motion or file-reference success cannot accept a character. `review-create`
records explicit rejection without requiring painting.

Generic authoring inspects all layers, mesh parents, deformers and their actual
key axes. It resolves mouth and paired brow parents by semantic association, refuses
ambiguous topology, and enumerates the inspected combination keys. Normalized curve
fields author smile/frown and separate brow emotion. Imported procedural blink,
mouth interior, gaze and head motion remain PSD2Live's approximate base rig.
Seven expressions and a subtle looping idle are authored against inspected ranges.
No Girl2 source hash, opaque target ID or canvas coordinate enters this builder.

Milestone 1: 109 Python tests and five JavaScript talk tests pass. Girl2 restoration
reproduces the accepted Phase 2.6 layer records exactly, without inference rerun.
A fresh project/PSD/export and 32 actual standalone rendered frames pass basic
control, expression, gaze, idle and neutral-reset checks. Human visual review remains
pending; this does not promote a replacement for accepted Girl2. Development failures
(ingestion validation and default-expression name collision) remain in the run.

The fourth CC0 portrait in stevenburrow's archive, Boy2, was independently inferred
using the pinned BF16 worker on RTX 5090. It fails missing-face/eye-support and
source-preservation checks and is blocked before authoring. Ground truth is retained
separately and never used by inference. Additional independent artwork evaluation
and final evidence are pending. **Primary Phase 4B acceptance is not yet claimed.**

Local evidence: `runs/phase4b-girl2`, `runs/phase4b-boy2`,
`runs/phase4b-boy2-{raw,truth,neural,sam}`. All generated artifacts remain ignored.
