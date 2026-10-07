# CRAN readiness checklist

Consult [current CRAN policy](https://cran.r-project.org/web/packages/policies.html)
and [the submission page](https://cran.r-project.org/submit.html) at release time.
This checklist is an engineering gate, not a guarantee of acceptance or a frozen
copy of policy. Mark each item complete, pending, or not applicable with evidence
and rationale; do not mark unavailable platform checks complete.

## Product and metadata

- [ ] Package has a clear purpose and appropriate name; check name availability
  and conflicts for new submissions. Title/description explain functionality.
- [ ] Version identifies this release; NEWS records changes. Maintainer identity
  and email are real and reachable; Authors@R roles and contributors are accurate.
- [ ] License choice is confirmed and compatible with all bundled code/data;
  required license files, citations and third-party attribution are present.
- [ ] DESCRIPTION dependencies, minimum versions, encoding, URLs, BugReports,
  system requirements and vignette builder match actual use. No development-only
  Remotes dependency is required for CRAN installation.
- [ ] Public API is reviewed; exports are intentional; compatibility or migration
  is documented; internal helpers remain unexported.

## Artifact and technical evidence

- [ ] Documentation regenerated where appropriate, versioned and aligned with code.
  Examples, tests and relevant vignettes run with public/local resources.
- [ ] Build contents exclude secrets, caches, credentials, machine paths and
  development artifacts; include all install-time assets and source required.
- [ ] Full `R CMD check --as-cran` was run on the release tarball, with 0 ERRORs,
  0 WARNINGs; all NOTEs investigated and recorded. Include SHA-256 and log paths.
- [ ] Test relevant operating systems and current release R; obtain R-devel evidence
  when feasible, especially for submission/native code. Record exact versions and
  unavailable checks. Windows/compiler and macOS differences need actual evidence.
- [ ] Address portability, non-ASCII handling, library restrictions, runtime/memory
  use, offline operation, optional dependencies and appropriate temporary-file cleanup.
- [ ] Native code has registration/portable build evidence and any applicable
  sanitizer/strict checks. Reverse-dependency impact evaluated for updates that
  change widely used behavior, interfaces or compiled code.

## Submission package

- [ ] `cran-comments.md` concisely lists platforms/R versions, exact ERROR/WARNING/
  NOTE counts, explanations and reverse-dependency results where relevant. Missing
  checks are stated honestly. Exclude this development note from the tarball.
- [ ] New-submission or incoming-feasibility NOTEs are explained; network outages
  are documented and relevant checks retried when service is available. Do not
  suppress checks or classify missing dependencies as a harmless NOTE.
- [ ] Resubmission notes address each reviewer point; release tarball is unchanged
  since its final check; filenames/version/hash match the prepared submission.
- [ ] User has explicitly requested actual submission before uploading or sending
  email. Preparation and local checking are allowed without a separate upload flow.

## Suggested evidence record

```text
Version / source revision:
Tarball / SHA-256:
Platform / R / toolchain:
Command / date / log path:
ERROR / WARNING / NOTE counts:
Each NOTE and disposition:
Cross-platform / R-devel / reverse-dependency evidence:
Pending readiness items:
```

Primary technical specification:
[Writing R Extensions](https://cran.r-project.org/doc/manuals/r-release/R-exts.html).
