## Context

`emcdproj template validate` and `agentsmgr-maintain template validate`
share identical core logic (copier copy invocation, variant discovery,
temporary directory management) but differ in error handling maturity,
result reporting, and validation scope. The new `copiertv` package must
serve both consumers and be general enough for any Copier template project.

## Goals / Non-Goals

Goals:
- Single configurable validation engine reusable by any Copier template
  project.
- Configurable validation commands (the tool does not prescribe what to
  validate).
- Configurable answers directory path.
- Structured error handling and result reporting.
- CLI with `survey` and `validate` subcommands.
- Configuration file support for persistent settings.
- Language-agnostic (no reliance on Python-specific config files like
  `pyproject.toml`).

Non-Goals:
- Prescribing a specific validation pipeline (full QA vs. narrow rendering
  check).
- Managing Copier template content or schema.
- Adapting `emcdproj` or `agentsmgr` (separate follow-up by their owners).
- Wrapping validation commands in Hatch environments.

## Decisions

### Copier Python API over subprocess

Use Copier's `run_copy` Python API instead of `subprocess.run('copier', 'copy', ...)`.

```python
from copier import run_copy

copy_kwargs = dict(
    str( source_directory ),
    project_directory,
    data = answers_data,
    defaults = True,
    overwrite = True,
    quiet = True,
)
if vcs_ref is not None:
    copy_kwargs[ 'vcs_ref' ] = vcs_ref
if unsafe:
    copy_kwargs[ 'unsafe' ] = True
worker = run_copy( **copy_kwargs )
```

This avoids a subprocess dependency, provides structured error types
(`UnsafeTemplateError`, `UserMessageError`), and gives access to
`worker.answers.combined` for post-copy inspection.

`vcs_ref` defaults to `None` (use current working-tree content). Users
may configure it to `'HEAD'`, a branch name, or a tag.

`unsafe` defaults to `false`. Users with templates that use tasks or
Jinja extensions must set it to `true`.

Alternatives considered:
- Subprocess invocation (existing pattern): Rejected because it adds an
  external dependency, provides less structured errors, and requires
  PATH resolution.

### Configurable validation commands

Validation commands are supplied as a list of entries, each with:
- `args`: the argument sequence (required).
- `cwd`: the working directory for the subprocess (optional, defaults
  to the template source directory).

The following placeholders are interpolated in both `args` and `cwd`
values before execution:
- `{template_dir}`: the template source directory.
- `{project_dir}`: the generated project directory (inside the temp dir).
- `{temp_dir}`: the temporary directory root.
- `{variant}`: the variant name.

This supports both reference consumers:
- `emcdproj` pattern: run from the generated project (`cwd="{project_dir}"`).
- `agentsmgr` pattern: run from the template repo (default `cwd`), pass
  the generated project as an argument (`--source {project_dir}`).

The tool executes commands sequentially, wrapping subprocess errors in
structured exceptions. No Hatch environment wrapping is performed; users
include Hatch invocations in their command definitions if needed.

Alternatives considered:
- Built-in validation presets (e.g., "full-qa", "narrow"): Rejected because
  validation scope is project-specific and presets would need constant
  maintenance.
- Shell string parsing: Rejected because argument sequences are safer and
  avoid shell injection.
- Automatic Hatch wrapping: Rejected because `copiertv` and its dependencies
  are regular runtime dependencies, not development dependencies.
- Only generated-project cwd: Rejected because the `agentsmgr` reference
  consumer needs to run from the template repository.

### Configurable answers directory

The answers directory is a required configuration value (CLI arg or config
file). No default convention is imposed, since projects use `data/copier/`,
`tests/data/profiles/`, or other layouts.

Alternatives considered:
- Auto-discovery by searching for `answers-*.yaml` in common locations:
  Rejected as fragile and surprising.
- Hardcoding `data/copier/`: Rejected because it conflicts with
  `agentsmgr`'s convention.

### Configuration hierarchy

Four-tier configuration with clear precedence:

1. **CLI arguments** (highest precedence).
2. **Environment variable** `COPIERTV_CONFIG` pointing to a config file
   (replaces lower-precedence files, does not overlay them).
3. **Per-project config** at `.auxiliary/configuration/copiertv/general.toml`
   (relative to project root). This path is configurable via per-user
   configuration.
4. **Per-user config** via `platformdirs` / `emcd-appcore` (XDG-compliant
   on Linux, `~/Library/Application Support` on macOS, `%APPDATA%` on
   Windows).

Project root is detected by walking up from CWD looking for VCS markers
(`.git`, `.hg`, `.svn`).

No reliance on language-specific files (`pyproject.toml`, `Cargo.toml`,
`package.json`).

Alternatives considered:
- Flat config file at repo root: Rejected because it pollutes the project
  root and conflicts with language-specific config conventions.
- Only CLI args: Rejected because projects need persistent defaults.

### Error hierarchy

Extend the existing `Omniexception`/`Omnierror` pattern with
domain-specific exceptions: `ConfigurationAbsence`,
`ConfigurationInvalidity`, `FileOperationFailure`,
`ValidationCommandFailure`. Each has a `render_as_markdown()` method for
terminal display.

Alternatives considered:
- Raw exception propagation (emcdproj pattern): Rejected because it produces
  poor user experience.
- Single generic error class: Rejected because callers need to distinguish
  error categories.

### Result reporting

`ValidationResult` dataclass with variant name, temporary directory,
items attempted/generated, preserved flag, and per-command status. Rendered
as Markdown via the existing `render_and_print_result` pattern from
`appcore`.

## Risks / Trade-offs

- Config file format may need iteration as consumers adopt the tool.
  Mitigation: start minimal, version the format.
- No built-in validation presets means users must always configure commands.
  Mitigation: provide clear documentation and examples.
- Copier's Python API is a private API (`copier._main.Worker`); the public
  API (`run_copy`) may suffice. Mitigation: use `run_copy` which is the
  documented public API.

## Migration Plan

1. Implement core engine and CLI.
2. Add configuration file support.
3. `emcdproj` and `agentsmgr` owners adapt their projects to use `copiertv`
   CLI in QA pipelines (separate changes, out of scope for this proposal).

## Open Questions

- Should the tool support parallel variant validation?
