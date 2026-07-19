# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Tests for command-line interface. '''


import io
import os
import subprocess
import sys

from pathlib import Path

import pytest

from copiertv import exceptions
from copiertv.cli import (
    _RENDERING_REPLACEMENTS,
    _adapt_rendered_lines,
    _print_rendered_lines,
    _survey,
    _validate,
    execute,
    intercept_errors,
)
from copiertv.configuration import Configuration

# --- InterceptErrors ---

@pytest.mark.asyncio
async def test_100_intercept_errors_omnierror( capsys ):
    ''' Catches Omnierror, prints markdown, raises SystemExit. '''
    @intercept_errors( )
    async def failing_function( ):
        raise exceptions.ConfigurationAbsence( )
    with pytest.raises( SystemExit ) as exc_info:
        await failing_function( )
    assert exc_info.value.code == 1
    captured = capsys.readouterr( )
    assert captured.out


@pytest.mark.asyncio
async def test_110_intercept_errors_passthrough_non_omnierror( ):
    ''' Re-raises non-Omnierror exceptions. '''
    @intercept_errors( )
    async def failing_function( ):
        raise ValueError( 'not an Omnierror' )
    with pytest.raises( ValueError, match = 'not an Omnierror' ):
        await failing_function( )


@pytest.mark.asyncio
async def test_120_intercept_errors_success( ):
    ''' Passes through when no exception raised. '''
    @intercept_errors( )
    async def success_function( ):
        pass
    await success_function( )


# --- Survey ---

@pytest.mark.asyncio
async def test_130_survey_prints_variants( capsys, tmp_path ):
    ''' Prints discovered variants to stdout. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    ( answers_dir / 'answers-alpha.yaml' ).write_text( '' )
    ( answers_dir / 'answers-default.yaml' ).write_text( '' )
    config = Configuration( answers_directory = answers_dir )
    await _survey( config )
    captured = capsys.readouterr( )
    assert 'alpha' in captured.out
    assert 'default' in captured.out


@pytest.mark.asyncio
async def test_140_survey_missing_answers_dir( ):
    ''' Raises ConfigurationInvalidity when answers dir absent. '''
    config = Configuration( )
    with pytest.raises( exceptions.ConfigurationInvalidity ):
        await _survey( config )


# --- Validate ---

@pytest.mark.asyncio
async def test_150_validate_prints_result( capsys, tmp_path ):
    ''' Prints validation result markdown to stdout. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    ( answers_dir / 'answers-default.yaml' ).write_text(
        'name: test\n' )
    template_dir = tmp_path / 'template'
    template_dir.mkdir( )
    ( template_dir / 'copier.yml' ).write_text(
        'project_name:\n  type: str\n  default: myproject\n' )
    ( template_dir / 'output.txt.jinja' ).write_text(
        '{{ project_name }}\n' )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = template_dir,
    )
    await _validate( 'default', config )
    captured = capsys.readouterr( )
    assert 'Validation complete' in captured.out
    assert 'default' in captured.out


@pytest.mark.asyncio
async def test_160_validate_propagates_errors( ):
    ''' Propagates exceptions from validate_variant. '''
    config = Configuration( )
    with pytest.raises( exceptions.ConfigurationInvalidity ):
        await _validate( 'default', config )


# --- Execute ---

def test_170_execute_callable( ):
    ''' execute is callable. '''
    assert callable( execute )


# --- Module subprocess tests ---


def _isolated_env( base ):
    ''' Builds a subprocess environment that points user-level
        configuration directories at ``base``, isolating the
        subprocess from any developer / runner user-level
        configuration. ``base`` is created if missing.

        On Linux and most BSDs, ``XDG_CONFIG_HOME`` controls
        ``PlatformDirs`` resolution; on macOS, ``PlatformDirs``
        falls back to ``HOME``-derived paths (specifically
        ``~/Library/Application Support``); on Windows,
        ``APPDATA`` / ``LOCALAPPDATA`` take over. The helper
        sets all four so the subprocess is isolated regardless
        of which variable the host platform actually consults.
    '''
    base = Path( base )
    base.mkdir( parents = True, exist_ok = True )
    for name in ( 'home', 'xdg', 'appdata', 'localappdata' ):
        ( base / name ).mkdir( parents = True, exist_ok = True )
    env = os.environ.copy( )
    env[ 'HOME' ] = str( base / 'home' )
    env[ 'XDG_CONFIG_HOME' ] = str( base / 'xdg' )
    env[ 'APPDATA' ] = str( base / 'appdata' )
    env[ 'LOCALAPPDATA' ] = str( base / 'localappdata' )
    return env


