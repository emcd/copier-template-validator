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


''' Integration tests for copiertv. '''


import os
from pathlib import Path

import pytest

from copiertv import exceptions
from copiertv.configuration import (
    Configuration,
    ValidationCommand,
    acquire_configuration,
    parse_toml_configuration,
)
from copiertv.engine import (
    _execute_command,
    copy_template,
    validate_variant,
)


DATA_DIRECTORY = Path( __file__ ).parent.parent / 'data'
TEMPLATES_DIRECTORY = DATA_DIRECTORY / 'templates'
ANSWERS_DIRECTORY = DATA_DIRECTORY / 'answers'


# --- CopyTemplate ---

def test_100_copy_template_real( tmp_path ):
    ''' Copies a real Copier template to a temporary directory. '''
    template_dir = TEMPLATES_DIRECTORY / 'minimal'
    answers_file = ANSWERS_DIRECTORY / 'answers-default.yaml'
    project_dir = tmp_path / 'output'
    copy_template( answers_file, project_dir, template_dir )
    output_file = project_dir / 'project_name.txt'
    assert output_file.exists( )
    assert output_file.read_text( ).strip( ) == 'testproject'


def test_110_copy_template_with_vcs_ref( tmp_path ):
    ''' Copies template with a vcs_ref parameter. '''
    template_dir = TEMPLATES_DIRECTORY / 'minimal'
    answers_file = ANSWERS_DIRECTORY / 'answers-default.yaml'
    project_dir = tmp_path / 'output'
    copy_template(
        answers_file, project_dir, template_dir, vcs_ref = 'HEAD' )
    output_file = project_dir / 'project_name.txt'
    assert output_file.exists( )


# --- ExecuteCommand ---

def test_120_execute_command_real_success( tmp_path ):
    ''' Runs a real command successfully. '''
    _execute_command(
        ( 'echo', 'hello' ),
        working_directory = tmp_path,
        temporary_directory = tmp_path,
        preserve = False,
    )


def test_130_execute_command_real_failure( tmp_path ):
    ''' Raises ValidationCommandFailure for non-zero exit. '''
    with pytest.raises( exceptions.ValidationCommandFailure ):
        _execute_command(
            ( 'false', ),
            working_directory = tmp_path,
            temporary_directory = tmp_path,
            preserve = False,
        )


def test_140_execute_command_real_not_found( tmp_path ):
    ''' Raises ConfigurationInvalidity for missing command. '''
    with pytest.raises( exceptions.ConfigurationInvalidity ):
        _execute_command(
            ( 'nonexistent_command_xyz', ),
            working_directory = tmp_path,
            temporary_directory = tmp_path,
            preserve = False,
        )


# --- ValidateVariant ---

def test_150_validate_variant_end_to_end( tmp_path ):
    ''' Validates a variant with real template and commands. '''
    config = Configuration(
        answers_directory = ANSWERS_DIRECTORY,
        template_directory = TEMPLATES_DIRECTORY / 'minimal',
        commands = (
            ValidationCommand( args = ( 'true', ) ),
        ),
    )
    result = validate_variant( 'default', config )
    assert result.variant == 'default'
    assert result.items_attempted == 2
    assert result.items_generated == 2


def test_160_validate_variant_command_failure( tmp_path ):
    ''' Propagates ValidationCommandFailure from real command. '''
    config = Configuration(
        answers_directory = ANSWERS_DIRECTORY,
        template_directory = TEMPLATES_DIRECTORY / 'minimal',
        commands = (
            ValidationCommand( args = ( 'false', ) ),
        ),
    )
    with pytest.raises( exceptions.ValidationCommandFailure ):
        validate_variant( 'default', config )


# --- ParseTomlConfiguration ---

def test_170_parse_toml_configuration_real( fs ):
    ''' Parses a real TOML configuration file. '''
    config_path = Path( '/project/copiertv.toml' )
    fs.create_file(
        config_path,
        contents = (
            '[answers]\n'
            'directory = "data/copier"\n'
            '\n'
            '[[commands]]\n'
            'args = ["make", "test"]\n'
            '\n'
            '[options]\n'
            'preserve = true\n'
            'unsafe = true\n'
            'vcs-ref = "HEAD"\n'
        ),
    )
    config = parse_toml_configuration( config_path )
    assert config.answers_directory == Path( 'data/copier' )
    assert len( config.commands ) == 1
    assert config.commands[ 0 ].args == ( 'make', 'test' )
    assert config.preserve is True
    assert config.unsafe is True
    assert config.vcs_ref == 'HEAD'


def test_180_parse_toml_configuration_missing_file( fs ):
    ''' Raises FileOperationFailure for missing TOML file. '''
    with pytest.raises( exceptions.FileOperationFailure ):
        parse_toml_configuration( Path( '/nonexistent.toml' ) )


def test_190_parse_toml_configuration_invalid( fs ):
    ''' Raises DataInvalidity for malformed TOML. '''
    config_path = Path( '/bad.toml' )
    fs.create_file( config_path, contents = '[[[' )
    with pytest.raises( exceptions.DataInvalidity ):
        parse_toml_configuration( config_path )


# --- AcquireConfiguration ---

def test_200_acquire_configuration_project_config( fs ):
    ''' Loads project configuration from .auxiliary directory. '''
    fs.create_dir( '/project/.auxiliary/configuration/copiertv' )
    fs.create_file(
        '/project/.auxiliary/configuration/copiertv/general.toml',
        contents = '[answers]\ndirectory = "project/dir"\n',
    )
    fs.create_dir( '/project/.git' )
    os.chdir( '/project' )
    config = acquire_configuration( { } )
    assert config.answers_directory == Path( 'project/dir' )


def test_210_acquire_configuration_cli_overrides( ):
    ''' CLI overrides take precedence over file config. '''
    appcore_config = {
        'answers': { 'directory': 'file/dir' },
        'options': { 'preserve': False },
    }
    cli_config = Configuration( preserve = True )
    config = acquire_configuration( appcore_config, cli_config )
    assert config.answers_directory == Path( 'file/dir' )
    assert config.preserve is True


def test_220_acquire_configuration_project_config_override( fs ):
    ''' Uses project-configuration path from appcore config. '''
    fs.create_file(
        '/custom/config.toml',
        contents = '[answers]\ndirectory = "custom/dir"\n',
    )
    appcore_config = {
        'options': { 'project-configuration': '/custom/config.toml' },
    }
    config = acquire_configuration( appcore_config )
    assert config.answers_directory == Path( 'custom/dir' )
