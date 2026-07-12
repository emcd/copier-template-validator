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
==============================================================================

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
    template-directory = "."
    preserve = false
    unsafe = false

Use placeholders in command arguments and working directories:

.. code-block:: toml

    [[commands]]
    args = ["make", "check", "--source", "{project_directory}"]
    cwd = "{template_directory}"

Available placeholders: ``{template_directory}``, ``{project_directory}``,
``{temporary_directory}``, ``{variant}``.


Configuration Reference
------------------------------------------------------------------------------

The full set of TOML keys recognized by copiertv:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Key
     - Type
     - Description
   * - ``[answers] directory``
     - string (path)
     - Directory containing ``answers-*.yaml`` preset files.
   * - ``[[commands]]``
     - array of tables
     - Validation commands to execute against each generated project.
       Each entry *must* declare ``args``; ``cwd`` is optional.
   * - ``[[commands]] args``
     - sequence of strings (required)
     - Argument vector passed to the command. Supports placeholders.
   * - ``[[commands]] cwd``
     - string (optional)
     - Working directory. Supports placeholders. Defaults to the
       template directory.
   * - ``[options] template-directory``
     - string (path)
     - Source directory of the Copier template. Required when not
       supplied via CLI.
   * - ``[options] vcs-ref``
     - string (optional)
     - Git ref passed to Copier (branch, tag, or commit). An empty
       string is treated as absent.
   * - ``[options] preserve``
     - bool (optional)
     - When true, keeps generated project directories on disk after
       validation rather than cleaning them up.
   * - ``[options] unsafe``
     - bool (optional)
     - When true, allows unsafe Copier template features (custom
       Jinja extensions, template migrations, and pre/post
       tasks).

Absent vs. empty semantics
..............................................................................

Configuration values flow through three layers in ascending precedence:
user configuration (via ``emcd-appcore``), project configuration
(``general.toml``), and CLI overrides. When a key is *omitted*, its
value is inherited from the next-lower layer. The parser
deliberately distinguishes *absent* from *explicitly empty* for two
keys, but in two different ways:

- ``commands = []`` clears the inherited list — useful for
  overriding a default set without replacing it. ``commands = []``
  matches no commands.
- ``vcs-ref = ""`` is treated as absent. Empty strings are a
  convenient sentinel value from configuration templates and should
  behave the same as omitting the key.

All other sequence and scalar keys follow the standard inheritance
behavior: omit the key to inherit, present the key with a value to
override.

Configuration errors
..............................................................................

Invalid configuration surfaces through the CLI's Markdown error
interface. The exact content depends on which kind of error is
raised:

- Type validation errors from the ``_expect_*`` helpers identify
  the field path, the expected type, and (where reasonable to
  print) the offending value.
- Structural errors raised by ``DataInvalidity`` (for example, a
  ``[[commands]]`` entry missing ``args``) identify the source
  configuration file path along with a short reason.

Configuration parsing is fail-fast: the parser stops at the first
invalid value rather than reporting all errors at once.
