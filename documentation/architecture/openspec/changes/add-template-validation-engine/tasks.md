## 1. Core Engine
- [ ] 1.1 Implement variant discovery (glob `answers-*.yaml`, extract names
      with proper `answers-` prefix removal)
- [ ] 1.2 Implement template copy via Copier Python API (`run_copy`) with
      configurable `vcs_ref` and `unsafe` options
- [ ] 1.3 Implement validation command execution with `cwd` and placeholder
      interpolation (`{template_dir}`, `{project_dir}`, `{temp_dir}`,
      `{variant}`)
- [ ] 1.4 Implement temporary directory management (create, yield, cleanup)
- [ ] 1.5 Implement `ValidationResult` dataclass with Markdown rendering
- [ ] 1.6 Implement `ValidationCommandFailure` exception carrying temp
      directory path when preservation is active

## 2. Error Handling
- [ ] 2.1 Define exception hierarchy (`ConfigurationAbsence`,
      `ConfigurationInvalidity`, `FileOperationFailure`,
      `ValidationCommandFailure`)
- [ ] 2.2 Implement error interception decorator for CLI commands

## 3. Configuration
- [ ] 3.1 Define configuration dataclass (`AnswersDirectory`,
      `ValidationCommands` with `cwd`/`args`, `PreserveFlag`,
      `VariantFilter`, `VcsRef`, `UnsafeFlag`)
- [ ] 3.2 Implement TOML config file reader with hierarchy: per-user
      (platformdirs), per-project (`.auxiliary/configuration/copiertv/
      general.toml`), env var (`COPIERTV_CONFIG`, replaces lower config),
      CLI overrides
- [ ] 3.3 Implement project root detection via VCS markers (`.git`, `.hg`,
      `.svn`)
- [ ] 3.4 Implement placeholder interpolation engine (`{template_dir}`,
      `{project_dir}`, `{temp_dir}`, `{variant}`)
- [ ] 3.5 Implement CLI argument parsing via `tyro` (`survey`, `validate`
      subcommands)
- [ ] 3.6 Implement config merge (CLI overrides config file)

## 4. CLI Wiring
- [ ] 4.1 Wire `survey` subcommand (list discovered variants)
- [ ] 4.2 Wire `validate` subcommand (copy + validate + report)
- [ ] 4.3 Wire logging (scribe pattern) and error display

## 5. Testing
- [ ] 5.1 Unit tests for variant discovery
- [ ] 5.2 Unit tests for configuration parsing
- [ ] 5.3 Integration tests for full validation flow (with mock Copier)
- [ ] 5.4 CLI smoke tests

## 6. Documentation
- [ ] 6.1 Update README.rst with project description and usage
- [ ] 6.2 Add configuration file reference
- [ ] 6.3 Add examples for `emcdproj` and `agentsmgr` migration
