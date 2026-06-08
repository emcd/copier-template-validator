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


''' Tests for exception hierarchy. '''


from pathlib import Path

from copiertv.exceptions import (
    ConfigurationAbsence,
    ConfigurationInvalidity,
    DataInvalidity,
    DependencyAbsence,
    FileOperationFailure,
    Omnierror,
    ValidationCommandFailure,
)


class TestConfigurationAbsence:
    ''' Tests for ConfigurationAbsence. '''

    def test_000_without_location( self ):
        ''' Has default message without location. '''
        exc = ConfigurationAbsence( )
        assert 'Could not locate' in str( exc )

    def test_010_with_location( self ):
        ''' Includes location in message. '''
        exc = ConfigurationAbsence( Path( '/some/path' ) )
        assert '/some/path' in str( exc )

    def test_020_render( self ):
        ''' Renders as Markdown lines. '''
        exc = ConfigurationAbsence( )
        lines = exc.render_as_markdown( )
        assert len( lines ) == 3
        assert '\u274c' in lines[ 0 ]


class TestConfigurationInvalidity:
    ''' Tests for ConfigurationInvalidity. '''

    def test_000_default( self ):
        ''' Has default message. '''
        exc = ConfigurationInvalidity( )
        assert 'Invalid configuration' in str( exc )

    def test_010_with_reason( self ):
        ''' Includes reason in message. '''
        exc = ConfigurationInvalidity( 'bad value' )
        assert 'bad value' in str( exc )

    def test_020_with_exception( self ):
        ''' Wraps exception as reason. '''
        cause = ValueError( 'oops' )
        exc = ConfigurationInvalidity( cause )
        assert 'oops' in str( exc )


class TestDependencyAbsence:
    ''' Tests for DependencyAbsence. '''

    def test_000_message( self ):
        ''' Includes package name in message. '''
        exc = DependencyAbsence( 'copier' )
        assert 'copier' in str( exc )
        assert 'not installed' in str( exc )


class TestDataInvalidity:
    ''' Tests for DataInvalidity. '''

    def test_000_message( self ):
        ''' Includes path and cause in message. '''
        exc = DataInvalidity( Path( '/data.yaml' ), 'Invalid YAML' )
        assert '/data.yaml' in str( exc )
        assert 'Invalid YAML' in str( exc )


class TestFileOperationFailure:
    ''' Tests for FileOperationFailure. '''

    def test_000_message( self ):
        ''' Includes path and operation in message. '''
        exc = FileOperationFailure( Path( '/file' ), 'read' )
        assert '/file' in str( exc )
        assert 'read' in str( exc )


class TestValidationCommandFailure:
    ''' Tests for ValidationCommandFailure. '''

    def test_000_basic( self ):
        ''' Stores command and return code. '''
        exc = ValidationCommandFailure(
            ( 'make', 'test' ), 1 )
        assert exc.command == ( 'make', 'test' )
        assert exc.returncode == 1

    def test_010_with_temp_dir( self, tmp_path ):
        ''' Includes temp directory in message. '''
        exc = ValidationCommandFailure(
            ( 'make', 'test' ), 1, tmp_path )
        lines = exc.render_as_markdown( )
        assert len( lines ) == 2
        assert str( tmp_path ) in lines[ 1 ]

    def test_020_without_temp_dir( self ):
        ''' Renders without temp directory. '''
        exc = ValidationCommandFailure(
            ( 'make', 'test' ), 1 )
        lines = exc.render_as_markdown( )
        assert len( lines ) == 1


class TestInheritance:
    ''' Tests for exception inheritance. '''

    def test_000_omnierror( self ):
        ''' All exceptions inherit from Omnierror. '''
        classes = [
            ConfigurationAbsence,
            ConfigurationInvalidity,
            DataInvalidity,
            DependencyAbsence,
            FileOperationFailure,
            ValidationCommandFailure,
        ]
        for cls in classes:
            assert issubclass( cls, Omnierror )
