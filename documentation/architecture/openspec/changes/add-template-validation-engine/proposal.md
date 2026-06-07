# Change: Add Template Validation Engine

## Why

Two existing projects (`emcdproj` and `agentsmgr`) each implement Copier
template validation with nearly identical patterns but divergent error
handling, result reporting, and validation scope. Extracting a generic
validator eliminates duplication and provides a single, configurable tool
for any Copier template project.

## What Changes

- Implement core validation engine: variant discovery, template copy
  (via Copier Python API), validation command execution, and result
  reporting.
- Add configurable validation commands (users supply the commands to run;
  the tool is agnostic about what gets validated).
- Add configurable answers directory path (no hardcoded convention).
- Add structured error hierarchy wrapping Copier and filesystem errors.
- Add `ValidationResult` dataclass with Markdown rendering for terminal
  output.
- Implement CLI via `tyro` with `survey` and `validate` subcommands.
- Support a TOML configuration file with hierarchy: per-user
  (platformdirs), per-project (`.auxiliary/configuration/copiertv/
  general.toml`), environment variable, and CLI overrides.
- Wire logging via Python `logging` module (scribe pattern).

## Impact

- Affected specs: `template-validation` (new capability).
- Affected code: `sources/copiertv/` (engine, CLI, config, exceptions,
  results modules).
- External consumers: `emcdproj` and `agentsmgr` will eventually delegate
  to this package via its CLI (separate follow-up by their owners).
