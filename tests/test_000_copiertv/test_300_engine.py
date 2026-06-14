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


''' Tests for validation engine. '''


from pathlib import Path
from subprocess import CalledProcessError

import pytest

from copiertv import exceptions
from copiertv.configuration import (
    Configuration,
    ValidationCommand,
)
from copiertv.engine import (
    ValidationResult,
    copy_template,
    execute_validation_commands,
    survey_variants,
    validate_variant,
)


# --- SurveyVariants ---

def test_100_survey_variants_found( fs ):
    ''' Discovers variants from answers files. '''
    answers_dir = Path( '/project/data/copier' )
    fs.create_file( answers_dir / 'answers-default.yaml' )
    fs.create_file( answers_dir / 'answers-maximum.yaml' )
    result = survey_variants( answers_dir )
    assert result == ( 'default', 'maximum' )


def test_110_survey_variants_no_variants( fs ):
    ''' Returns empty tuple when no answers files exist. '''
    answers_dir = Path( '/project/data/copier' )
    fs.create_dir( answers_dir )
    result = survey_variants( answers_dir )
    assert result == ( )


def test_120_survey_variants_missing_directory( fs ):
    ''' Raises ConfigurationAbsence for missing directory. '''
    answers_dir = Path( '/nonexistent' )
    with pytest.raises( exceptions.ConfigurationAbsence ):
        survey_variants( answers_dir )


def test_130_survey_variants_ignores_non_matching( fs ):
    ''' Ignores files that do not match pattern. '''
    answers_dir = Path( '/project/data/copier' )
    fs.create_file( answers_dir / 'answers-default.yaml' )
    fs.create_file( answers_dir / 'README.md' )
    fs.create_file( answers_dir / 'other.yaml' )
    result = survey_variants( answers_dir )
    assert result == ( 'default', )


def test_140_survey_variants_sorted( fs ):
    ''' Returns variants in sorted order. '''
    answers_dir = Path( '/project/data/copier' )
    fs.create_file( answers_dir / 'answers-maximum.yaml' )
    fs.create_file( answers_dir / 'answers-alpha.yaml' )
    fs.create_file( answers_dir / 'answers-default.yaml' )
    result = survey_variants( answers_dir )
    assert result == ( 'alpha', 'default', 'maximum' )


# --- ValidationResult ---

def test_180_validation_result_render_success( tmp_path ):
    ''' Renders successful validation result. '''
    result = ValidationResult(
        variant = 'default',
        temporary_directory = tmp_path,
        items_attempted = 2,
        items_generated = 2,
        preserved = False,
    )
    lines = result.render_as_markdown( )
    assert len( lines ) == 4
    assert 'default' in lines[ 0 ]
    assert str( tmp_path ) in lines[ 1 ]
    assert '2/2' in lines[ 2 ]
    assert 'cleaned up' in lines[ 3 ]


def test_190_validation_result_render_preserved( tmp_path ):
    ''' Renders result with preserved directory. '''
    result = ValidationResult(
        variant = 'maximum',
        temporary_directory = tmp_path,
        items_attempted = 3,
        items_generated = 3,
        preserved = True,
    )
    lines = result.render_as_markdown( )
    assert len( lines ) == 4
    assert 'preserved' in lines[ 3 ].lower( )


# --- CopyTemplate ---

def test_200_copy_template_basic( fs ):
    ''' Calls copier with correct arguments. '''
    answers_path = Path( '/data/answers-default.yaml' )
    fs.create_file(
        answers_path, contents = 'name: test\n' )
    project_dir = Path( '/output' )
    template_dir = Path( '/template' )
    calls = [ ]
    def fake_copier( src, dst, **kwargs ):
        calls.append( ( src, dst, kwargs ) )
    copy_template(
        answers_path, project_dir, template_dir,
        copier = fake_copier,
    )
    assert len( calls ) == 1
    src, dst, kwargs = calls[ 0 ]
    assert src == str( template_dir )
    assert dst == project_dir
    assert kwargs[ 'data' ] == { 'name': 'test' }
    assert kwargs[ 'defaults' ] is True
    assert kwargs[ 'overwrite' ] is True
    assert kwargs[ 'quiet' ] is True


