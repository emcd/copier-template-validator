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
                                    copiertv                                   
*******************************************************************************

.. image:: https://img.shields.io/pypi/v/copiertv
   :alt: Package Version
   :target: https://pypi.org/project/copiertv/

.. image:: https://img.shields.io/pypi/status/copiertv
   :alt: PyPI - Status
   :target: https://pypi.org/project/copiertv/

.. image:: https://github.com/emcd/copier-template-validator/actions/workflows/tester.yaml/badge.svg?branch=master&event=push
   :alt: Tests Status
   :target: https://github.com/emcd/copier-template-validator/actions/workflows/tester.yaml

.. image:: https://emcd.github.io/copier-template-validator/coverage.svg
   :alt: Code Coverage Percentage
   :target: https://github.com/emcd/copier-template-validator/actions/workflows/tester.yaml

.. image:: https://img.shields.io/github/license/emcd/copier-template-validator
   :alt: Project License
   :target: https://github.com/emcd/copier-template-validator/blob/master/LICENSE.txt

.. image:: https://img.shields.io/pypi/pyversions/copiertv
   :alt: Python Versions
   :target: https://pypi.org/project/copiertv/


📋 A generic validator for `Copier <https://github.com/copier-org/copier>`_
templates. Instantiates templates with various preset answer files
(variants) and runs configurable validation commands against the
generated projects.

Key Features
-------------------------------------------------------------------------------

- **Configurable validation commands**: Define validation commands in a
  TOML configuration file. The tool is agnostic about what gets validated.
- **Configurable answers directory**: Specify where variant answer files
  live. No hardcoded convention imposed.
- **Placeholder interpolation**: Use ``{template_directory}``,
  ``{project_directory}``, ``{temporary_directory}``, and ``{variant}``
  in command args and working directories.
- **Copier Python API**: Uses ``copier.run_copy`` directly instead of
  shelling out to a subprocess.
- **Configuration hierarchy**: CLI arguments, per-project config, and
  per-user config (via ``emcd-appcore``) with clear precedence.
- **Structured error handling**: Domain-specific exceptions with
  Markdown rendering for terminal display.


Installation 📦
===============================================================================

Method: Install Executable Script
-------------------------------------------------------------------------------

Install via the `uv <https://github.com/astral-sh/uv/blob/main/README.md>`_
``tool`` command:

::

    uv tool install copiertv

or, run directly with `uvx
<https://github.com/astral-sh/uv/blob/main/README.md>`_:

::

    uvx copiertv

Or, install via `pipx <https://pipx.pypa.io/stable/how-to/install-pipx.html>`_:

::

    pipx install copiertv

Method: Install Python Package
-------------------------------------------------------------------------------

Install via `uv <https://github.com/astral-sh/uv/blob/main/README.md>`_ ``pip``
command:

::

    uv pip install copiertv

Or, install via ``pip``:

::

    pip install copiertv


Usage
===============================================================================

Survey Variants
-------------------------------------------------------------------------------

List available template variants (reads answers directory from
configuration)::

    copiertv survey

Validate a Variant
-------------------------------------------------------------------------------

Validate a template variant::

    copiertv validate default

Preserve the generated project for inspection::

    copiertv validate --preserve default

Configuration File
-------------------------------------------------------------------------------

Create ``.auxiliary/configuration/copiertv/general.toml`` in your
template repository::

    [answers]
    directory = "data/copier"

    [[commands]]
    args = ["hatch", "env", "prune"]

    [[commands]]
    args = ["hatch", "--env", "develop", "run", "make-all"]

    [options]
    preserve = false
    unsafe = false

Commands support placeholder interpolation for paths::

    [[commands]]
    args = ["make", "check", "--source", "{project_directory}"]
    cwd = "{template_directory}"

Available placeholders: ``{template_directory}``, ``{project_directory}``,
``{temporary_directory}``, ``{variant}``.

For the complete list of recognized keys, absent-vs-empty semantics,
and configuration error rendering, see the `Configuration Reference
<https://emcd.github.io/copier-template-validator/stable/sphinx-html/examples/cli.html#configuration-reference>`_.


Contribution 🤝
===============================================================================

Contribution to this project is welcome! However, it must follow the `code of
conduct
<https://emcd.github.io/python-project-common/stable/sphinx-html/common/conduct.html>`_
for the project.

Please file bug reports and feature requests in the `issue tracker
<https://github.com/emcd/copier-template-validator/issues>`_ or submit `pull
requests <https://github.com/emcd/copier-template-validator/pulls>`_ to
improve the source code or documentation.

