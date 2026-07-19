Upgrade ``emcd-appcore[cli]`` from ``~=1.6`` to ``~=1.7`` so the
project pulls in tyro 1.x instead of tyro 0.9.x. The 0.9.x line
emits box-drawing characters in its ``--help`` output that
fail to encode on Windows runners with default cp1252 stdout,
causing the entire GitHub Actions Windows matrix to fail on
``tests/test_000_copiertv/test_400_cli.py::test_200_cli_help``.
Tyro 1.x contains the upstream non-UTF-8 tty fix and resolves
the failure.
