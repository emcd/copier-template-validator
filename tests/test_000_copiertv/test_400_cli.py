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
from copiertv.cli import _survey, _validate, intercept_errors
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
    assert 'Could not locate configuration' in captured.out


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
async def test_130_survey_prints_variants( capsys, mocker, tmp_path ):
    ''' Prints discovered variants to stdout. '''
    mocker.patch(
        'copiertv.engine.survey_variants',
        return_value = ( 'alpha', 'default' ),
    )
    config = Configuration( answers_directory = tmp_path )
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
async def test_150_validate_prints_result( capsys, mocker, tmp_path ):
    ''' Prints validation result markdown to stdout. '''
    from copiertv.engine import ValidationResult
    mock_result = ValidationResult(
        variant = 'default',
        temporary_directory = tmp_path,
        items_attempted = 2,
        items_generated = 2,
        preserved = False,
    )
    mocker.patch(
        'copiertv.engine.validate_variant',
        return_value = mock_result,
    )
    config = Configuration( )
    await _validate( 'default', config )
    captured = capsys.readouterr( )
    assert 'Validation complete' in captured.out
    assert 'default' in captured.out


@pytest.mark.asyncio
async def test_160_validate_propagates_errors( mocker ):
    ''' Propagates exceptions from validate_variant. '''
    mocker.patch(
        'copiertv.engine.validate_variant',
        side_effect = exceptions.ConfigurationAbsence( ),
    )
    config = Configuration( )
    with pytest.raises( exceptions.ConfigurationAbsence ):
        await _validate( 'default', config )


# --- Execute ---

def test_170_execute_runs( mocker ):
    ''' Calls asyncio.run on _main. '''
    mock_run = mocker.patch( 'asyncio.run' )
    from copiertv.cli import execute
    execute( )
    mock_run.assert_called_once( )


def test_180_execute_system_exit( mocker ):
    ''' Re-raises SystemExit. '''
    mocker.patch( 'asyncio.run', side_effect = SystemExit( 1 ) )
    from copiertv.cli import execute
    with pytest.raises( SystemExit ):
        execute( )


def test_190_execute_base_exception( mocker ):
    ''' Converts BaseException to SystemExit(1). '''
    mocker.patch(
        'asyncio.run',
        side_effect = KeyboardInterrupt( ),
    )
    from copiertv.cli import execute
    with pytest.raises( SystemExit ) as exc_info:
        execute( )
    assert exc_info.value.code == 1
