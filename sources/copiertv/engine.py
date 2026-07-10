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
    import yaml
    try: content = path.read_text( encoding = 'utf-8' )
    except ( OSError, IOError ) as exception: # pragma: no cover
        raise _exceptions.FileOperationFailure(
            path, 'read answers file' ) from exception
    try: data: dict[ str, __.typx.Any ] = yaml.safe_load( content )
    except Exception as exception: # pragma: no cover
        raise _exceptions.DataInvalidity(
            path, 'Invalid YAML' ) from exception
    if not isinstance( data, dict ): # pragma: no cover
        raise _exceptions.DataInvalidity(
            path, 'Answers file must be a mapping' )
    return data


def _execute_command(
    command: tuple[ str, ... ],
    working_directory: __.Path,
    temporary_directory: __.Path,
    preserve: bool,
    executor: __.cabc.Callable[ ..., __.typx.Any ] = __.subprocess.run,
) -> None:
    ''' Runs a command and wraps errors. '''
    try: executor(
        command, cwd = working_directory, check = True,
        stdout = __.subprocess.PIPE, stderr = __.subprocess.PIPE,
    )
    except FileNotFoundError as exception:
        raise _exceptions.ConfigurationInvalidity(
            str( exception ) ) from exception
    except __.subprocess.CalledProcessError as exception:
        temp_ref: __.Absential[ __.Path ] = (
            temporary_directory if preserve else __.absent )
        stderr_text: __.Absential[ str ] = (
            exception.stderr.decode( 'utf-8', errors = 'replace' )
            if exception.stderr else __.absent )
        raise _exceptions.ValidationCommandFailure(
            command, exception.returncode, temp_ref, stderr_text
        ) from exception


def copy_template( # noqa: PLR0913
    answers_file: __.Path,
    project_directory: __.Path,
    template_directory: __.Path,
    vcs_ref: __.Absential[ str ] = __.absent,
    unsafe: bool = False,
    answers_reader: __.cabc.Callable[
        [ __.Path ], dict[ str, __.typx.Any ]
    ] = _acquire_answers_file,
    copier: __.Absential[
        __.cabc.Callable[ ..., __.typx.Any ]
    ] = __.absent,
) -> None:
    ''' Copies template using Copier Python API. '''
    copier_copy: __.cabc.Callable[ ..., __.typx.Any ]
    if __.is_absent( copier ):
        from copier import run_copy as copier_copy
    else: copier_copy = copier
    copy_kwargs: dict[ str, __.typx.Any ] = dict(
        data = answers_reader( answers_file ),
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
    template_directory: __.Path,
    project_directory: __.Path,
    temporary_directory: __.Path,
    variant: str,
    executor: __.cabc.Callable[ ..., __.typx.Any ] = __.subprocess.run,
) -> None:
    ''' Executes validation commands sequentially. '''
    preserve = (
        bool( config.preserve )
        if not __.is_absent( config.preserve )
        else False )
    if __.is_absent( config.commands ): return
    for cmd in config.commands:
        args, cwd = _config.interpolate_command(
            cmd, template_directory, project_directory,
            temporary_directory, variant )
        _scribe.debug(
            f"Running validation command: {' '.join( args )}" )
        _execute_command(
            args, cwd, temporary_directory, preserve,
            executor = executor )


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
    copier: __.Absential[
        __.cabc.Callable[ ..., __.typx.Any ]
    ] = __.absent,
    executor: __.cabc.Callable[ ..., __.typx.Any ] = __.subprocess.run,
) -> ValidationResult:
    ''' Validates a single template variant. '''
    answers_dir = config.answers_directory
    if __.is_absent( answers_dir ):
        raise _exceptions.ConfigurationInvalidity(
            subject = 'answers directory' )
    answers_file = answers_dir / f"answers-{variant}.yaml"
    if not answers_file.is_file( ):
        raise _exceptions.ConfigurationAbsence( answers_file )
    template_directory = _resolve_template_directory( config )
    _scribe.info( f"Validating variant: {variant}" )
    temporary_directory = _create_temporary_directory( variant )
    preserve = (
        bool( config.preserve )
        if not __.is_absent( config.preserve )
        else False )
    unsafe = (
        bool( config.unsafe )
        if not __.is_absent( config.unsafe )
        else False )
    try:
        project_directory = temporary_directory / variant
        copy_template(
            answers_file, project_directory, template_directory,
            config.vcs_ref, unsafe,
            copier = copier )
        execute_validation_commands(
            config, template_directory, project_directory,
            temporary_directory, variant,
            executor = executor )
        commands_count = (
            0 if __.is_absent( config.commands )
            else len( config.commands ) )
        items = commands_count + 1
        result = ValidationResult(
            variant = variant,
            temporary_directory = temporary_directory,
            items_attempted = items,
            items_generated = items,
            preserved = preserve,
        )
    except _exceptions.ValidationCommandFailure:
        if not preserve:
            _remove_temporary_directory( temporary_directory )
        raise
    except Exception:
        if not preserve:
            _remove_temporary_directory( temporary_directory )
        raise
    if not preserve:
        _remove_temporary_directory( temporary_directory )
    return result


def _create_temporary_directory( variant: str ) -> __.Path:
    ''' Creates a temporary directory for validation. '''
    try: return __.Path( __.tempfile.mkdtemp(
        prefix = f"copiertv-{variant}-" ) )
    except ( OSError, IOError ) as exception: # pragma: no cover
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
    ''' Resolves template directory from configuration. '''
    if not __.is_absent( config.template_directory ):
        return config.template_directory
    raise _exceptions.ConfigurationInvalidity(
        subject = 'template directory' )
