#!/usr/bin/env Rscript
# Static AST preflight. Does not source/evaluate package code or install dependencies.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L || args[[1L]] %in% c("--help", "-h")) {
  cat("Usage: Rscript --vanilla validate_package.R /absolute/package/path\n",
      "Static preflight only. ERROR exits 1; WARN is advisory; usage exits 2.\n",
      "Scans R/tests/demo, roxygen examples, Rd examples and Rmd R chunks.\n",
      "Cannot prove API quality, guard coverage, dynamic calls or CRAN acceptance.\n", sep = "")
  quit(status = if (length(args) == 1L) 0L else 2L)
}
root <- normalizePath(args[[1L]], winslash = "/", mustWork = TRUE)
errors <- 0L
finding <- function(level, path, message) {
  cat(sprintf("%s %s: %s\n", level, path, message))
  if (identical(level, "ERROR")) errors <<- errors + 1L
}
description <- file.path(root, "DESCRIPTION")
if (!file.exists(description)) {
  finding("ERROR", root, "Missing DESCRIPTION.")
  quit(status = 1L)
}
dcf <- tryCatch(read.dcf(description), error = function(e) {
  finding("ERROR", description, conditionMessage(e))
  NULL
})
if (is.null(dcf) || nrow(dcf) != 1L) quit(status = 1L)
field <- function(name) if (name %in% colnames(dcf)) dcf[1L, name] else ""
for (key in c("Package", "Version", "Title", "Description", "License")) {
  if (!nzchar(field(key))) finding("ERROR", description, paste("Missing field", key))
}
if (!grepl("^[A-Za-z][A-Za-z0-9.]*[A-Za-z0-9]$", field("Package"))) {
  finding("ERROR", description, "Invalid package name.")
}
if (!grepl("^[0-9]+([.-][0-9]+)+$", field("Version"))) {
  finding("ERROR", description, "Invalid numeric package version.")
}
if (!nzchar(field("Authors@R")) && !(nzchar(field("Author")) && nzchar(field("Maintainer")))) {
  finding("ERROR", description, "Need Authors@R or Author and Maintainer.")
}
if (nzchar(field("Authors@R"))) {
  invisible(tryCatch(parse(text = field("Authors@R")), error = function(e) {
    finding("ERROR", description, paste("Authors@R syntax:", conditionMessage(e)))
  }))
}
for (relative in c("NAMESPACE", "R")) {
  if (!file.exists(file.path(root, relative))) finding("ERROR", root, paste("Missing", relative))
}
if (!dir.exists(file.path(root, "tests"))) finding("WARN", root, "No tests directory; review behavior coverage.")
namespace <- file.path(root, "NAMESPACE")
if (file.exists(namespace)) {
  if (any(grepl("exportPattern", readLines(namespace, warn = FALSE), fixed = TRUE))) {
    finding("ERROR", namespace, "Broad exportPattern is incompatible with intentional small API.")
  }
}
if (grepl("\\+ *file +LICENSE", field("License")) && !file.exists(file.path(root, "LICENSE"))) {
  finding("ERROR", description, "Declared LICENSE file is missing.")
}
dependencies <- function(key) {
  value <- gsub("\\([^)]*\\)", "", field(key))
  trimws(strsplit(value, ",", fixed = TRUE)[[1L]])
}
declared <- unique(c(dependencies("Imports"), dependencies("Depends"),
                     dependencies("Suggests"), field("Package"),
                     "base", "compiler", "datasets", "graphics", "grDevices",
                     "grid", "methods", "parallel", "splines", "stats", "stats4",
                     "tcltk", "tools", "utils"))
if ("R" %in% declared) declared <- setdiff(declared, "R")
runtime_declared <- unique(c(dependencies("Imports"), dependencies("Depends"), field("Package")))
optional <- setdiff(dependencies("Suggests"), runtime_declared)