def _run_cli( *args, cwd ):
    ''' Invokes the CLI as ``python -m copiertv`` and returns
        the CompletedProcess. ``cwd`` is required and is used as
        both the working directory and the root of an isolated
        user-config environment, so the subprocess does not read
        any developer / runner user-level configuration.
    '''
    return subprocess.run(  # noqa: S603
        [ sys.executable, '-m', 'copiertv', *args ],
        capture_output = True, text = True,
        timeout = 30, check = False,
        cwd = str( cwd ),
        env = _isolated_env( cwd ),
    )


def test_200_cli_help( tmp_path ):
    ''' ``python -m copiertv --help`` exits 0 and lists subcommands. '''
    result = _run_cli( '--help', cwd = tmp_path )
    assert result.returncode == 0, (
        f'stderr:\n{result.stderr}\nstdout:\n{result.stdout}' )
    assert 'survey' in result.stdout
    assert 'validate' in result.stdout


def test_210_cli_version( tmp_path ):
    ''' ``python -m copiertv --version`` exits 0 and prints version. '''
    result = _run_cli( '--version', cwd = tmp_path )
    assert result.returncode == 0, (
        f'stderr:\n{result.stderr}\nstdout:\n{result.stdout}' )
    assert 'copiertv' in result.stdout.lower( )
    assert '1.0' in result.stdout


def test_220_cli_default_subcommand_without_config( tmp_path ):
    ''' With no subcommand the application defaults to ``survey``;
        ``survey`` without answers configuration fails with a
        non-zero exit and surfaces an answers or configuration
        error message.
    '''
    result = _run_cli( cwd = tmp_path )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert (
        'answers' in combined.lower( )
        or 'configuration' in combined.lower( )
    )


def test_225_cli_default_subcommand_with_config( tmp_path ):
    ''' With a complete project configuration the no-subcommand
        invocation runs ``survey`` (the default subcommand) and
        exits 0 listing the discovered variants. A ``.git``
        marker is created in ``tmp_path`` so the configuration
        reader's project-root detection resolves to ``tmp_path``
        rather than walking up to a parent directory.
    '''
    ( tmp_path / '.git' ).mkdir( )
    answers_dir = tmp_path / 'answers'
    answers_dir.mkdir( )
    ( answers_dir / 'answers-default.yaml' ).write_text( '' )
    config_dir = (
        tmp_path / '.auxiliary' / 'configuration' / 'copiertv' )
    config_dir.mkdir( parents = True )
    ( config_dir / 'general.toml' ).write_text(
        f'[answers]\ndirectory = "{answers_dir}"\n'
    )
    result = _run_cli( cwd = tmp_path )
    assert result.returncode == 0, (
        f'stderr:\n{result.stderr}\nstdout:\n{result.stdout}' )
    assert 'default' in result.stdout


def test_230_cli_survey_without_config( tmp_path ):
    ''' ``survey`` with no answers configuration exits non-zero and
        renders an error via the Markdown error interface.
    '''
    result = _run_cli( 'survey', cwd = tmp_path )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert (
        'answers' in combined.lower( )
        or 'configuration' in combined.lower( )
    )


def test_240_cli_validate_without_config( tmp_path ):
    ''' ``validate`` with no configuration exits non-zero. '''
    result = _run_cli( 'validate', 'default', cwd = tmp_path )
    assert result.returncode != 0


# --- Encoding adaptation helpers ---


def _text_stream( encoding ):
    ''' Wraps a BytesIO in a TextIOWrapper with the given encoding. '''
    return io.TextIOWrapper( io.BytesIO( ), encoding = encoding )


def test_300_adapt_rendered_lines_utf8_unchanged( ):
    ''' UTF-8 streams receive the lines unchanged. '''
    sample = (
        '\u2705 Validation complete for \'default\' variant:',
        ' * Items: 1 of 1 generated',
        '\u274c Invalid configuration: answers directory',
    )
    assert _adapt_rendered_lines( sample, 'utf-8' ) == sample


def test_310_adapt_rendered_lines_cp1252_substitutes_decorations( ):
    ''' cp1252 streams receive ASCII labels for all five decorations. '''
    sample = (
        '\u2705 ok',                          # success
        '\u274c fail',                         # error
        '\U0001f4c1 folder',                  # folder
        '\U0001f5d1\ufe0f cleanup-with-vs',   # trash with VS-16
        '\U0001f5d1 cleanup-bare',            # trash without VS-16
    )
    adapted = _adapt_rendered_lines( sample, 'cp1252' )
    assert adapted[ 0 ] == '[OK] ok'
    assert adapted[ 1 ] == '[ERROR] fail'
    assert adapted[ 2 ] == '[FILES] folder'
    assert adapted[ 3 ] == '[CLEANUP] cleanup-with-vs'
    assert adapted[ 4 ] == '[CLEANUP] cleanup-bare'


