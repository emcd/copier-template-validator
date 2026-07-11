## Context

`Configuration.variant_filter` was introduced as a documented
configuration surface during the v1.0a2 release but the runtime
behavior was never wired up. The field has been **removed** from
the `Configuration` dataclass as part of this commit stack because
no current consumer requires it and the project is in alpha. This
change is kept as the **design contract for future
re-introduction**; nothing here is queued for implementation
until a real consumer need is identified.

## Goals / Non-Goals

Goals:
- Preserve the design contract so re-introduction is cheap.
- Document the recorded use cases that justify the field for the
  next reviewer.
- Spell out the strict allowlist semantics, bounded rejection
  message construction, and the absent/empty distinction so the
  next implementation cannot drift.

Non-Goals:
- Implementing the runtime contract now.
- Changing the field's surface (still `[options] variants`) when
  re-introduced.
- Adding CLI flags for variant selection.
- Introducing a "validate all matching variants" mode (the current
  CLI shape validates one explicit variant per invocation).

## Recorded use cases

These motivated the design work preserved here. They are recorded
so the next reviewer can quickly decide whether re-introduction is
warranted:

- **CI split-fast/slow**: a fast variant on every PR, a slow
  variant on a schedule. Each CI job carries its own `variants`
  filter.
- **Templates with many variants**: subset selection for default
  validation runs when the template exposes five or more preset
  combinations.
- **Conditional coverage on protected branches**: a `release`
  filter validates only the release configuration before tagging.
- **Selective E2E**: a heavy variant is filtered out of default
  runs and triggered separately.
- **Audit and inventory use**: `copiertv survey` with a filter
  reports which discovered variants are in the "blessed" set.

Neither current consumer (`agents-common`, planned
`python-project-common`) currently requires the filter.

## Decisions

These decisions are the technical contract for the next
implementation. They are not subject to change without a separate
review.

### Filter is an allowlist, not a default-selection gate

`variant_filter` is an allowlist of variant names for both survey
and validate. The positional `validate NAME` argument selects
which variant to validate; it does not override the filter. An
absent filter permits every discovered/requested variant. A
present filter (including the empty tuple) restricts both paths
identically.

This deliberately diverges from the precedent set by
`options.preserve` and `--preserve`, where the CLI flag overrides
the configuration value. Variant selection is not a configuration
default — it is an explicit choice controlled either by the
configuration surface or by the user listing discovery output, not
simultaneously by both.

### Survey filters through the configuration value

`survey_variants` accepts an optional `variant_filter` parameter
and applies it to the discovered set. The decision to treat an
empty filter as "list no variants" matches the established
semantics in the parser, where `commands = []` and `variants = []`
are explicit-clear values. The function preserves lexicographic
ordering of the discovered set; configured names that lack answer
files are simply absent from the survey output, not an error.

### Validate enforces the filter

`validate_variant` enforces the filter check before any template
copy or command execution, so non-CLI callers receive the same
contract. A requested variant name outside the filter, or any
variant when the filter is the empty tuple, raises
`ConfigurationInvalidity`.

### Rejection message construction

The rejection is constructed as:

```
ConfigurationInvalidity(
    field = 'options.variants',
    value = requested_variant_name,
    expected = <allowed-set description>,
)
```

`ConfigurationInvalidity` renders `field` before any free-form
reason, so the rejection cannot also carry a long-form prose
explanation. All information must fit into the three structured
fields. The `expected` description is bounded and deterministic:

- For the empty filter, `expected` SHALL describe the permitted
  set as "no variants are permitted".
- For a non-empty filter, the description is bounded both by
  entry count and by per-name length:
  - The list is sorted lexicographically.
  - At most sixteen entries are included.
  - Each displayed name is bounded to a maximum of thirty-two
    Unicode code points **including** the trailing `…` (U+2026
    HORIZONTAL ELLIPSIS). Truncated names retain the first
    thirty-one code points of the source name and append `…`;
    untruncated names are emitted verbatim.
  - The "and N more" suffix is appended only when the configured
    filter contains more than sixteen entries. In that case
    `N = len(variant_filter) - 16`. Per-name truncation is a
    display concern that never contributes to `N`; a displayed
    long name shortened to thirty-one code points plus `…` is
    still one displayed entry, not zero. The suffix SHALL NOT
    appear for filters of sixteen or fewer entries, even when
    per-name truncation occurs, so the suffix is never "and 0
    more".

The bound makes the message size deterministic regardless of how
long the configured variant names are. With sixteen entries of
up to thirty-two code points each joined by `, ` plus a possible
"and N more" suffix (which only appears when `len(filter) > 16`),
the maximum rendered length of the expected description is well
under one kilobyte for any sane configuration.

### Empty-cleared semantics preserved

`Configuration.variant_filter = ()` (the explicit-empty case)
clears the inherited filter through the merge machinery, matching
the parser-side distinction already documented in the in-flight
docs commit. The empty tuple is still a present allowlist — it
permits no variant names — so on the validate path it rejects
every requested variant. The empty filter does not behave "the
same as a non-empty filter" because a non-empty filter permits
its members; it behaves as a present-but-empty allowlist.

### Filter membership does not imply the variant exists

A filter may list names that have no corresponding
`answers-*.yaml` file. The filter check passes for those names
because the filter is an allowlist, not an existence claim. The
existing missing-answers-file behavior in `validate_variant`
raises `ConfigurationAbsence` for any requested variant whose
answers file is missing, regardless of filter membership. The
filter must not be misinterpreted as a guarantee that the variant
is real.