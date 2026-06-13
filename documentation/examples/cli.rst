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
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+


*******************************************************************************
CLI Examples
*******************************************************************************


Surveying Variants
===============================================================================

List available template variants from an answers directory:

.. code-block:: bash

    copiertv survey

This reads the answers directory from your configuration and prints variant
names to stdout.


Validating Variants
===============================================================================

Validate a single variant:

.. code-block:: bash

    copiertv validate default

Validate and preserve the generated project for inspection:

.. code-block:: bash

    copiertv validate --preserve default


Configuration
===============================================================================

Create ``.auxiliary/configuration/copiertv/general.toml`` in your template
repository:

.. code-block:: toml

    [answers]
    directory = "data/copier"

    [[commands]]
    args = ["hatch", "env", "prune"]

    [[commands]]
    args = ["hatch", "--env", "develop", "run", "make-all"]

    [options]
    preserve = false
    unsafe = false

Use placeholders in command arguments and working directories:

.. code-block:: toml

    [[commands]]
    args = ["make", "check", "--source", "{project_directory}"]
    cwd = "{template_directory}"

Available placeholders: ``{template_directory}``, ``{project_directory}``,
``{temporary_directory}``, ``{variant}``.
