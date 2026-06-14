## ADDED Requirements

### Requirement: Variant Discovery
The system SHALL discover template variants by globbing for `answers-*.yaml`
files in a configurable directory and extracting variant names by removing
the `answers-` prefix from file stems (e.g., `answers-default.yaml` yields
`default`).

#### Scenario: Variants found
- **WHEN** the answers directory contains `answers-default.yaml` and
  `answers-maximum.yaml`
- **THEN** the system SHALL report variants `default` and `maximum`

#### Scenario: No variants found
- **WHEN** the answers directory contains no `answers-*.yaml` files
- **THEN** the system SHALL report an empty variant list

#### Scenario: Missing answers directory
- **WHEN** the configured answers directory does not exist
- **THEN** the system SHALL raise a `ConfigurationAbsence` error

### Requirement: Template Copy
The system SHALL copy a Copier template to a temporary directory using the
Copier Python API (`run_copy`) with the variant's answers data, `defaults`,
`overwrite`, and configurable `vcs_ref` and `unsafe` options.

#### Scenario: Successful copy
- **WHEN** a valid answers file and template source are provided
- **THEN** the system SHALL invoke `run_copy` with the template source,
  destination directory, answers data, `defaults=True`, `overwrite=True`,
  and the configured `vcs_ref` value

#### Scenario: No VCS ref configured
- **WHEN** `vcs_ref` is not configured or is set to `null`
- **THEN** the system SHALL omit the `vcs_ref` argument, using the
  template's current working-tree content

#### Scenario: Unsafe template support
- **WHEN** `unsafe` is configured as `true`
- **THEN** the system SHALL pass `unsafe=True` to `run_copy`, enabling
  templates that use tasks or Jinja extensions

#### Scenario: Copier not installed
- **WHEN** the `copier` package is not installed
- **THEN** the system SHALL raise a `ConfigurationInvalidity` error with
  a message indicating Copier is missing

#### Scenario: Copier copy fails
- **WHEN** `run_copy` raises a Copier error
- **THEN** the system SHALL raise a `ConfigurationInvalidity` error wrapping
  the Copier exception

### Requirement: Validation Command Execution
The system SHALL execute a configurable list of validation commands
sequentially, supporting an explicit working directory model and path
interpolation placeholders.

Each command configuration SHALL specify:
- `args`: the argument sequence (required).
- `cwd`: the working directory for the subprocess (optional, defaults
  to the template source directory).

The following placeholders SHALL be interpolated in both `args` and `cwd`
values before execution:
- `{template_dir}`: the template source directory.
- `{project_dir}`: the generated project directory (inside the temp dir).
- `{temp_dir}`: the temporary directory root.
- `{variant}`: the variant name.

#### Scenario: All commands succeed
- **WHEN** all validation commands exit with status zero
- **THEN** the system SHALL report success

#### Scenario: Command working directory defaults to template
- **WHEN** a command does not specify `cwd`
- **THEN** the system SHALL execute the command with the template source
  directory as the working directory

#### Scenario: Command working directory uses placeholder
- **WHEN** a command specifies `cwd = "{project_dir}"`
- **THEN** the system SHALL execute the command with the generated project
  directory as the working directory

#### Scenario: Command args use placeholders
- **WHEN** a command specifies `args = ["tool", "check", "--source", "{project_dir}"]`
- **THEN** the system SHALL interpolate `{project_dir}` to the actual
  generated project path before execution

#### Scenario: Command fails
- **WHEN** a validation command exits with non-zero status
- **THEN** the system SHALL raise a `ValidationCommandFailure` error
  wrapping the subprocess error, including the temporary directory path
  when preservation is active, and stop execution

#### Scenario: Command not found
- **WHEN** a validation command binary is not found on `PATH`
- **THEN** the system SHALL raise a `ConfigurationInvalidity` error

### Requirement: Temporary Directory Management
The system SHALL manage temporary directories for generated projects,
creating them before validation and cleaning them up afterward unless
preservation is requested.

#### Scenario: Cleanup after validation
- **WHEN** the preserve flag is `false`
- **THEN** the system SHALL remove the temporary directory after validation
  completes (success or failure)

#### Scenario: Preserve for inspection
- **WHEN** the preserve flag is `true`
- **THEN** the system SHALL retain the temporary directory and report its
  path in the result

### Requirement: Result Reporting
The system SHALL produce a `ValidationResult` with variant name, temporary
directory path, items attempted, items generated, and preserved flag, and
render it as Markdown for terminal display.

#### Scenario: Successful validation
- **WHEN** validation completes successfully
- **THEN** the system SHALL render a result showing variant name, temporary
  directory, item counts, and cleanup status

### Requirement: Configuration Hierarchy
The system SHALL read configuration from multiple sources with the following
precedence (highest first): CLI arguments, environment variable
`COPIERTV_CONFIG`, per-project config file, per-user config file. The
environment variable replaces lower-precedence config files (it does not
overlay them).

#### Scenario: Per-project config present
- **WHEN** `.auxiliary/configuration/copiertv/general.toml` exists relative
  to the project root
- **THEN** the system SHALL load configuration from it

#### Scenario: Per-user config present
- **WHEN** a config file exists at the platform-appropriate location
  (via `platformdirs` / `emcd-appcore`)
- **THEN** the system SHALL load configuration from it as defaults

#### Scenario: Environment variable replaces lower config
- **WHEN** `COPIERTV_CONFIG` is set to a file path
- **THEN** the system SHALL load configuration from that path instead of
  (not in addition to) the per-project and per-user config files

#### Scenario: CLI overrides config
- **WHEN** both config file and CLI arguments provide the same setting
- **THEN** the CLI argument SHALL take precedence

### Requirement: Project Root Detection
The system SHALL detect the project root by walking up from the current
working directory looking for VCS markers (`.git`, `.hg`, `.svn`).

#### Scenario: VCS directory found
- **WHEN** a `.git`, `.hg`, or `.svn` directory exists in an ancestor of
  the current working directory
- **THEN** the system SHALL use that directory as the project root

#### Scenario: No VCS directory found
- **WHEN** no VCS marker is found up to the filesystem root
- **THEN** the system SHALL use the current working directory as the
  project root

### Requirement: CLI Subcommands
The system SHALL provide `survey` and `validate` subcommands via the
`copiertv` entry point.

#### Scenario: Survey subcommand
- **WHEN** the user runs `copiertv survey`
- **THEN** the system SHALL list all discovered variant names

#### Scenario: Validate subcommand
- **WHEN** the user runs `copiertv validate --variant default`
- **THEN** the system SHALL copy the template with the `default` answers,
  run validation commands, and report results
