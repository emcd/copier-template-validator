Add a Configuration Reference section to the Sphinx documentation
that catalogs every TOML key recognized by copiertv — answers
directory, ``[[commands]]`` with ``args`` and ``cwd``, and the
``[options]`` keys for template-directory, variants, vcs-ref,
preserve, and unsafe — along with each key's type and purpose. The
section documents absent-versus-empty semantics for ``commands``,
``variants``, and ``vcs-ref`` (the first two clear inherited lists
when set to an empty array; an empty ``vcs-ref`` is treated as
absent) and clarifies which error fields the CLI Markdown error
interface renders for type-validation versus structural errors. The
README points to this reference rather than duplicating it.
