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


''' Command-line interface. '''


from . import __
from . import configuration as _configuration
from . import engine as _engine
from . import exceptions as _exceptions
from . import state as _state


def intercept_errors( ) -> __.cabc.Callable[
    [ __.cabc.Callable[
        ..., __.cabc.Coroutine[ __.typx.Any, __.typx.Any, None ] ] ],
    __.cabc.Callable[
        ..., __.cabc.Coroutine[ __.typx.Any, __.typx.Any, None ] ]
]:
    ''' Decorator that catches Omnierror for CLI display. '''
    def decorator(
        function: __.cabc.Callable[
            ..., __.cabc.Coroutine[ __.typx.Any, __.typx.Any, None ] ]
    ) -> __.cabc.Callable[
        ..., __.cabc.Coroutine[ __.typx.Any, __.typx.Any, None ]
    ]:
        @__.functools.wraps( function )
        async def wrapper(
            *args: __.typx.Any, **kwargs: __.typx.Any
        ) -> None:
            try: await function( *args, **kwargs )
            except _exceptions.Omnierror as exc:
                renderer = getattr(
                    exc, 'render_as_markdown', None )
                if renderer:
                    lines = renderer( )
                    print( '\n'.join( lines ) )
                raise SystemExit( 1 ) from exc
        return wrapper
    return decorator


async def _survey( config: _configuration.Configuration ) -> None:
    ''' Lists discovered template variants. '''
    answers_dir = config.answers_directory
    if __.is_absent( answers_dir ):
        from .exceptions import ConfigurationInvalidity
        raise ConfigurationInvalidity( 'answers directory' )  # noqa: TRY003
    for variant in _engine.survey_variants( answers_dir ):
        print( variant )


async def _validate(
    variant: str,
    config: _configuration.Configuration,
) -> None:
    ''' Validates a template variant. '''
    result = _engine.validate_variant( variant, config )
    lines = result.render_as_markdown( )
    print( '\n'.join( lines ) )


class _SurveyCommand( __.appcore_cli.Command ):
    ''' Surveys available template configuration variants. '''

    @intercept_errors( )
    async def execute( self, auxdata: __.Globals ) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not isinstance( auxdata, _state.Globals ):
            raise _exceptions.ConfigurationInvalidity( )
        await _survey( auxdata.copiertv_configuration )


class _ValidateCommand( __.appcore_cli.Command ):
    ''' Validates template against configuration variant. '''

    variant: __.typx.Annotated[
        str,
        __.typx.Doc( ''' Configuration variant to validate. ''' ),
        __.tyro.conf.Positional,
    ]
    preserve: __.typx.Annotated[
        bool,
        __.tyro.conf.arg(
            help = 'Keep temporary files for inspection.',
            prefix_name = False ),
    ] = False

    @intercept_errors( )
    async def execute( self, auxdata: __.Globals ) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not isinstance( auxdata, _state.Globals ):
            raise _exceptions.ConfigurationInvalidity( )
        cli_config = _configuration.Configuration(
            preserve = self.preserve )
        config = _configuration.merge_configurations(
            auxdata.copiertv_configuration, cli_config )
        await _validate( self.variant, config )


class _Application( __.appcore_cli.Application ):
    ''' Copiertv CLI application. '''

    command: __.typx.Union[
        __.typx.Annotated[
            _SurveyCommand,
            __.tyro.conf.subcommand(
                'survey', prefix_name = False ),
        ],
        __.typx.Annotated[
            _ValidateCommand,
            __.tyro.conf.subcommand(
                'validate', prefix_name = False ),
        ],
    ] = __.dcls.field( default_factory = _SurveyCommand )

    async def execute( self, auxdata: __.Globals ) -> None:
        ''' Dispatches to the selected command. '''
        await self.command( auxdata )

    async def prepare(
        self, exits: __.ctxl.AsyncExitStack
    ) -> _state.Globals:
        ''' Prepares copiertv-specific global state. '''
        auxdata_base = await super( ).prepare( exits )
        config = _configuration.acquire_configuration(
            auxdata_base.configuration )
        return _state.Globals(
            copiertv_configuration = config,
            **{
                field.name: getattr( auxdata_base, field.name )
                for field in __.dcls.fields( auxdata_base )
                if not field.name.startswith( '_' ) } )


def execute( ) -> None:
    ''' Entrypoint for CLI execution. '''
    config = (
        __.tyro.conf.EnumChoicesFromValues,
        __.tyro.conf.HelptextFromCommentsOff,
    )
    try: __.asyncio.run( __.tyro.cli( _Application, config = config )( ) )
    except SystemExit: raise
    except BaseException: raise SystemExit( 1 ) from None
