# Common R CMD check findings

Start with `00check.log`, then `00install.out`, test `.Rout.fail`, example output,
and vignette/build logs. Distinguish infrastructure failures from package defects.
The first causal finding often explains later failures; fix it before broad edits.
Severity varies by R version and context; the table is a diagnosis guide, not a waiver.

| Finding / search text | Likely cause | Repair and verify |
| --- | --- | --- |
| package installation failed | Compile error, missing headers/system library, syntax or load hook | Read install log; fix first error; declare system needs; rerun install and full check |
| dependency not available | Missing local provision, unavailable CRAN package, incorrect dependency/version | Verify DESCRIPTION and repositories; provision outside runtime; never install from package code |
| Namespace dependency not required / missing namespace dependency | Namespace declarations and DESCRIPTION disagree | Audit `::`, imports and registrations; remove/add the correct declaration; regenerate |
| no visible binding / no visible global function definition | Undeclared import, typo, NSE use | Qualify/import true functions; fix typo; use explicit pronouns/NSE design; do not blanket globalVariables all names |
| undocumented code objects | Accidental export or missing Rd | Remove helper export or document intended API; regenerate docs/namespace |
| codoc mismatches / undocumented arguments | Rd usage or parameters disagree with function formals | Fix roxygen source/inheritance and regenerate; verify defaults and `...` |
| S3 generic/method consistency / apparent S3 methods exported but not registered | Wrong signature or missing method registration | Align generic/method contract; register via roxygen2; test dispatch on installed package |
| examples failed | Missing asset/dependency, stale API, invalid example | Reproduce installed example; make it short/offline/guarded; do not hide it with dontrun |
| tests failed | Behavior regression, order/state leak, optional dependency assumption | Read first test failure; reproduce in vanilla session; isolate fixtures; retain regression coverage |
| re-building vignettes failed | Missing builder/tool, missing file, failing chunks | Check Suggests/VignetteBuilder/metadata; use installed paths; run full vignette build |
| non-standard files / hidden files / empty directories | Development artifacts leaked or unnecessary scaffold directories | Inspect tarball; make narrow Rbuildignore changes; never exclude real tests/docs to silence check |
| invalid DESCRIPTION / malformed Authors@R / license | DCF issue, identity error, incompatible/missing license file | Fix metadata using actual author/license decisions; verify built metadata |
| non-ASCII characters in R code | Nonportable literals or encoding | Use suitable Unicode escapes in R code; verify UTF-8 docs and locale behavior |
| unable to verify current time / URL checks fail | Network, proxy, service or malformed URL | Distinguish outage from broken URL; verify and retry; retain evidence; do not disable incoming/URL checks |
| New submission / incoming feasibility NOTE | Incoming checks need human review | Inspect precise text/name conflicts; explain in submission notes; never assume every incoming NOTE is harmless |
| check takes too long / examples exceed time | Excessive computation or network | Use small representative examples/fixtures; optimize with measurement; retain meaningful coverage |
| compiled code / registration / non-portable flags | Unsupported APIs or platform assumptions | Fix supported interfaces and build config; run target platform/strict checks |
| PDF manual failure / LaTeX missing | Documentation defect or incomplete developer toolchain | Inspect TeX log; fix Rd or provision tools; a no-manual run remains partial evidence |

Do not respond with blanket `suppressWarnings()`, skipped tests, weakened thresholds,
`_R_CHECK_FORCE_SUGGESTS_=false`, or blanket NOTE exemptions. If an environment cannot
run a check, name the missing prerequisite and leave that gate pending.

Check mechanics and authoritative terminology:
[Writing R Extensions: checking packages](https://cran.r-project.org/doc/manuals/r-release/R-exts.html#Checking-packages).
