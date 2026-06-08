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
    _parse_configuration_data,
    detect_project_root,
    interpolate_command,
    merge_configurations,
)


class TestValidationCommand:
    ''' Tests for ValidationCommand dataclass. '''

    def test_000_basic( self ):
        ''' Creates command with args only. '''
        cmd = ValidationCommand( args = ( 'echo', 'hello' ) )
        assert cmd.args == ( 'echo', 'hello' )
        assert cmd.cwd is absent

    def test_010_with_cwd( self ):
        ''' Creates command with args and cwd. '''
        cmd = ValidationCommand(
            args = ( 'make', 'test' ),
            cwd = '{project_dir}',
        )
        assert cmd.args == ( 'make', 'test' )
        assert cmd.cwd == '{project_dir}'


class TestConfiguration:
    ''' Tests for Configuration dataclass. '''

    def test_000_defaults( self ):
        ''' Has expected default values. '''
        config = Configuration( )
        assert config.answers_directory is absent
        assert config.commands == ( )
        assert config.template_directory is absent
        assert config.preserve is False
        assert config.variant_filter is absent
        assert config.vcs_ref is absent
        assert config.unsafe is False


class TestParseConfigurationData:
    ''' Tests for TOML configuration parsing. '''

    def test_000_empty( self ):
        ''' Parses empty configuration. '''
        config = _parse_configuration_data( { } )
        assert config.answers_directory is absent
        assert config.commands == ( )

    def test_010_answers_directory( self ):
        ''' Parses answers directory. '''
        data = { 'answers': { 'directory': 'data/copier' } }
        config = _parse_configuration_data( data )
        assert config.answers_directory == Path( 'data/copier' )

    def test_020_commands( self ):
        ''' Parses validation commands. '''
        data = {
            'commands': [
                { 'args': [ 'make', 'test' ] },
                { 'args': [ 'lint' ], 'cwd': '{project_dir}' },
            ]
        }
        config = _parse_configuration_data( data )
        assert len( config.commands ) == 2
        assert config.commands[ 0 ].args == ( 'make', 'test' )
        assert config.commands[ 1 ].cwd == '{project_dir}'

    def test_030_options( self ):
        ''' Parses options section. '''
        data = {
            'options': {
                'preserve': True,
                'unsafe': True,
                'vcs-ref': 'HEAD',
                'variants': [ 'default', 'maximum' ],
            }
        }
        config = _parse_configuration_data( data )
        assert config.preserve is True
        assert config.unsafe is True
        assert config.vcs_ref == 'HEAD'
        assert config.variant_filter == ( 'default', 'maximum' )


class TestMergeConfigurations:
    ''' Tests for configuration merging. '''

    def test_000_override_answers( self ):
        ''' Override answers_directory takes precedence. '''
        base = Configuration( answers_directory = Path( '/base' ) )
        override = Configuration( answers_directory = Path( '/override' ) )
        result = merge_configurations( base, override )
        assert result.answers_directory == Path( '/override' )

    def test_010_base_preserved( self ):
        ''' Base values preserved when override is absent. '''
        base = Configuration( preserve = True )
        override = Configuration( )
        result = merge_configurations( base, override )
        assert result.preserve is True

    def test_020_override_preserve( self ):
        ''' Override preserve takes precedence. '''
        base = Configuration( preserve = False )
        override = Configuration( preserve = True )
        result = merge_configurations( base, override )
        assert result.preserve is True


class TestInterpolateCommand:
    ''' Tests for command interpolation. '''

    def test_000_basic( self, fs ):
        ''' Interpolates placeholders in args. '''
        template_dir = Path( '/template' )
        project_dir = Path( '/project' )
        temp_dir = Path( '/temp' )
        cmd = ValidationCommand(
            args = ( 'check', '--source', '{project_dir}' ) )
        args, cwd = interpolate_command(
            cmd, template_dir, project_dir, temp_dir, 'default' )
        assert args == ( 'check', '--source', '/project' )
        assert cwd == template_dir

    def test_010_cwd_placeholder( self, fs ):
        ''' Interpolates cwd placeholder. '''
        template_dir = Path( '/template' )
        project_dir = Path( '/project' )
        temp_dir = Path( '/temp' )
        cmd = ValidationCommand(
            args = ( 'make', ),
            cwd = '{project_dir}',
        )
        _, cwd = interpolate_command(
            cmd, template_dir, project_dir, temp_dir, 'default' )
        assert cwd == project_dir

    def test_020_variant_placeholder( self, fs ):
        ''' Interpolates variant placeholder. '''
        template_dir = Path( '/template' )
        project_dir = Path( '/project' )
        temp_dir = Path( '/temp' )
        cmd = ValidationCommand(
            args = ( 'echo', '{variant}' ) )
        args, _ = interpolate_command(
            cmd, template_dir, project_dir, temp_dir, 'maximum' )
        assert args == ( 'echo', 'maximum' )


class TestDetectProjectRoot:
    ''' Tests for project root detection. '''

    def test_000_git_found( self, fs ):
        ''' Returns directory containing .git. '''
        fs.create_dir( '/project/.git' )
        fs.create_dir( '/project/src' )
        import os
        os.chdir( '/project/src' )
        root = detect_project_root( )
        assert root == Path( '/project' )

    def test_010_no_vcs( self, fs ):
        ''' Returns CWD when no VCS marker found. '''
        fs.create_dir( '/plain/dir' )
        import os
        os.chdir( '/plain/dir' )
        root = detect_project_root( )
        assert root == Path( '/plain/dir' )
