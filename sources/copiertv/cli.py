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


@intercept_errors( )
async def _main( ) -> None:
    ''' Entrypoint for CLI execution. '''
    config = (
        __.tyro.conf.EnumChoicesFromValues,
        __.tyro.conf.HelptextFromCommentsOff,
    )
    dispatcher = __.tyro.cli( _CommandDispatcher, config = config )
    await dispatcher( )


class _SurveyCommand:
    ''' Surveys available template configuration variants. '''

    async def __call__( self ) -> None:
        config = _configuration.acquire_configuration( )
        await _survey( config )


class _ValidateCommand:
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

    async def __call__( self ) -> None:
        cli_config = _configuration.Configuration(
            preserve = self.preserve )
        config = _configuration.acquire_configuration( cli_config )
        await _validate( self.variant, config )


class _CommandDispatcher:
    ''' Dispatches template validation commands. '''

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

    async def __call__( self ) -> None:
        await self.command( )


def execute( ) -> None:
    ''' Entrypoint for CLI execution. '''
    from asyncio import run
    try: run( _main( ) )
    except SystemExit: raise
    except BaseException: raise SystemExit( 1 ) from None