def test_320_adapt_rendered_lines_ascii_substitutes( ):
    ''' ASCII streams also receive ASCII labels. '''
    sample = ( '\u2705 done', '\u274c broken' )
    adapted = _adapt_rendered_lines( sample, 'ascii' )
    assert adapted[ 0 ] == '[OK] done'
    assert adapted[ 1 ] == '[ERROR] broken'


def test_330_adapt_rendered_lines_user_text_backslashreplace( ):
    ''' Non-decoration text that still cannot encode is preserved
        via ``backslashreplace`` rather than silently dropped.
    '''
    sample = ( '\u274c failure on /tmp/路径/内/部', )
    adapted = _adapt_rendered_lines( sample, 'ascii' )
    assert '[ERROR]' in adapted[ 0 ]
    assert 'failure on ' in adapted[ 0 ]
    # All remaining characters must be safely encodable as ASCII.
    adapted[ 0 ].encode( 'ascii' )


def test_340_adapt_rendered_lines_no_encoding_passes_through( ):
    ''' Streams without an encoding attribute (e.g., ``StringIO``)
        pass lines through unchanged so test harness stays
        Unicode-clean.
    '''
    sample = ( '\u2705 keep \u274c', )
    assert _adapt_rendered_lines( sample, None ) == sample


def test_350_adapt_rendered_lines_unknown_encoding_substitutes( ):
    ''' An unknown encoding name falls through to substitutions
        and backslashreplace rather than raising.
    '''
    sample = ( '\u2705 ok', )
    adapted = _adapt_rendered_lines( sample, 'not-a-real-codec' )
    assert '[OK]' in adapted[ 0 ]


def test_360_replacements_cover_five_decorations( ):
    ''' The replacement table covers every decorated literal used
        in the rendered output, including the bare and
        variation-selector-16 trash forms.
    '''
    expected = {
        '\u2705', '\u274c', '\U0001f4c1',
        '\U0001f5d1\ufe0f', '\U0001f5d1',
    }
    seen = { src for src, _label in _RENDERING_REPLACEMENTS }
    assert seen == expected


def test_370_print_rendered_lines_adapts_to_stream( ):
    ''' ``_print_rendered_lines`` adapts to the supplied stream's
        encoding and writes to it.
    '''
    stream = _text_stream( 'cp1252' )
    _print_rendered_lines( ( '\u2705 done', ), stream = stream )
    stream.seek( 0 )
    written = stream.read( )
    assert written == '[OK] done\n'


def test_380_print_rendered_lines_resolves_sys_stdout_each_call( ):
    ''' ``_print_rendered_lines`` resolves ``sys.stdout`` at call
        time, not as a default argument, so changes to ``sys.stdout``
        between calls are respected.
    '''
    original_stdout = sys.stdout
    try:
        stream = _text_stream( 'cp1252' )
        sys.stdout = stream
        _print_rendered_lines( ( '\u2705 first', ) )
        _print_rendered_lines( ( '\u274c second', ) )
        sys.stdout = original_stdout
        stream.seek( 0 )
        written = stream.read( )
        assert written == '[OK] first\n[ERROR] second\n'
    finally:
        sys.stdout = original_stdout


# --- Subprocess regression for the Windows cp1252 failure ---


def test_390_subprocess_cp1252_default_survey_no_unicode_encode_error( ):
    ''' Reproduces the original Windows cp1252 failure on every
        host by forcing the subprocess interpreter to use cp1252
        via ``PYTHONIOENCODING``. Asserts nonzero exit, nonempty
        output, the ``[ERROR]`` fallback label, and no raised
        ``UnicodeEncodeError``.
    '''
    import tempfile
    with tempfile.TemporaryDirectory( ) as td:
        base = Path( td )
        ( base / 'home' ).mkdir( )
        ( base / 'xdg' ).mkdir( )
        ( base / 'appdata' ).mkdir( )
        ( base / 'localappdata' ).mkdir( )
        env = os.environ.copy( )
        env[ 'HOME' ] = str( base / 'home' )
        env[ 'XDG_CONFIG_HOME' ] = str( base / 'xdg' )
        env[ 'APPDATA' ] = str( base / 'appdata' )
        env[ 'LOCALAPPDATA' ] = str( base / 'localappdata' )
        env[ 'PYTHONIOENCODING' ] = 'cp1252'
        env.pop( 'PYTHONUTF8', None )
        result = subprocess.run(
            [ sys.executable, '-m', 'copiertv' ],
            capture_output = True, text = True,
            timeout = 30, check = False,
            cwd = str( base ),
            env = env,
        )
    assert result.returncode != 0
    assert 'UnicodeEncodeError' not in result.stderr
    assert 'UnicodeEncodeError' not in result.stdout
    combined = result.stdout + result.stderr
    assert combined.strip( ), 'subprocess produced no output'
    assert '[ERROR]' in combined
