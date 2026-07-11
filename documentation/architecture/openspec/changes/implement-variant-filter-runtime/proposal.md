# Change: Variant Filter Design Contract (Field Removed; Parked)

## Status

The `[options] variants` field has been **removed** from
`Configuration` as part of this commit stack. The project is in
alpha and downstream consumers can expect breaking changes.

This proposal is kept as the **design contract for future
re-introduction** rather than as an active implementation plan. The
specification, design, and tasks below describe what an
implementation must satisfy if and when the field is re-added. No
implementation work is queued against this proposal until a real
consumer need is identified.

## Why

Even though no current consumer requires the field, the use cases
below are documented here so that the design decisions are available
the next time someone evaluates whether to re-introduce it:

- **CI split-fast/slow**: a template with a fast `default` variant
  (lint + unit) and a slow `maximum` variant (heavy integration
  tests) can run the fast variant on every pull request and the
  slow variant nightly. Each CI job sets its own `variants` filter
  to bound its scope.
- **Templates with many variants**: when a template exposes five or
  more preset combinations, a filter lets the default validation
  step focus on a subset of combinations, deferring niche combos to
  scheduled jobs.
- **Conditional coverage on protected branches**: a `release`
  variant filter restricts validation to the release configuration
  before tagging, gating "did the release path actually work" with
  no manual intervention.
- **Selective E2E**: a heavy variant that runs Playwright or
  Cypress against deployed infrastructure can be filtered out of
  default `copiertv validate` runs and triggered separately.
- **Audit and inventory use**: `copiertv survey` with a filter
  reports which discovered variants are in the "blessed" set,
  useful for documentation pipelines that report current support.

These use cases motivated the design work preserved in this
proposal but did not justify shipping the implementation now:
both current consumers (`agents-common` and the planned
`python-project-common` cutover) have a small fixed set of variants
and run them all on every validation pass without a filter.

## What Changes

- The `[options] variants` TOML key is no longer recognized by the
  parser. Configurations that set it will see the key ignored
  silently (no error, no fallback) because the alpha-release
  contract permits breaking changes.
- `Configuration.variant_filter` no longer exists. Code that
  referenced the field has been removed as part of this commit
  stack.
- The design contract captured in `design.md` and the requirements
  captured in `spec.md` describe the runtime behavior that a
  future re-introduction must satisfy, including:
  - strict allowlist semantics with no positional-CLI bypass,
  - absent filter permits every variant; present filter (including
    the empty tuple) restricts both survey and validate identically,
  - field enforcement happens before template copy or command
    execution,
  - structured rejection message construction with bounded
    allowed-set description,
  - filter membership does not imply the variant exists,
  - explicit-empty semantics for both `commands = []` and
    `variants = []`.

## Re-introduction path

When a downstream consumer reports a need that matches one of the
recorded use cases, the implementation work is small and the design
decisions are already settled. The re-introduction commit should:

1. Re-add `Configuration.variant_filter`, `_parse_variant_filter`,
   and the relevant rows in `_parse_options_section` and
   `_parse_configuration_data`.
2. Implement the requirements in `specs/template-validation/spec.md`.
3. Restore the `[options] variants` row to the Configuration
   Reference table in `documentation/examples/cli.rst`.
4. Open a fresh change proposal that references this design contract
   and supersedes the parked status here. Apply the `opsx-archive`
   workflow on this change when the new proposal lands.

## Impact

- Affected specs: `template-validation` (ADDED Requirements describe
  the future contract; no current consumer).
- Affected code at removal time: `sources/copiertv/configuration.py`,
  `tests/test_000_copiertv/test_200_configuration.py`,
  `documentation/examples/cli.rst`.
- External consumers: `agents-common` (migrated) is unaffected
  because its configuration does not set `variants`. The pending
  `python-project-common` cutover is unaffected for the same
  reason. Existing configurations that set `variants = [...]` will
  see the key ignored with no error; the variant discovery,
  survey, and validate paths continue to operate over the full
  set of discovered variants as before.
- Documentation: the Configuration Reference table in
  `documentation/examples/cli.rst` has been updated to drop the
  `[options] variants` row and to trim the "Absent vs. empty
  semantics" subsection to two keys.