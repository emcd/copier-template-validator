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
    ''' Parses configuration mapping into dataclass.

        Stops at the first invalid value encountered; this is intentional
        to match the project's fail-fast preference. Collective error
        reporting is not supported.
    '''
    answers_directory = _parse_answers_section(
        data.get( 'answers', { } ) )
    commands_data = data.get( 'commands' )
    commands = (
        _parse_commands_section( commands_data, source )
        if commands_data is not None else __.absent )
    options = _parse_options_section( data.get( 'options', { } ) )
    return Configuration(
        answers_directory = answers_directory,
        commands = commands,
        template_directory = options[ 'template_directory' ],
        preserve = options[ 'preserve' ],
        vcs_ref = options[ 'vcs_ref' ],
        unsafe = options[ 'unsafe' ],
    )


def _parse_answers_section(
    answers_data: __.typx.Any,
) -> __.Absential[ __.Path ]:
    ''' Parses ``[answers]`` section. '''
    answers_data = _expect_mapping( 'answers', answers_data )
    directory = answers_data.get( 'directory' )
    if directory is None: return __.absent
    _expect_string( 'answers.directory', directory )
    return __.Path( directory )


def _parse_commands_section(
    commands_data: __.typx.Any,
    source: __.Absential[ __.Path ],
) -> __.Absential[ tuple[ ValidationCommand, ... ] ]:
    ''' Parses ``[[commands]]`` array.

        Returns ``absent`` when the key is absent (inherited commands
        preserved through merge). Returns an empty tuple for an explicit
        empty array (clears inherited commands through merge).
    '''
    if commands_data is None: return __.absent
    if ( not isinstance( commands_data, __.cabc.Sequence )
         or isinstance( commands_data, str ) ):
        raise _exceptions.ConfigurationInvalidity(
            field = 'commands',
            expected = 'sequence of mappings',
            value = commands_data )
    items = __.typx.cast(
        __.cabc.Sequence[ __.typx.Any ], commands_data )
    return tuple(
        _parse_command( index, cmd, source )
        for index, cmd in enumerate( items ) )


def _parse_command(
    index: int,
    cmd: __.typx.Any,
    source: __.Absential[ __.Path ],
) -> ValidationCommand:
    ''' Parses a single command entry. '''
    cmd = _expect_mapping( f"commands[{index}]", cmd )
    try: raw_args = cmd[ 'args' ]
    except KeyError as exception:
        message = "missing 'args' in command"
        if not __.is_absent( source ):
            message = f"{message}: {source}"
        raise _exceptions.DataInvalidity(
            source if not __.is_absent( source )
            else __.Path( '<configuration>' ),
            message ) from exception
    args = _expect_string_sequence(
        f"commands[{index}].args", raw_args )
    cwd = cmd.get( 'cwd', __.absent )
    if not __.is_absent( cwd ):
        _expect_string( f"commands[{index}].cwd", cwd )
    return ValidationCommand( args = args, cwd = cwd )


def _parse_options_section(
    options_data: __.typx.Any,
) -> __.cabc.Mapping[ str, __.typx.Any ]:
    ''' Parses ``[options]`` section into field map. '''
    options_data = _expect_mapping( 'options', options_data )
    template_directory = _parse_template_directory_option(
        options_data.get( 'template-directory' ) )
    vcs_ref = _parse_vcs_ref( options_data.get( 'vcs-ref' ) )
    preserve = _expect_bool(
        'options.preserve', options_data.get( 'preserve' ) )
    unsafe = _expect_bool(
        'options.unsafe', options_data.get( 'unsafe' ) )
    return {
        'template_directory': template_directory,
        'preserve': preserve,
        'vcs_ref': vcs_ref,
        'unsafe': unsafe,
    }


def _parse_template_directory_option(
    value: __.typx.Any,
) -> __.Absential[ __.Path ]:
    ''' Parses ``options.template-directory``. '''
    if value is None: return __.absent
    _expect_string( 'options.template-directory', value )
    return __.Path( value )


def _parse_vcs_ref(
    value: __.typx.Any,
) -> __.Absential[ str ]:
    ''' Parses ``options.vcs-ref``, treating empty as absent. '''
    if value is None: return __.absent
    if value == '': return __.absent
    return _expect_string( 'options.vcs-ref', value )


def _expect_bool(
    field: str, value: __.typx.Any
) -> __.Absential[ bool ]:
    ''' Validates bool field or returns absent. '''
    if value is None: return __.absent
    if not isinstance( value, bool ):
        raise _exceptions.ConfigurationInvalidity(
            field = field,
            expected = 'bool',
            value = value )
    return value


def _expect_mapping(
    field: str, value: __.typx.Any,
) -> __.cabc.Mapping[ str, __.typx.Any ]:
    ''' Validates mapping field or raises. '''
    if not _is_mapping( value ):
        raise _exceptions.ConfigurationInvalidity(
            field = field,
            expected = 'mapping',
            value = value )
    return value


def _expect_string(
    field: str, value: __.typx.Any,
) -> str:
    ''' Validates string field or raises. '''
    if not isinstance( value, str ):
        raise _exceptions.ConfigurationInvalidity(
            field = field,
            expected = 'str',
            value = value )
    return value


def _expect_string_sequence(
    field: str, value: __.typx.Any,
) -> tuple[ str, ... ]:
    ''' Validates sequence-of-strings field or raises. '''
    if ( not isinstance( value, __.cabc.Sequence )
         or isinstance( value, str ) ):
        raise _exceptions.ConfigurationInvalidity(
            field = field,
            expected = 'sequence of strings',
            value = value )
    items = __.typx.cast(
        __.cabc.Sequence[ __.typx.Any ], value )
    return tuple(
        _expect_string( f"{field}[{index}]", item )
        for index, item in enumerate( items ) )


def _is_mapping(
    value: __.typx.Any,
) -> __.typx.TypeGuard[ __.cabc.Mapping[ str, __.typx.Any ] ]:
    ''' Type guard for mapping values. '''
    return isinstance( value, __.cabc.Mapping )
