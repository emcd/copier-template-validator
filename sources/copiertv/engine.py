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


''' Core template validation engine. '''


from . import __
from . import configuration as _config
from . import exceptions as _exceptions


_scribe = __.logging.getLogger( __name__ )


class ValidationResult( __.immut.DataclassObject ):
    ''' Result of a template validation run. '''

    variant: str
    temporary_directory: __.Path
    items_attempted: int
    items_generated: int
    preserved: bool

    def render_as_markdown( self ) -> tuple[ str, ... ]:
        ''' Renders validation result as Markdown lines. '''
        lines = [
            f"\u2705 Validation complete for "
            f"'{self.variant}' variant:",
            f" * Temporary Directory: "
            f"{self.temporary_directory}",
            f" * Items: {self.items_generated}"
            f"/{self.items_attempted} generated",
        ]
        if self.preserved:
            lines.append(
                f" * \U0001f4c1 Files preserved for inspection"
                f" at: {self.temporary_directory}" )
        else:
            lines.append(
                ' * \U0001f5d1\ufe0f  Temporary files cleaned up' )
        return tuple( lines )


def _acquire_answers_file(
    path: __.Path,
) -> dict[ str, __.typx.Any ]:
    ''' Reads a YAML answers file. '''
    try: import yaml
    except ImportError as exception:
        raise _exceptions.DependencyAbsence( 'pyyaml' ) from exception
    try: content = path.read_text( encoding = 'utf-8' )
    except ( OSError, IOError ) as exception:
        raise _exceptions.FileOperationFailure(
            path, 'read answers file' ) from exception
    try: data: dict[ str, __.typx.Any ] = yaml.safe_load( content )
    except Exception as exception:
        raise _exceptions.DataInvalidity(
            path, 'Invalid YAML' ) from exception
    if not isinstance( data, dict ):
        raise _exceptions.DataInvalidity(
            path, 'Answers file must be a mapping' )
    return data


def _execute_command(
    command: tuple[ str, ... ],
    cwd: __.Path,
    temp_dir: __.Path,
    preserve: bool,
    _runner: __.cabc.Callable[ ..., __.typx.Any ] = __.subprocess.run,
) -> None:
    ''' Runs a command and wraps errors. '''
    try: _runner( command, cwd = cwd, check = True )
    except FileNotFoundError as exception:
        raise _exceptions.ConfigurationInvalidity(
            str( exception ) ) from exception
    except __.subprocess.CalledProcessError as exception:
        temp_ref: __.Absential[ __.Path ] = (
            temp_dir if preserve else __.absent )
        raise _exceptions.ValidationCommandFailure(
            command, exception.returncode, temp_ref
        ) from exception


def copy_template( # noqa: PLR0913
    answers_file: __.Path,
    project_directory: __.Path,
    template_directory: __.Path,
    vcs_ref: __.Absential[ str ] = __.absent,
    unsafe: bool = False,
    _answers_reader: __.cabc.Callable[
        [ __.Path ], dict[ str, __.typx.Any ]
    ] = _acquire_answers_file,
    _copier_copy: __.Absential[
        __.cabc.Callable[ ..., __.typx.Any ]
    ] = __.absent,
) -> None:
    ''' Copies template using Copier Python API. '''
    copier_copy: __.cabc.Callable[ ..., __.typx.Any ]
    if __.is_absent( _copier_copy ):
        try: from copier import run_copy as copier_copy
        except ImportError as exception:
            raise _exceptions.DependencyAbsence(
                'copier' ) from exception
    else: copier_copy = _copier_copy
    copy_kwargs: dict[ str, __.typx.Any ] = dict(
        data = _answers_reader( answers_file ),
        defaults = True,
        overwrite = True,
        quiet = True,
    )
    if not __.is_absent( vcs_ref ):
        copy_kwargs[ 'vcs_ref' ] = vcs_ref
    if unsafe: copy_kwargs[ 'unsafe' ] = True
    try: copier_copy(
        str( template_directory ),
        project_directory,
        **copy_kwargs,
    )
    except Exception as exception:
        raise _exceptions.ConfigurationInvalidity(
            str( exception ) ) from exception


