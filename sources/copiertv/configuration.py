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


''' Configuration loading and management. '''


from . import __
from . import exceptions as _exceptions


_VCS_MARKERS = ( '.git', '.hg', '.svn' )


class ValidationCommand( __.immut.DataclassObject ):
    ''' A single validation command with args and working directory. '''

    args: __.typx.Annotated[
        tuple[ str, ... ],
        __.typx.Doc( ''' Argument sequence for the command. ''' ),
    ]
    cwd: __.typx.Annotated[
        __.Absential[ str ],
        __.typx.Doc(
            ''' Working directory, with placeholder support. ''' ),
    ] = __.absent


class Configuration( __.immut.DataclassObject ):
    ''' Complete validation configuration. '''

    answers_directory: __.typx.Annotated[
        __.Absential[ __.Path ],
        __.typx.Doc(
            ''' Directory containing ``answers-*.yaml`` files. ''' ),
    ] = __.absent
    commands: __.typx.Annotated[
        __.Absential[ tuple[ ValidationCommand, ... ] ],
        __.typx.Doc( ''' Validation commands to execute. ''' ),
    ] = __.absent
    template_directory: __.typx.Annotated[
        __.Absential[ __.Path ],
        __.typx.Doc( ''' Template source directory. ''' ),
    ] = __.absent
    preserve: __.typx.Annotated[
        __.Absential[ bool ],
        __.typx.Doc( ''' Preserve temporary directories. ''' ),
    ] = __.absent
    variant_filter: __.typx.Annotated[
        __.Absential[ tuple[ str, ... ] ],
        __.typx.Doc( ''' Only validate these variants. ''' ),
    ] = __.absent
    vcs_ref: __.typx.Annotated[
        __.Absential[ str ],
        __.typx.Doc( ''' Git ref for copier copy. ''' ),
    ] = __.absent
    unsafe: __.typx.Annotated[
        __.Absential[ bool ],
        __.typx.Doc( ''' Allow unsafe Copier features. ''' ),
    ] = __.absent


def acquire_configuration(
    appcore_configuration: __.cabc.Mapping[ str, __.typx.Any ],
    cli_overrides: __.Absential[ Configuration ] = __.absent,
) -> Configuration:
    ''' Acquires config from appcore dict and project config.

        Merges project configuration with appcore-provided user
        configuration. CLI overrides take final precedence.
    '''
    user_config = _parse_configuration_data( appcore_configuration )
    project_config = _acquire_project_configuration(
        appcore_configuration )
    file_config = merge_configurations( user_config, project_config )
    if __.is_absent( cli_overrides ): return file_config
    return merge_configurations( file_config, cli_overrides )


def detect_project_root( ) -> __.Path:
    ''' Detects project root by walking up for VCS markers. '''
    path = __.Path.cwd( )
    while True:
        for marker in _VCS_MARKERS:
            if ( path / marker ).exists( ): return path
        parent = path.parent
        if parent == path: break
        path = parent
    return __.Path.cwd( )


def interpolate_command(
    command: ValidationCommand,
    template_directory: __.Path,
    project_directory: __.Path,
    temporary_directory: __.Path,
    variant: str,
) -> tuple[ tuple[ str, ... ], __.Path ]:
    ''' Interpolates placeholders in command args and cwd. '''
    placeholders = {
        '{template_directory}': str( template_directory ),
        '{project_directory}': str( project_directory ),
        '{temporary_directory}': str( temporary_directory ),
        '{variant}': variant,
    }
    args = tuple(
        _interpolate_string( arg, placeholders )
        for arg in command.args
    )
    if __.is_absent( command.cwd ): cwd = template_directory
    else: cwd = __.Path(
        _interpolate_string( command.cwd, placeholders ) )
    return args, cwd


def merge_configurations(
    base: Configuration, override: Configuration
) -> Configuration:
    ''' Merges configurations, override taking precedence. '''
    kwargs: dict[ str, __.typx.Any ] = { }
    for field in __.dcls.fields( Configuration ):
        if field.name.startswith( '_' ): continue
        override_value = getattr( override, field.name )
        base_value = getattr( base, field.name )
        if not __.is_absent( override_value ):
            kwargs[ field.name ] = override_value
        else:
            kwargs[ field.name ] = base_value
    return Configuration( **kwargs )


def parse_toml_configuration( path: __.Path ) -> Configuration:
    ''' Parses configuration from a TOML file. '''
    try: content = path.read_text( encoding = 'utf-8' )
    except ( OSError, IOError ) as exception:
        raise _exceptions.FileOperationFailure(
            path, 'read configuration' ) from exception
    try: data = __.tomllib.loads( content )
    except ValueError as exception:
        raise _exceptions.DataInvalidity(
            path, 'Invalid TOML' ) from exception
    return _parse_configuration_data( data, source = path )


def _acquire_project_configuration(
    appcore_configuration: __.cabc.Mapping[ str, __.typx.Any ],
) -> Configuration:
    ''' Acquires per-project configuration. '''
    options_data = appcore_configuration.get( 'options', { } )
    project_config_raw = options_data.get( 'project-configuration' )
    if project_config_raw:
        config_path = __.Path( project_config_raw )
    else:
        project_root = detect_project_root( )
        config_path = (
            project_root / '.auxiliary' / 'configuration'
            / 'copiertv' / 'general.toml' )
    if not config_path.is_file( ): return Configuration( )
    return parse_toml_configuration( config_path )


def _interpolate_string(
    value: str, placeholders: dict[ str, str ]
) -> str:
    ''' Replaces placeholder substrings in a string. '''
    for placeholder, replacement in placeholders.items():
        value = value.replace( placeholder, replacement )
    return value


def _parse_configuration_data(
    data: __.cabc.Mapping[ str, __.typx.Any ],
    source: __.Absential[ __.Path ] = __.absent,
) -> Configuration:
    ''' Parses configuration mapping into dataclass. '''
    answers_data = data.get( 'answers', { } )
    answers_dir_raw = answers_data.get( 'directory' )
    answers_directory = (
        __.Path( answers_dir_raw )
        if answers_dir_raw else __.absent )
    commands_data = data.get( 'commands', ( ) )
    commands: list[ ValidationCommand ] = [ ]
    for cmd in commands_data:
        try: args = tuple( cmd[ 'args' ] )
        except KeyError as exception:
            message = "missing 'args' in command"
            if not __.is_absent( source ):
                message = f"{message}: {source}"
            raise _exceptions.DataInvalidity(
                source if not __.is_absent( source )
                else __.Path( '<configuration>' ),
                message ) from exception
        commands.append( ValidationCommand(
            args = args,
            cwd = cmd.get( 'cwd', __.absent ),
        ) )
    options_data = data.get( 'options', { } )
    template_dir_raw = options_data.get( 'template-directory' )
    template_directory = (
        __.Path( template_dir_raw )
        if template_dir_raw else __.absent )
    variants_raw = options_data.get( 'variants' )
    variant_filter = (
        tuple( variants_raw ) if variants_raw else __.absent )
    vcs_ref = options_data.get( 'vcs-ref', __.absent )
    preserve_raw = options_data.get( 'preserve' )
    unsafe_raw = options_data.get( 'unsafe' )
    return Configuration(
        answers_directory = answers_directory,
        commands = tuple( commands ),
        template_directory = template_directory,
        preserve = preserve_raw if preserve_raw is not None else __.absent,
        variant_filter = variant_filter,
        vcs_ref = vcs_ref if vcs_ref else __.absent,
        unsafe = unsafe_raw if unsafe_raw is not None else __.absent,
    )
