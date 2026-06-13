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


import pytest

from copiertv import exceptions
from copiertv.cli import _survey, _validate, execute, intercept_errors
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
