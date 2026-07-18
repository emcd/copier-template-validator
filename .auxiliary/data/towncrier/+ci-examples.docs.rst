Add a CI Integration Examples page to the Sphinx documentation.
The new page covers wiring ``copiertv`` into common CI systems
(GitHub Actions for single-variant and per-variant loops, GitLab
CI), pip / Hatch caching considerations, and using ``--preserve``
to surface generated projects for debugging. Pinning the
installation version uses the released ``1.0a2`` (not a
not-yet-released ``1.0.0``).
