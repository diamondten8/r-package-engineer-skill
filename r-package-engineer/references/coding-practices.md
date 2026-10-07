# Package coding and architecture

## Public API and internal modules

Write the contract before exposing a function: parameter types and lengths, defaults,
NA/NaN/Inf behavior, empty input, return type/class/shape, ordering and side effects.
Choose a few cohesive entrypoints instead of exporting implementation steps. Preserve
argument names and return contracts; deliberate breaking changes need versioning,
NEWS entries and migration guidance. Prefer composable functions over one function
with many mutually exclusive modes.

Use `R/<feature>.R` for public entrypoints and `R/<feature>-helpers.R` for internal
work when separation aids navigation. Helpers receive their inputs explicitly and
have no `@export`; `@noRd` is appropriate for short undocumented internals. Longer
internal contracts may use Rd with `@keywords internal`. A dot prefix is a naming
choice, not access control. Export neither helpers nor every object via `exportPattern`.

Validate at boundaries; trust validated invariants inside helpers. Reject ambiguous
partial argument matching in API examples. Use `seq_along()`/`seq_len()`, explicit
`drop = FALSE`, scalar condition checks, and vectorized operations where clear.
Avoid `1:length(x)`, recycling accidents, silent coercion, and mutable default state.

## Namespace and dependencies

| Field / mechanism | Use |
| --- | --- |
| Imports | Required runtime packages; calls via `pkg::fun()` or targeted `@importFrom` |
| Suggests | Tests, examples, vignettes, optional features; guard runtime optional features with `requireNamespace()` |
| Depends | R minimum version, or intentionally attached packages when the design truly needs them |
| LinkingTo | Headers used by compiled code; does not replace a runtime Imports dependency |
| `@export`, `@exportS3Method` / method registration | Intentional public symbols and dispatch; review generated namespace |

Do not import entire packages to fix one missing symbol. Declare dependencies even
when another dependency happens to pull them in. Namespace qualification alone
does not add a DESCRIPTION dependency. Avoid external `:::`; use supported APIs.
List necessary minimum versions based on used functionality, not the developer's
installed version. Remove unused dependencies deliberately after checking docs/tests.
Keep development tools in Suggests only if package-shipped artifacts use them;
roxygen2 itself need not be a runtime dependency.

For optional features, raise an actionable condition when the dependency is absent;
never install it at runtime. Explicitly registering S3 methods differs from exporting
all methods by name. Confirm S4/native registration when those systems are used.

## Errors, state and resources

Use `stop(..., call. = FALSE)` or existing structured conditions; use `rlang::abort()`
only when that dependency is justified. Messages name the argument, expected contract,
and remedy. Expose condition classes if downstream code should recover by type.
Do not return `NULL` or success-shaped data for unexpected failures. Catch only
recoverable errors; preserve useful context and let programmer errors surface.
Distinguish warning-worthy degraded results from invalid input and routine messages.

Never call the banned runtime patterns listed in SKILL.md. Also avoid `<<-` into
global state, `assign(..., .GlobalEnv)`, and hidden `source()` of user-machine paths.
Use explicit path arguments, `system.file()` for installed assets, and `tempfile()`
for scratch work. Write persistent files only to a location the caller chose; make
overwrites explicit. Use `on.exit(..., add = TRUE)` for connections/cleanup and scoped
state restoration. Use local test fixtures for RNG, locale and options; do not set
the user's seed on package load. Hooks must remain lightweight and noninteractive.

Avoid hardcoded home paths, credentials and network use in routine checks. Optional
network features need timeouts and graceful offline behavior. Native code must use
supported R APIs, registered routines, portable flags and declared system requirements;
an R-only smoke test does not validate a compiled package.

## Metadata and build hygiene

Use factual DESCRIPTION title/description and real Authors@R/maintainer details.
Choose a compatible license, preserve third-party copyright, and document data rights.
Keep development notes, CI, caches and secrets outside the source tarball via
`.Rbuildignore`; inspect tarball contents rather than ignoring entire source directories.
Generated `NAMESPACE`/Rd files belong in version control. `inst/` is for installed
assets; `data/` and `R/sysdata.rda` have different visibility and documentation needs.

For authoritative namespace mechanics, see
[roxygen2 imports and exports](https://roxygen2.r-lib.org/articles/namespace.html).