def test_210_copy_template_with_vcs_ref( fs ):
    ''' Forwards vcs_ref to copier. '''
    answers_path = Path( '/data/answers-default.yaml' )
    fs.create_file(
        answers_path, contents = 'name: test\n' )
    calls = [ ]
    def fake_copier( src, dst, **kwargs ):
        calls.append( kwargs )
    copy_template(
        answers_path, Path( '/output' ), Path( '/template' ),
        vcs_ref = 'v1.0',
        copier = fake_copier,
    )
    assert calls[ 0 ][ 'vcs_ref' ] == 'v1.0'


def test_220_copy_template_with_unsafe( fs ):
    ''' Forwards unsafe flag to copier. '''
    answers_path = Path( '/data/answers-default.yaml' )
    fs.create_file(
        answers_path, contents = 'name: test\n' )
    calls = [ ]
    def fake_copier( src, dst, **kwargs ):
        calls.append( kwargs )
    copy_template(
        answers_path, Path( '/output' ), Path( '/template' ),
        unsafe = True,
        copier = fake_copier,
    )
    assert calls[ 0 ][ 'unsafe' ] is True


def test_230_copy_template_copier_error( fs ):
    ''' Wraps copier exceptions as ConfigurationInvalidity. '''
    answers_path = Path( '/data/answers-default.yaml' )
    fs.create_file(
        answers_path, contents = 'name: test\n' )
    def failing_copier( src, dst, **kwargs ):
        raise RuntimeError( 'copier failed' )
    with pytest.raises( exceptions.ConfigurationInvalidity ):
        copy_template(
            answers_path, Path( '/output' ), Path( '/template' ),
            copier = failing_copier,
        )


# --- ValidateVariant ---

def test_240_validate_success( tmp_path ):
    ''' Returns ValidationResult on success. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    answers_file = answers_dir / 'answers-default.yaml'
    answers_file.write_text( 'name: test\n' )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = tmp_path / 'template',
    )
    def fake_copier( src, dst, **kwargs ): pass
    def fake_executor( args, **kwargs ): pass
    result = validate_variant(
        'default', config,
        copier = fake_copier,
        executor = fake_executor,
    )
    assert isinstance( result, ValidationResult )
    assert result.variant == 'default'
    assert result.items_attempted == 1


def test_250_validate_missing_answers_dir( ):
    ''' Raises ConfigurationInvalidity when answers dir absent. '''
    config = Configuration( )
    with pytest.raises( exceptions.ConfigurationInvalidity ):
        validate_variant( 'default', config )


def test_260_validate_missing_answers_file( tmp_path ):
    ''' Raises ConfigurationAbsence for missing variant file. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = tmp_path / 'template',
    )
    with pytest.raises( exceptions.ConfigurationAbsence ):
        validate_variant(
            'nonexistent', config,
            copier = lambda *a, **k: None,
            executor = lambda *a, **k: None,
        )


def test_270_validate_cmd_failure_propagates( tmp_path ):
    ''' Propagates ValidationCommandFailure from commands. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    answers_file = answers_dir / 'answers-default.yaml'
    answers_file.write_text( 'name: test\n' )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = tmp_path / 'template',
        commands = ( ValidationCommand( args = ( 'test', ) ), ),
    )
    def failing_executor( args, **kwargs ):
        raise CalledProcessError( 1, args )
    with pytest.raises( exceptions.ValidationCommandFailure ):
        validate_variant(
            'default', config,
            copier = lambda *a, **k: None,
            executor = failing_executor,
        )


def test_275_validate_cmd_failure_cleanup( tmp_path ):
    ''' Cleans up temp directory on command failure when preserve=False. '''
    import tempfile
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    answers_file = answers_dir / 'answers-default.yaml'
    answers_file.write_text( 'name: test\n' )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = tmp_path / 'template',
        commands = ( ValidationCommand( args = ( 'false', ) ), ),
    )
    system_temp = Path( tempfile.gettempdir( ) )
    temp_dirs_before = set( system_temp.glob( 'copiertv-*' ) )
    def failing_executor( args, **kwargs ):
        raise CalledProcessError( 1, args )
    with pytest.raises( exceptions.ValidationCommandFailure ):
        validate_variant(
            'default', config,
            copier = lambda *a, **k: None,
            executor = failing_executor,
        )
    temp_dirs_after = set( system_temp.glob( 'copiertv-*' ) )
    assert temp_dirs_before == temp_dirs_after


def test_280_validate_cleanup_on_success( tmp_path ):
    ''' Removes temp directory when preserve is False. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    answers_file = answers_dir / 'answers-default.yaml'
    answers_file.write_text( 'name: test\n' )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = tmp_path / 'template',
    )
    result = validate_variant(
        'default', config,
        copier = lambda *a, **k: None,
        executor = lambda *a, **k: None,
    )
    assert not result.temporary_directory.exists( )


