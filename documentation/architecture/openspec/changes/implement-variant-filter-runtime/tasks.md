# Tasks for change: Variant Filter Design Contract (Field Removed; Parked)

> Parked. The `[options] variants` field has been removed from
> `Configuration` as of commit `02f4026`. The tasks below describe
> the work required to re-introduce the field when a consumer
> need is identified, **not** active implementation work.

## 0. Status (recorded at parking time)

- [x] 0.1 Remove `Configuration.variant_filter` from the dataclass
      and parser.
- [x] 0.2 Drop the `[options] variants` row from the Configuration
      Reference table in `documentation/examples/cli.rst`.
- [x] 0.3 Update the variant-related parser tests.
- [x] 0.4 Record the use-case rationale and re-introduction path
      in `proposal.md` (parked change).

## 1. Engine (when re-introducing)

- [ ] 1.1 Re-add `Configuration.variant_filter` as
      `Absential[tuple[str, ...]]` with default `absent`.
- [ ] 1.2 Re-add `_parse_variant_filter` helper in
      `sources/copiertv/configuration.py`.
- [ ] 1.3 Re-add the `variant_filter` row to the
      `_parse_options_section` return mapping and pass it through
      `_parse_configuration_data`.
- [ ] 1.4 Extend `survey_variants` to accept an optional
      `variant_filter` parameter. When the filter is absent,
      preserve current behavior; when non-empty, intersect
      lexicographically; when empty tuple, return `()`. Configured
      names without answer files SHALL be silently omitted.
- [ ] 1.5 Extend `validate_variant` to enforce `variant_filter`
      on the requested variant name. Enforce BEFORE template copy
      and command execution. When the filter is absent, preserve
      current behavior; when the requested name is not permitted,
      raise `ConfigurationInvalidity(field='options.variants',
      value=<requested>, expected=<allowed-set description>)`.

## 2. Helpers (when re-introducing)

- [ ] 2.1 Add a private helper (e.g. `_format_permitted_set`) in
      `engine.py` that formats the `expected` description for the
      `ConfigurationInvalidity` message per the bounded/truncated
      requirement. Lexicographic sort, sixteen-entry bound,
      per-name length bound of 32 code points including the
      ellipsis, "and N more" indicator with N = len(filter) - 16.

## 3. CLI (when re-introducing)

- [ ] 3.1 Update `_survey` in `sources/copiertv/cli.py` to pass
      `config.variant_filter` to `survey_variants`.
- [ ] 3.2 Verify `_validate` and `_ValidateCommand.execute` need
      no changes beyond what `validate_variant` does; the filter
      enforcement at the engine level covers the CLI path.

## 4. Tests (when re-introducing)

- [ ] 4.1 Add engine tests: survey with absent / non-empty /
      empty filter; survey with configured name absent from
      answer directory; validate with absent / matching /
      non-matching / empty-filter cases; validate with configured
      allowed name but missing answers file.
- [ ] 4.2 Add CLI subprocess tests covering survey filtered
      output and validate rejecting an out-of-filter variant.
- [ ] 4.3 Add tests for the bounded rejection message:
      - empty filter expects "no variants are permitted"
      - 16-entry filter expects full listing and no
        "and N more" suffix
      - 20-entry filter expects first 16 + "and 4 more"
        with N = 20 - 16 = 4
      - filter including exactly one entry longer than 31 code
        points expects the displayed name to be its first 31
        code points + "…" with displayed length exactly 32 code
        points and NO "and N more" suffix (since
        len(filter) == 1, not greater than sixteen)
      - the suffix must never read "and 0 more" — verify by
        constructing every case where one might naively be
        emitted and asserting absence

## 5. Documentation (when re-introducing)

- [ ] 5.1 Re-add the `[options] variants` row to the Configuration
      Reference table in `documentation/examples/cli.rst`.
- [ ] 5.2 Re-add the empty-clear bullet for `variants = []` to
      the "Absent vs. empty semantics" subsection.
- [ ] 5.3 Update towncrier fragment describing the runtime
      contract change.

## 6. Proposal workflow (when re-introducing)

- [ ] 6.1 Open a fresh change proposal that references this
      parked design contract.
- [ ] 6.2 Apply `opsx-archive` to this change once the new
      proposal lands.