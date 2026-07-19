Adapt the rendered CLI output to the output stream's declared
encoding so error and success messages render correctly on
hosts whose default stdout encoding cannot represent the
decorated Unicode characters used in the markdown output
(``\u2705`` for success, ``\u274c`` for failure,
``\U0001f4c1`` for the preserved-files marker, and the bare
and variation-selector-16 forms of ``\U0001f5d1`` for the
cleanup marker). On UTF-capable streams the rendered lines
are emitted unchanged; on streams whose encoding cannot
represent the decorations the characters are replaced with
semantic ASCII labels (``[OK]``, ``[ERROR]``, ``[FILES]``,
``[CLEANUP]``) and any remaining unencodable text in
user-supplied paths and messages is preserved via
``backslashreplace`` rather than silently dropped. The previous
behavior raised ``UnicodeEncodeError`` mid-print on Windows
runners with default ``cp1252`` stdout and produced an empty,
nonzero exit, which caused the entire GitHub Actions Windows
matrix to fail on the module-level subprocess tests.
