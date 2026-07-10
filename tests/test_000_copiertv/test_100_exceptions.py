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
    FileOperationFailure,
    Omnierror,
    ValidationCommandFailure,
)


def test_100_configuration_absence_without_location( ):
    ''' Has message without location. '''
    exc = ConfigurationAbsence( )
    assert str( exc )


def test_110_configuration_absence_with_location( ):
    ''' Includes location in message. '''
    location = Path( '/some/path' )
    exc = ConfigurationAbsence( location )
    assert str( location ) in str( exc )


def test_120_configuration_absence_render( ):
    ''' Renders as Markdown lines. '''
    exc = ConfigurationAbsence( )
    lines = exc.render_as_markdown( )
    assert isinstance( lines, tuple )
    assert all( isinstance( line, str ) for line in lines )
    assert len( lines ) > 0


def test_125_configuration_invalidity_render( ):
    ''' Renders as Markdown lines. '''
    exc = ConfigurationInvalidity( )
    lines = exc.render_as_markdown( )
    assert isinstance( lines, tuple )
    assert all( isinstance( line, str ) for line in lines )
    assert len( lines ) > 0


def test_130_configuration_invalidity_default( ):
    ''' Has message. '''
    exc = ConfigurationInvalidity( )
    assert str( exc )


def test_140_configuration_invalidity_with_reason( ):
    ''' Includes reason in message. '''
    exc = ConfigurationInvalidity( 'bad value' )
    assert 'bad value' in str( exc )


def test_145_configuration_invalidity_with_field( ):
    ''' Includes field in message. '''
    exc = ConfigurationInvalidity(
        field = 'options.template-directory' )
    assert 'options.template-directory' in str( exc )


def test_150_configuration_invalidity_with_field_expected_value( ):
    ''' Includes field, expected, and offending value. '''
    exc = ConfigurationInvalidity(
        field = 'options.preserve',
        expected = 'bool',
        value = 42 )
    message = str( exc )
    assert 'options.preserve' in message
    assert 'bool' in message
    assert '42' in message


def test_155_configuration_invalidity_field_takes_precedence( ):
    ''' Field info takes precedence over reason. '''
    exc = ConfigurationInvalidity(
        'ignored reason', field = 'options.x', expected = 'str' )
    assert 'options.x' in str( exc )
    assert 'ignored reason' not in str( exc )


def test_150_configuration_invalidity_with_exception( ):
    ''' Wraps exception as reason. '''
    cause = ValueError( 'oops' )
    exc = ConfigurationInvalidity( cause )
    assert 'oops' in str( exc )


def test_170_data_invalidity_message( ):
    ''' Includes path and cause in message. '''
    path = Path( '/data.yaml' )
    exc = DataInvalidity( path, 'Invalid YAML' )
    assert str( path ) in str( exc )
    assert 'Invalid YAML' in str( exc )


def test_180_file_operation_failure_message( ):
    ''' Includes path and operation in message. '''
    path = Path( '/file' )
    exc = FileOperationFailure( path, 'read' )
    assert str( path ) in str( exc )
    assert 'read' in str( exc )


def test_185_file_operation_failure_render( ):
    ''' Renders as Markdown lines. '''
    exc = FileOperationFailure( Path( '/file' ), 'read' )
    lines = exc.render_as_markdown( )
    assert isinstance( lines, tuple )
    assert all( isinstance( line, str ) for line in lines )
    assert len( lines ) > 0


def test_190_validation_command_failure_basic( ):
    ''' Stores command and return code. '''
    exc = ValidationCommandFailure(
        ( 'make', 'test' ), 1 )
    assert exc.command == ( 'make', 'test' )
    assert exc.returncode == 1
    assert str( exc )


def test_200_validation_command_failure_with_temp_dir( tmp_path ):
    ''' Includes temp directory in message. '''
    exc = ValidationCommandFailure(
        ( 'make', 'test' ), 1, tmp_path )
    assert str( exc )
    lines = exc.render_as_markdown( )
    assert isinstance( lines, tuple )
    assert len( lines ) > 1


def test_210_validation_command_failure_without_temp_dir( ):
    ''' Renders without temp directory. '''
    exc = ValidationCommandFailure(
        ( 'make', 'test' ), 1 )
    lines = exc.render_as_markdown( )
    assert isinstance( lines, tuple )
    assert len( lines ) == 1


def test_215_validation_command_failure_with_stderr( ):
    ''' Includes stderr in message. '''
    exc = ValidationCommandFailure(
        ( 'make', 'test' ), 1, stderr = 'error output' )
    assert str( exc )
    lines = exc.render_as_markdown( )
    assert isinstance( lines, tuple )
    assert len( lines ) > 1


def test_220_inheritance_omnierror( ):
    ''' All exceptions inherit from Omnierror. '''
    classes = [
        ConfigurationAbsence,
        ConfigurationInvalidity,
        DataInvalidity,
        FileOperationFailure,
        ValidationCommandFailure,
    ]
    for cls in classes:
        assert issubclass( cls, Omnierror )
