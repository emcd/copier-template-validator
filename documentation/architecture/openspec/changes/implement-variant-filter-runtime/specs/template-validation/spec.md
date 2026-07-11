# Status

The `[options] variants` configuration key has been removed from
`Configuration` as part of this commit stack. This change is
parked and the requirements below describe the design contract
for future re-introduction, not the current system behavior. They
have not been archived into `openspec/specs/template-validation/spec.md`
because no consumer currently relies on them.

When a downstream consumer reports a need that matches one of the
recorded use cases, the implementation must satisfy these
requirements exactly. Any deviation requires a fresh proposal
that updates this content before the implementation lands.

## ADDED Requirements

### Requirement: Variant Filter Survey

The system SHALL filter the discovered variant list through
`Configuration.variant_filter` when the field is present:

- **WHEN** `variant_filter` is absent the system SHALL return every
  discovered variant (current behavior).
- **WHEN** `variant_filter` is a non-empty tuple the system SHALL
  return only the discovered variants whose names appear in the
  filter, preserving lexicographic ordering. Configured names that
  lack a corresponding `answers-*.yaml` file SHALL be omitted
  silently, not raised as errors.
- **WHEN** `variant_filter` is the empty tuple the system SHALL
  return an empty list (explicit-clear semantic).

#### Scenario: No filter configured
- **WHEN** `Configuration.variant_filter` is absent
- **AND** the answers directory contains `answers-default.yaml`
  and `answers-maximum.yaml`
- **THEN** `survey_variants` returns `('default', 'maximum')`

#### Scenario: Filter narrows results
- **WHEN** `Configuration.variant_filter = ('default',)` only
- **AND** the answers directory contains `answers-default.yaml`
  and `answers-maximum.yaml`
- **THEN** `survey_variants` returns `('default',)`

#### Scenario: Filter excludes all
- **WHEN** `Configuration.variant_filter = ('other',)` only
- **AND** the answers directory contains `answers-default.yaml`
- **THEN** `survey_variants` returns `()`

#### Scenario: Empty filter clears
- **WHEN** `Configuration.variant_filter = ()`
- **AND** the answers directory contains `answers-default.yaml`
- **THEN** `survey_variants` returns `()`

#### Scenario: Configured name without answer file
- **WHEN** `Configuration.variant_filter = ('other',)` where
  `other` has no `answers-other.yaml`
- **AND** the answers directory contains `answers-default.yaml`
- **THEN** `survey_variants` returns `()`: the intersection of
  the discovered set `('default',)` and the filter `('other',)`
  is empty, and the configured `other` is silently omitted
  because no answer file exists for it

### Requirement: Variant Filter Validate

The system SHALL enforce `Configuration.variant_filter` on the
`validate` path. Enforcement SHALL occur before any template copy
or validation command executes, so non-CLI callers receive the
same contract.

- **WHEN** `variant_filter` is absent the validation SHALL permit
  any requested variant name (current behavior).
- **WHEN** `variant_filter` is a non-empty tuple and the requested
  variant name appears in the filter the validation SHALL proceed.
- **WHEN** `variant_filter` is a non-empty tuple and the requested
  variant name does NOT appear in the filter the system SHALL
  raise `ConfigurationInvalidity` constructed with
  `field='options.variants'`, `value=<requested variant name>`,
  and `expected=<permitted-set description>` per the Rejection
  Message requirement.
- **WHEN** `variant_filter` is the empty tuple the system SHALL
  raise `ConfigurationInvalidity` for any requested variant with
  `expected` describing "no variants are permitted".

#### Scenario: Validate within filter
- **WHEN** `Configuration.variant_filter = ('default',)` only
- **AND** the user runs `copiertv validate default`
- **THEN** the system copies the template and runs the
  configured validation commands

#### Scenario: Validate outside filter rejected
- **WHEN** `Configuration.variant_filter = ('default',)` only
- **AND** the user runs `copiertv validate maximum`
- **THEN** the system SHALL raise `ConfigurationInvalidity` with
  `field='options.variants'`, `value='maximum'`, and `expected`
  describing the permitted set that contains `default` and not
  `maximum`

