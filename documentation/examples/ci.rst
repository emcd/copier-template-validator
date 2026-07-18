.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. +--------------------------------------------------------------------------+
   |                                                                          |
   | Licensed under the Apache License, Version 2.0 (the "License");          |
   | you may not use this file except in compliance with the License.         |
   | You may obtain a copy of the License at                                  |
   |                                                                          |
   |     http://www.apache.org/licenses/LICENSE-2.0                           |
   |                                                                          |
   | Unless required by applicable law or agreed to in writing, software      |
   | distributed under the License is distributed on an "AS IS" BASIS,         |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+


*******************************************************************************
CI Integration Examples
*******************************************************************************


This page shows how to wire ``copiertv`` into common continuous
integration (CI) systems. The examples assume the same configuration
file described in :doc:`cli`: a
``.auxiliary/configuration/copiertv/general.toml`` in the project
repository, with one or more ``answers-*.yaml`` files.


Install in CI
==============================================================================

``copiertv`` is a Python package. Install it in your CI step the
same way you would any Python tool:

.. code-block:: bash

    pipx install copiertv

Or via ``pip`` if the job uses a managed virtual environment:

.. code-block:: bash

    pip install copiertv

Pinning the version is recommended in CI. Pick the latest
release published on PyPI (currently the ``1.0a2`` alpha
series at the time of writing; substitute the version you
intend to validate against):

.. code-block:: bash

    pipx install copiertv==1.0a2


GitHub Actions
==============================================================================

The simplest integration runs the validator on every push and pull
request, against one specific variant:

.. code-block:: yaml

    name: Validate Template

    on:
      push:
        branches: [ main ]
      pull_request:

    jobs:
      validate:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: '3.12'
          - name: Install copiertv
            run: pipx install copiertv==1.0a2
          - name: Survey variants
            run: copiertv survey
          - name: Validate 'default' variant
            run: copiertv validate default

A common pattern is to iterate ``copiertv validate`` over every
discovered variant using ``survey`` output as the input list.
Use a ``while read`` loop rather than word splitting so variant
names containing whitespace are passed through intact:

.. code-block:: yaml

          - name: Validate every variant
            run: |
              while IFS= read -r variant; do
                echo "=== Validating $variant ==="
                copiertv validate "$variant"
              done < <(copiertv survey)

Failure of any variant fails the job, since ``copiertv`` exits
non-zero when a validation command fails or configuration is
invalid.


GitLab CI
==============================================================================

A minimal ``.gitlab-ci.yml`` snippet:

.. code-block:: yaml

    validate-template:
      image: python:3.12
      before_script:
        - pip install copiertv==1.0a2
      script:
        - copiertv survey
        - copiertv validate default


Caching dependencies
==============================================================================

``copiertv`` depends on Copier and a small set of Python packages.
If your CI job uses ``pip`` with a virtual environment, caching the
Hatch or ``pip`` cache between runs reduces install time noticeably:

.. code-block:: yaml

    # GitHub Actions example
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'
    - run: pip install copiertv==1.0a2

The example above uses ``pip`` so the actions/setup-python
``cache: 'pip'`` directive caches downloaded wheels across
runs. ``pipx`` keeps each tool in its own virtual environment,
so its cache story is different: pipx itself downloads wheels
through pip (so the user-level pip cache still applies to the
download step), but the resulting virtualenv is not part of the
pip cache. For pipeline simplicity, prefer ``pip install`` in
CI unless you specifically rely on pipx elsewhere on the same
runner.


Reusing generated projects for debugging
==============================================================================

When a CI run fails, the temporary project directories are removed
by default. To retain them for debugging, pass ``--preserve`` to
``copiertv validate``. CI runners typically make the workspace
artifacts accessible for download after the job, so the preserved
directory ends up in the artifacts bundle.

Example step for upload:

.. code-block:: yaml

          - name: Validate with preserve for debugging
            run: copiertv validate --preserve default
          - name: Upload preserved directories on failure
            if: failure()
            uses: actions/upload-artifact@v4
            with:
              name: copiertv-preserved
              path: /tmp/copiertv-*


When ``--preserve`` is not set, ``copiertv`` cleans up its
temporary directories automatically on both success and failure
paths, so the CI environment stays tidy without manual intervention.


Surface area to wire
==============================================================================

In summary, integrating ``copiertv`` into CI requires exactly:

- A step that installs ``copiertv`` (and Python if not already
  present).
- A step that runs ``copiertv survey`` if you want to enumerate
  variants in CI logs.
- One ``copiertv validate <variant>`` step per variant you care
  about (or a loop driven by ``survey`` output).
- Optional: a step that uploads preserved directories on failure.

There is no daemon, background process, or persistent service to
manage. Each invocation is independent and exits with a non-zero
status on failure.
