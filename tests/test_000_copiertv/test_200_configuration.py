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


''' Tests for configuration module. '''


from pathlib import Path

from absence import absent

from copiertv.configuration import (
    Configuration,
    ValidationCommand,
    detect_project_root,
    interpolate_command,
    merge_configurations,
)


def test_100_validation_command_basic( ):
    ''' Creates command with args only. '''
    cmd = ValidationCommand( args = ( 'echo', 'hello' ) )
    assert cmd.args == ( 'echo', 'hello' )
    assert cmd.cwd is absent


def test_110_validation_command_with_cwd( ):
    ''' Creates command with args and cwd. '''
    cmd = ValidationCommand(
        args = ( 'make', 'test' ),
        cwd = '{project_directory}',
    )
    assert cmd.args == ( 'make', 'test' )
    assert cmd.cwd == '{project_directory}'


def test_120_configuration_defaults( ):
    ''' Has expected default values. '''
    config = Configuration( )
    assert config.answers_directory is absent
    assert config.commands == ( )
    assert config.template_directory is absent
    assert config.preserve is absent
    assert config.variant_filter is absent
    assert config.vcs_ref is absent
    assert config.unsafe is absent


def test_130_merge_configurations_override_answers( ):
    ''' Override answers_directory takes precedence. '''
    base = Configuration( answers_directory = Path( '/base' ) )
    override = Configuration( answers_directory = Path( '/override' ) )
    result = merge_configurations( base, override )
    assert result.answers_directory == Path( '/override' )


def test_140_merge_configurations_base_preserved( ):
    ''' Base values preserved when override is absent. '''
    base = Configuration( preserve = True )
    override = Configuration( )
    result = merge_configurations( base, override )
    assert result.preserve is True


def test_150_merge_configurations_override_preserve( ):
    ''' Override preserve takes precedence. '''
    base = Configuration( preserve = False )
    override = Configuration( preserve = True )
    result = merge_configurations( base, override )
    assert result.preserve is True


def test_155_merge_configurations_false_overrides_true( ):
    ''' Explicit false can override true. '''
    base = Configuration( preserve = True, unsafe = True )
    override = Configuration( preserve = False, unsafe = False )
    result = merge_configurations( base, override )
    assert result.preserve is False
    assert result.unsafe is False


def test_160_interpolate_command_basic( fs ):
    ''' Interpolates placeholders in args. '''
    template_directory = Path( '/template' )
    project_directory = Path( '/project' )
    temporary_directory = Path( '/temp' )
    cmd = ValidationCommand(
        args = ( 'check', '--source', '{project_directory}' ) )
    args, cwd = interpolate_command(
        cmd, template_directory, project_directory,
        temporary_directory, 'default' )
    assert args == ( 'check', '--source', str( project_directory ) )
    assert cwd == template_directory


def test_170_interpolate_command_cwd_placeholder( fs ):
    ''' Interpolates cwd placeholder. '''
    template_directory = Path( '/template' )
    project_directory = Path( '/project' )
    temporary_directory = Path( '/temp' )
    cmd = ValidationCommand(
        args = ( 'make', ),
        cwd = '{project_directory}',
    )
    _, cwd = interpolate_command(
        cmd, template_directory, project_directory,
        temporary_directory, 'default' )
    assert cwd == project_directory


def test_180_interpolate_command_variant_placeholder( fs ):
    ''' Interpolates variant placeholder. '''
    template_directory = Path( '/template' )
    project_directory = Path( '/project' )
    temporary_directory = Path( '/temp' )
    cmd = ValidationCommand(
        args = ( 'echo', '{variant}' ) )
    args, _ = interpolate_command(
        cmd, template_directory, project_directory,
        temporary_directory, 'maximum' )
    assert args == ( 'echo', 'maximum' )


def test_190_detect_project_root_git_found( fs ):
    ''' Returns directory containing .git. '''
    fs.create_dir( '/project/.git' )
    fs.create_dir( '/project/src' )
    import os
    os.chdir( '/project/src' )
    root = detect_project_root( )
    # Compare path parts for Windows compatibility.
    assert root.parts == Path( '/project' ).parts


def test_200_detect_project_root_no_vcs( fs ):
    ''' Returns CWD when no VCS marker found. '''
    fs.create_dir( '/plain/dir' )
    import os
    os.chdir( '/plain/dir' )
    root = detect_project_root( )
    # Compare path parts for Windows compatibility.
    assert root.parts == Path( '/plain/dir' ).parts