#### Scenario: Empty filter rejects everything
- **WHEN** `Configuration.variant_filter = ()`
- **AND** the user runs `copiertv validate default`
- **THEN** the system SHALL raise `ConfigurationInvalidity` with
  `field='options.variants'`, `value='default'`, and `expected`
  describing "no variants are permitted"

#### Scenario: Configure allowed name but answers file missing
- **WHEN** `Configuration.variant_filter = ('default',)` only
- **AND** the configured answers directory does not contain
  `answers-default.yaml`
- **THEN** the system SHALL raise `ConfigurationAbsence` for the
  missing `answers-default.yaml` (the filter passed, the
  file-existence check then surfaced the missing file)

### Requirement: Rejection Message Construction

When a validate rejection occurs, the system SHALL construct
`ConfigurationInvalidity` as
`ConfigurationInvalidity(field='options.variants',
value=<requested variant name>, expected=<allowed-set
description>)`. Because `ConfigurationInvalidity` renders `field`
before any free-form reason, no additional reason argument SHALL
be passed.

The `expected` description SHALL be bounded and deterministic in
both entry count and per-name length:

- **WHEN** `variant_filter` is the empty tuple, `expected` SHALL
  describe the permitted set as "no variants are permitted".
- **WHEN** `variant_filter` is non-empty, the displayed list
  SHALL be sorted lexicographically, SHALL include at most
  sixteen entries, and SHALL bound each displayed name to a
  maximum of thirty-two Unicode code points **including** the
  trailing `…` (U+2026 HORIZONTAL ELLIPSIS). Truncated names
  retain the first thirty-one code points of the source name
  and append `…`; untruncated names SHALL appear verbatim.
- **WHEN** `variant_filter` contains more than sixteen entries,
  the description SHALL append "and N more" where
  `N = len(variant_filter) - 16`. The suffix SHALL NOT appear
  when `variant_filter` contains sixteen or fewer entries, even
  when one or more displayed names were truncated by the per-name
  length bound. Per-name truncation is communicated solely by the
  trailing `…` on the affected entry and never affects `N`.

#### Scenario: Empty filter rejection message
- **WHEN** `Configuration.variant_filter = ()`
- **AND** the user runs `copiertv validate default`
- **THEN** the rendered `ConfigurationInvalidity` message SHALL
  identify `options.variants` as the field, `default` as the
  rejected value, and "no variants are permitted" as the allowed
  set description

#### Scenario: Bounded rejection message
- **WHEN** `Configuration.variant_filter` contains twenty variant
  names in arbitrary order
- **AND** the user runs `copiertv validate` with a name not in
  the filter
- **THEN** the rendered `ConfigurationInvalidity` message SHALL
  list exactly sixteen of those names in lexicographic order
  followed by "and 4 more"

#### Scenario: Long variant name truncation
- **WHEN** `Configuration.variant_filter` includes a variant name
  whose value exceeds thirty-one code points
- **AND** the user runs `copiertv validate` with a name not in
  the filter
- **THEN** that long name in the displayed `expected`
  description SHALL be truncated to its first thirty-one code
  points followed by `…`, and any other entries SHALL appear
  beside it in lexicographic order respecting the same bound

#### Scenario: Long variant name with no count overflow
- **WHEN** `Configuration.variant_filter` contains exactly one
  entry whose value exceeds thirty-one code points
- **AND** the user runs `copiertv validate` with a name not in
  the filter
- **THEN** the displayed `expected` description SHALL contain
  exactly one entry, that entry SHALL end with `…`, and the
  description SHALL NOT include any "and N more" suffix
  (because `len(filter) == 1`, not greater than sixteen)

### Requirement: Backward Compatibility for Omitted Filter

The system SHALL preserve the current behavior for users that
omit `[options] variants` from their configuration file or
inherit an absent value through merge. Survey lists every
discovered variant; validate runs the requested variant
unconditionally.

#### Scenario: Existing user without variants key
- **WHEN** the project configuration contains no `variants`
  key under `[options]`
- **AND** the user runs `copiertv survey` or `copiertv
  validate <name>`
- **THEN** behavior matches the v1.0a2 release exactly
