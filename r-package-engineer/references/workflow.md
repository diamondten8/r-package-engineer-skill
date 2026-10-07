# Stage gates and resuming work

Maintain a compact status table in the handoff or the project's existing engineering
notes: stage, evidence (path/commit/artifact), status, next action. Status is complete,
pending, invalidated, or blocked. Do not create a new tracking system for a small fix.
Multiple stages can be incomplete at once; choose the earliest relevant missing gate.

| Stage | Required evidence / exit gate | Resume behavior |
| --- | --- | --- |
| Idea | User problem, audience, concrete use cases, scope and non-goals; check existing alternatives | Ask only for decisions that affect implementation; infer routine choices |
| Architecture | Proposed exports/signatures, return contracts, failure behavior, internal modules, dependency choices and test strategy | Keep established contracts; revisit only affected decisions |
| Scaffold | Valid package metadata, chosen license, namespace strategy, R directory, test harness and build exclusions | Use scaffold only for a new empty destination; add missing files individually to existing packages |
| Implementation | Functions satisfy contracts; narrow exports, internal helpers, deliberate state and dependency handling | Implement a coherent vertical slice before extending API |
| Tests | Normal, edge and failure behavior covered; regression test for bug fixes; installed-package execution viable | Reuse tests and add behavior coverage relevant to the change |
| Documentation | Current Rd/namespace generated from roxygen2 where used; runnable examples; relevant workflow vignette; release notes | Regenerate only affected generated outputs; inspect generated diff |
| Check | Built tarball checked; logs and hash identify exact source artifact; findings resolved or explicitly investigated | Rebuild after any input change; never reuse an unrelated or stale check |
| CRAN readiness | Checklist reviewed, current policy consulted, cross-platform evidence, release metadata and submission notes | Report missing evidence; upload only on explicit submission request |

## Change invalidation

- Input/return/signature or export changes invalidate architecture contracts, affected
  tests/docs, check, and readiness; a breaking change needs user-visible migration guidance.
- Internal-only implementation fixes keep architecture/scaffold complete but invalidate
  relevant tests, examples if behavior changes, check and readiness.
- Dependency/metadata changes invalidate namespace/load tests, relevant documentation,
  build/check and readiness. A dependency addition must have a stated purpose.
- Documentation/example/test changes invalidate build/check and readiness, even when
  runtime code is unchanged. Pure skill-repository README edits do not change an R artifact.
- A changed R version/toolchain/platform requires new environment-specific check evidence.

Inspect git diffs and artifact hashes where available; don't rely on timestamps alone.
For old packages, lack of a formal design document does not justify redesigning working
APIs. Infer existing contracts from docs, exports and tests, and record uncertainties.

## Practical commands

1. Preflight: `Rscript --vanilla <skill>/scripts/validate_package.R <package>`.
2. In an existing roxygen2 project, regenerate with
   `Rscript --vanilla -e 'roxygen2::roxygenise(commandArgs(TRUE)[1])' <package>`.
3. Run targeted tests with `testthat::test_local(<package>)` in a developer session.
   This is fast feedback; installed-package tests in check remain necessary.
4. Build/check with `python <skill>/scripts/check_package.py <package> --output <outside-package>`.
5. Diagnose logs using the check reference; fix underlying causes and rerun affected
   tests plus a fresh final check. Stop retries if the same environmental blocker repeats
   without new evidence; identify the tool/dependency needed.

The scaffold intentionally contains no public API and no invented test assertions.
Add real functions and tests before expecting its test harness to pass. A vignette
template describes the scaffold; replace it with the actual user workflow as the API develops.
