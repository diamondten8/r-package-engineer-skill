# Tests and documentation

## Behavior tests

Use the project's existing framework; scaffold defaults to testthat edition 3.
Test public behavior first: normal results, empty/scalar/vector inputs, missing and
nonfinite values where relevant, invalid classes/shapes, boundary values, return
attributes, and promised ordering. For each bug fix, reproduce the defect before
fixing it. Test error classes or stable useful message fragments, not entire volatile
stack traces. Use numeric tolerances justified by the algorithm.

Test helpers directly only for meaningful algorithmic invariants; internal tests
must not force helpers into the public API. An existing contract test is more valuable
than a test repeating the function's exact implementation. Coverage percentages are
diagnostic, not an acceptance substitute. Check namespace loading and optional
dependency absence when relevant. Never skip all tests to obtain a green check.

Keep tests deterministic, fast and independent of order. Use small shipped/local
fixtures, temporary directories and scoped cleanup. Avoid real credentials and
external services; test adapters using controlled doubles and separate explicitly
opted-in integration tests. Do not change the working directory. Namespace attachment
in `tests/testthat.R` is permitted; runtime package code must not attach dependencies.
Verify that tests run against the installed package in R CMD check, not only load_all().

For state isolation patterns, see
[testthat fixtures](https://testthat.r-lib.org/articles/test-fixtures.html).

## roxygen2 and namespace

Each exported function needs a useful title/description, `@param` for its complete
signature (including `...`), `@returns` describing shape/class, failure/side-effect
semantics where relevant, runnable `@examples`, and intentional `@export`. Use
`@inheritParams` and shared Rd topics to avoid inconsistent duplicated descriptions.
Document datasets (format, variables, provenance and licensing), classes and methods
as applicable. Internal helpers must not acquire exports through broad namespace rules.

Run roxygen2 when source docs change and inspect both `man/` and `NAMESPACE`. Do not
edit generated Rd/namespace to silence check: fix the source. For a hand-maintained
project, preserve that convention or migrate only with a deliberate scoped decision.
Check Rd usage against signatures, cross-references and output contracts.

## Examples and vignettes

Examples should be short, reproducible and illustrate actual returned values or
effects. Use built-in/shipped data and temporary files; clean up writes. Guard
Suggests usage with `requireNamespace()`. `\donttest{}` still runs in as-CRAN checks;
`\dontrun{}` is for genuinely unsuitable interactive/external actions, never a cover
for broken code. Keep at least a representative offline runnable example for an API.

Add a vignette when a multi-step workflow needs explanation. Follow the existing
engine; a new R Markdown vignette needs knitr/rmarkdown in Suggests, `VignetteBuilder:
knitr`, engine metadata and portable runnable chunks. A package with a tiny API need
not acquire a token vignette, but explicitly requested vignettes must be delivered.
Teach setup, workflow, interpretation and limitations; reference functions rather
than duplicating every Rd topic. Build source and rendered outputs with the actual
package toolchain. Do not disable chunk evaluation globally to obtain passing builds.

README is the quick entrypoint; Rd is the API contract; vignettes teach workflows;
NEWS records user-visible changes. Submission notes summarize evidence and remaining
NOTEs. Keep these roles separate. A README example is not proof that installed
examples/vignettes run in check.