def test_290_validate_preserves_on_config( tmp_path ):
    ''' Keeps temp directory when preserve is True. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    answers_file = answers_dir / 'answers-default.yaml'
    answers_file.write_text( 'name: test\n' )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = tmp_path / 'template',
        preserve = True,
    )
    result = validate_variant(
        'default', config,
        copier = lambda *a, **k: None,
        executor = lambda *a, **k: None,
    )
    assert result.temporary_directory.exists( )


def test_295_validate_cleanup_on_exception( tmp_path ):
    ''' Removes temp directory when copier raises unexpected error. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    answers_file = answers_dir / 'answers-default.yaml'
    answers_file.write_text( 'name: test\n' )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = tmp_path / 'template',
    )
    temp_dirs_before = set( tmp_path.parent.glob( 'copiertv-*' ) )
    def failing_copier( *a, **k ):
        raise RuntimeError( 'unexpected' )
    with pytest.raises( exceptions.ConfigurationInvalidity ):
        validate_variant(
            'default', config,
            copier = failing_copier,
            executor = lambda *a, **k: None,
        )
    temp_dirs_after = set( tmp_path.parent.glob( 'copiertv-*' ) )
    assert temp_dirs_before == temp_dirs_after


def test_296_validate_missing_template_dir( tmp_path ):
    ''' Raises ConfigurationInvalidity when template directory absent. '''
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    answers_file = answers_dir / 'answers-default.yaml'
    answers_file.write_text( 'name: test\n' )
    config = Configuration(
        answers_directory = answers_dir,
        # template_directory is absent
    )
    with pytest.raises( exceptions.ConfigurationInvalidity ):
        validate_variant(
            'default', config,
            copier = lambda *a, **k: None,
            executor = lambda *a, **k: None,
        )


def test_297_validate_preserve_skips_cleanup( tmp_path ):
    ''' Skips cleanup when preserve=True and exception occurs. '''
    import tempfile
    answers_dir = tmp_path / 'data'
    answers_dir.mkdir( )
    answers_file = answers_dir / 'answers-default.yaml'
    answers_file.write_text( 'name: test\n' )
    config = Configuration(
        answers_directory = answers_dir,
        template_directory = tmp_path / 'template',
        preserve = True,
    )
    system_temp = Path( tempfile.gettempdir( ) )
    temp_dirs_before = set( system_temp.glob( 'copiertv-*' ) )
    def failing_copier( *a, **k ):
        raise RuntimeError( 'unexpected' )
    with pytest.raises( exceptions.ConfigurationInvalidity ):
        validate_variant(
            'default', config,
            copier = failing_copier,
            executor = lambda *a, **k: None,
        )
    temp_dirs_after = set( system_temp.glob( 'copiertv-*' ) )
    assert len( temp_dirs_after ) > len( temp_dirs_before )


# --- ExecuteValidationCommands ---

def test_300_exec_commands_runs_all( tmp_path ):
    ''' Executes each command in sequence. '''
    config = Configuration(
        commands = (
            ValidationCommand( args = ( 'echo', 'one' ) ),
            ValidationCommand( args = ( 'echo', 'two' ) ),
        ),
    )
    execute_validation_commands(
        config,
        template_directory = tmp_path,
        project_directory = tmp_path / 'project',
        temporary_directory = tmp_path / 'temp',
        variant = 'default',
    )


def test_310_exec_commands_no_commands( tmp_path ):
    ''' Does nothing when no commands configured. '''
    config = Configuration( )
    execute_validation_commands(
        config,
        template_directory = tmp_path,
        project_directory = tmp_path / 'project',
        temporary_directory = tmp_path / 'temp',
        variant = 'default',
    )