For development guidance and standards, please see the `development guide
<https://emcd.github.io/copier-template-validator/stable/sphinx-html/contribution.html#development>`_.


Additional Indicia
===============================================================================

.. image:: https://img.shields.io/github/last-commit/emcd/copier-template-validator
   :alt: GitHub last commit
   :target: https://github.com/emcd/copier-template-validator

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json
   :alt: Copier
   :target: https://github.com/copier-org/copier

.. image:: https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg
   :alt: Hatch
   :target: https://github.com/pypa/hatch

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
   :alt: pre-commit
   :target: https://github.com/pre-commit/pre-commit

.. image:: https://microsoft.github.io/pyright/img/pyright_badge.svg
   :alt: Pyright
   :target: https://microsoft.github.io/pyright

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :alt: Ruff
   :target: https://github.com/astral-sh/ruff

.. image:: https://img.shields.io/pypi/implementation/copiertv
   :alt: PyPI - Implementation
   :target: https://pypi.org/project/copiertv/

.. image:: https://img.shields.io/pypi/wheel/copiertv
   :alt: PyPI - Wheel
   :target: https://pypi.org/project/copiertv/


Other Projects by This Author 🌟
===============================================================================


* `python-absence <https://github.com/emcd/python-absence>`_ (`absence <https://pypi.org/project/absence/>`_ on PyPI) 

  🕳️ A Python library package which provides a **sentinel for absent values** - a falsey, immutable singleton that represents the absence of a value in contexts where ``None`` or ``False`` may be valid values.
* `python-accretive <https://github.com/emcd/python-accretive>`_ (`accretive <https://pypi.org/project/accretive/>`_ on PyPI) 

  🌌 A Python library package which provides **accretive data structures** - collections which can grow but never shrink.
* `python-classcore <https://github.com/emcd/python-classcore>`_ (`classcore <https://pypi.org/project/classcore/>`_ on PyPI) 

  🏭 A Python library package which provides **foundational class factories and decorators** for providing classes with attributes immutability and concealment and other custom behaviors.
* `python-detextive <https://github.com/emcd/python-detextive>`_ (`detextive <https://pypi.org/project/detextive/>`_ on PyPI) 

  🕵️ A Python library which provides consolidated text detection capabilities for reliable content analysis. Offers MIME type detection, character set detection, and line separator processing.
* `python-dynadoc <https://github.com/emcd/python-dynadoc>`_ (`dynadoc <https://pypi.org/project/dynadoc/>`_ on PyPI) 

  📝 A Python library package which bridges the gap between **rich annotations** and **automatic documentation generation** with configurable renderers and support for reusable fragments.
* `python-falsifier <https://github.com/emcd/python-falsifier>`_ (`falsifier <https://pypi.org/project/falsifier/>`_ on PyPI) 

  🎭 A very simple Python library package which provides a **base class for falsey objects** - objects that evaluate to ``False`` in boolean contexts.
* `python-frigid <https://github.com/emcd/python-frigid>`_ (`frigid <https://pypi.org/project/frigid/>`_ on PyPI) 

  🔒 A Python library package which provides **immutable data structures** - collections which cannot be modified after creation.
* `python-icecream-truck <https://github.com/emcd/python-icecream-truck>`_ (`icecream-truck <https://pypi.org/project/icecream-truck/>`_ on PyPI) 

  🍦 **Flavorful Debugging** - A Python library which enhances the powerful and well-known ``icecream`` package with flavored traces, configuration hierarchies, customized outputs, ready-made recipes, and more.
* `python-librovore <https://github.com/emcd/python-librovore>`_ (`librovore <https://pypi.org/project/librovore/>`_ on PyPI) 

  🐲 **Documentation Search Engine** - An intelligent documentation search and extraction tool that provides both a command-line interface for humans and an MCP (Model Context Protocol) server for AI agents. Search across Sphinx and MkDocs sites with fuzzy matching, extract clean markdown content, and integrate seamlessly with AI development workflows.
* `python-mimeogram <https://github.com/emcd/python-mimeogram>`_ (`mimeogram <https://pypi.org/project/mimeogram/>`_ on PyPI) 

  📨 A command-line tool for **exchanging collections of files with Large Language Models** - bundle multiple files into a single clipboard-ready document while preserving directory structure and metadata... good for code reviews, project sharing, and LLM interactions.