def execute_validation_commands( # noqa: PLR0913
    config: _config.Configuration,
    template_dir: __.Path,
    project_dir: __.Path,
    temp_dir: __.Path,
    variant: str,
    _runner: __.cabc.Callable[ ..., __.typx.Any ] = __.subprocess.run,
) -> None:
    ''' Executes validation commands sequentially. '''
    for cmd in config.commands:
        args, cwd = _config.interpolate_command(
            cmd, template_dir, project_dir, temp_dir, variant )
        _scribe.debug(
            f"Running validation command: {' '.join( args )}" )
        _execute_command(
            args, cwd, temp_dir, config.preserve, _runner = _runner )


def survey_variants(
    answers_directory: __.Path,
) -> tuple[ str, ... ]:
    ''' Discovers variant names from ``answers-*.yaml`` files. '''
    if not answers_directory.is_dir( ):
        raise _exceptions.ConfigurationAbsence( answers_directory )
    return tuple( sorted(
        fsent.stem[ len( 'answers-' ): ]
        for fsent in answers_directory.glob( 'answers-*.yaml' )
        if fsent.is_file( )
    ) )


def validate_variant(
    variant: str,
    config: _config.Configuration,
    _copier_copy: __.Absential[
        __.cabc.Callable[ ..., __.typx.Any ]
    ] = __.absent,
    _runner: __.cabc.Callable[ ..., __.typx.Any ] = __.subprocess.run,
) -> ValidationResult:
    ''' Validates a single template variant. '''
    answers_dir = config.answers_directory
    if __.is_absent( answers_dir ):
        raise _exceptions.ConfigurationInvalidity( )
    answers_file = answers_dir / f"answers-{variant}.yaml"
    if not answers_file.is_file( ):
        raise _exceptions.ConfigurationAbsence( answers_file )
    template_dir = _resolve_template_directory( config )
    _scribe.info( f"Validating variant: {variant}" )
    temp_dir = _create_temporary_directory( variant )
    try:
        project_dir = temp_dir / variant
        copy_template(
            answers_file, project_dir, template_dir,
            config.vcs_ref, config.unsafe,
            _copier_copy = _copier_copy )
        execute_validation_commands(
            config, template_dir, project_dir, temp_dir, variant,
            _runner = _runner )
        items = len( config.commands ) + 1
        result = ValidationResult(
            variant = variant,
            temporary_directory = temp_dir,
            items_attempted = items,
            items_generated = items,
            preserved = config.preserve,
        )
    except _exceptions.ValidationCommandFailure:
        raise
    except Exception:
        if not config.preserve:
            _remove_temporary_directory( temp_dir )
        raise
    if not config.preserve:
        _remove_temporary_directory( temp_dir )
    return result


def _create_temporary_directory( variant: str ) -> __.Path:
    ''' Creates a temporary directory for validation. '''
    try: return __.Path( __.tempfile.mkdtemp(
        prefix = f"copiertv-{variant}-" ) )
    except ( OSError, IOError ) as exception:
        raise _exceptions.FileOperationFailure(
            __.Path( __.tempfile.gettempdir( ) ),
            'create temporary directory' ) from exception


def _remove_temporary_directory( path: __.Path ) -> None:
    ''' Removes a temporary directory, suppressing errors. '''
    _scribe.debug( f"Cleaning up temporary directory: {path}" )
    with __.ctxl.suppress( OSError, IOError ):
        __.shutil.rmtree( path )


def _resolve_template_directory(
    config: _config.Configuration,
) -> __.Path:
    ''' Resolves template directory from config or CWD. '''
    if not __.is_absent( config.template_directory ):
        return config.template_directory
    return __.Path.cwd( )
