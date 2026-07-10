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


''' Family of exceptions for package API. '''


from . import __


class Omniexception( __.immut.exceptions.Omniexception ):
    ''' Base for all exceptions raised by package API. '''


class Omnierror( Omniexception, Exception ):
    ''' Base for error exceptions raised by package API. '''


class ConfigurationAbsence( Omnierror, FileNotFoundError ):
    ''' Required configuration resource not found. '''

    def __init__(
        self, location: __.Absential[ __.Path ] = __.absent
    ) -> None:
        message = 'Could not locate configuration'
        if not __.is_absent( location ):
            message = f"{message} at '{location}'"
        super( ).__init__( f"{message}." )

    def render_as_markdown( self ) -> tuple[ str, ... ]:
        return (
            f"\u274c {self}",
            '',
            'Ensure the answers directory and copier.yaml exist.',
        )


class ConfigurationInvalidity( Omnierror, ValueError ):
    ''' Configuration data is invalid or a dependency is missing. '''

    def __init__(
        self,
        reason: __.Absential[ str | Exception ] = __.absent,
        *,
        subject: __.Absential[ str ] = __.absent,
        field: __.Absential[ str ] = __.absent,
        expected: __.Absential[ str ] = __.absent,
        value: __.typx.Any = __.absent,
    ) -> None:
        message = self._compose_message(
            reason, subject, field, expected, value )
        super( ).__init__( message )

    @staticmethod
    def _compose_message(
        reason: __.Absential[ str | Exception ],
        subject: __.Absential[ str ],
        field: __.Absential[ str ],
        expected: __.Absential[ str ],
        value: __.typx.Any,
    ) -> str:
        if not __.is_absent( field ):
            return ConfigurationInvalidity._format_field_error(
                field, expected, value )
        if not __.is_absent( subject ):
            return f"Missing required configuration: {subject}."
        if not __.is_absent( reason ):
            return f"Invalid configuration: {reason}"
        return 'Invalid configuration.'

    @staticmethod
    def _format_field_error(
        field: str,
        expected: __.Absential[ str ],
        value: __.typx.Any,
    ) -> str:
        if not __.is_absent( expected ) and not __.is_absent( value ):
            return (
                f"Invalid value for '{field}' "
                f"(expected {expected}, got {value!r})."
            )
        if not __.is_absent( expected ):
            return f"Invalid value for '{field}' (expected {expected})."
        if not __.is_absent( value ):
            return f"Invalid value for '{field}' (got {value!r})."
        return f"Invalid value for '{field}'."

    def render_as_markdown( self ) -> tuple[ str, ... ]:
        return ( f"\u274c {self}", )


class DataInvalidity( ConfigurationInvalidity ):
    ''' Data file content is invalid. '''

    def __init__( self, path: __.Path, cause: str ) -> None:
        super( ).__init__( f"{cause}: {path}" )


class FileOperationFailure( Omnierror, OSError ):
    ''' File or directory operation failure. '''

    def __init__( self, path: __.Path, operation: str = 'access file' ):
        message = f"Failed to {operation}: {path}"
        super( ).__init__( message )

    def render_as_markdown( self ) -> tuple[ str, ... ]:
        return ( f"\u274c {self}", )


class ValidationCommandFailure( Omnierror ):
    ''' Validation command exited with non-zero status. '''

    def __init__(
        self,
        command: tuple[ str, ... ],
        returncode: int,
        temp_directory: __.Absential[ __.Path ] = __.absent,
        stderr: __.Absential[ str ] = __.absent,
    ) -> None:
        self.command = command
        self.returncode = returncode
        self._temp_directory = temp_directory
        self._stderr = stderr
        message = (
            f"Validation command failed with exit code "
            f"{returncode}: {' '.join( command )}"
        )
        if not __.is_absent( temp_directory ):
            message = (
                f"{message}\nTemporary directory preserved at: "
                f"{temp_directory}"
            )
        if not __.is_absent( stderr ) and stderr:
            message = f"{message}\n{stderr}"
        super( ).__init__( message )

    def render_as_markdown( self ) -> tuple[ str, ... ]:
        lines = [
            f"\u274c Validation command failed "
            f"(exit code {self.returncode}): "
            f"{' '.join( self.command )}",
        ]
        if not __.is_absent( self._stderr ) and self._stderr:
            lines.append( self._stderr )
        if not __.is_absent( self._temp_directory ):
            lines.append(
                f"\U0001f4c1 Temporary directory preserved at: "
                f"{self._temp_directory}"
            )
        return tuple( lines )