call_name <- function(head) {
  if (is.symbol(head)) return(as.character(head))
  if (is.call(head) && is.symbol(head[[1L]]) && as.character(head[[1L]]) %in% c("::", ":::")) {
    return(as.character(head[[3L]]))
  }
  ""
}
inspect <- function(node, path, runtime) {
  if (is.call(node)) {
    name <- call_name(node[[1L]])
    banned <- c("setwd", "install.packages", "update.packages", "attach", "readline")
    if (runtime) banned <- c(banned, "library", "require", "source", "load", "save.image", "<<-")
    if (name %in% banned) finding("ERROR", path, paste("Forbidden call:", name))
    if (name == ":::") {
      if (runtime) finding("ERROR", path, "Do not access non-exported external APIs with :::.")
    }
    if (name %in% c("::", ":::")) {
      package <- as.character(node[[2L]])
      if (!(package %in% declared)) finding("ERROR", path, paste("Undeclared namespace:", package))
      if (runtime && package %in% optional) {
        finding("WARN", path, paste("Verify requireNamespace guard for optional dependency:", package))
      }
    }
    # Qualified dependency installers, e.g. remotes::install_github(), renv::restore().
    head <- node[[1L]]
    if (is.call(head) && call_name(head[[1L]]) %in% c("::", ":::")) {
      package <- as.character(head[[2L]])
      if ((package %in% c("pak", "remotes", "devtools") && grepl("^(install|pkg_install)", name)) ||
          (package == "renv" && name %in% c("install", "restore"))) {
        finding("ERROR", path, paste("Dependency installer:", package, name))
      }
    }
  }
  if (is.call(node) || is.expression(node) || is.pairlist(node)) {
    children <- as.list(node)
    for (index in seq_along(children)) {
      # Check before binding: missing formals/subscripts are not ordinary values.
      if (!identical(children[[index]], quote(expr = ))) inspect(children[[index]], path, runtime)
    }
  }
}
scan <- function(text, path, runtime = FALSE) {
  parsed <- tryCatch(parse(text = text, keep.source = TRUE), error = function(e) {
    finding("ERROR", path, paste("R syntax:", conditionMessage(e)))
    NULL
  })
  if (!is.null(parsed)) inspect(parsed, path, runtime)
}
for (directory in c("R", "tests", "demo")) {
  paths <- list.files(file.path(root, directory), pattern = "\\.[rR]$", recursive = TRUE, full.names = TRUE)
  for (path in paths) {
    lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
    scan(lines, path, identical(directory, "R"))
    # Parse roxygen examples separately because R's parser correctly ignores comments.
    example <- character()
    active <- FALSE
    for (line in lines) {
      if (grepl("^\\s*#'\\s*@examples( |$)", line)) {
        active <- TRUE
        next
      }
      if (active && (grepl("^\\s*#'\\s*@", line) || !grepl("^\\s*#'", line))) active <- FALSE
      if (active) example <- c(example, sub("^\\s*#' ?", "", line))
    }
    # Rd macros are handled by Rd2ex after documentation generation, not R parse.
    if (length(example) && !any(grepl("\\\\(dont|if|out|test)", example))) {
      scan(example, paste0(path, " [roxygen examples]"))
    }
  }
}
for (path in list.files(file.path(root, "man"), pattern = "\\.Rd$", full.names = TRUE)) {
  temporary <- tempfile(fileext = ".R")
  tryCatch({
    tools::Rd2ex(path, out = temporary)
    if (file.exists(temporary)) {
      scan(readLines(temporary, warn = FALSE), paste0(path, " [Rd examples]"))
    }
  }, error = function(e) finding("ERROR", path, paste("Rd extraction:", conditionMessage(e))))
  unlink(temporary)
}
paths <- list.files(file.path(root, "vignettes"), pattern = "\\.[Rr]md$", recursive = TRUE, full.names = TRUE)
if (length(paths) && !nzchar(field("VignetteBuilder"))) {
  finding("ERROR", description, "Rmd vignettes exist but VignetteBuilder is missing.")
}
for (path in paths) {
  lines <- readLines(path, warn = FALSE)
  chunk <- character()
  active <- FALSE
  for (line in lines) {
    if (!active && grepl("^\\s*`{3,}\\{r([ ,}])", line)) {
      active <- TRUE
    } else if (active && grepl("^\\s*`{3,}\\s*$", line)) {
      scan(chunk, paste0(path, " [R chunk]"))
      active <- FALSE
      chunk <- character()
    } else if (active) {
      chunk <- c(chunk, line)
    }
  }
  if (active) finding("ERROR", path, "Unclosed R chunk.")
}
cat(sprintf("Preflight finished: %d ERROR(s). This is not R CMD check.\n", errors))
cat("Limits: aliases/dynamic calls, inline/Sweave chunks, native code and optional guards need review.\n")
quit(status = if (errors > 0L) 1L else 0L)
