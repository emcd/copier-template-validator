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


# Semantic replacements for decorated Unicode characters that are
# part of the rendered CLI output. The pair ``🗑️`` / ``🗑`` covers
# the variation-selector-16 form and the bare form, since some
# terminals strip the variation selector before printing.
_RENDERING_REPLACEMENTS = (
    ( '\u2705', '[OK]' ),
    ( '\u274c', '[ERROR]' ),
    ( '\U0001f4c1', '[FILES]' ),
    ( '\U0001f5d1\ufe0f', '[CLEANUP]' ),
    ( '\U0001f5d1', '[CLEANUP]' ),
)


def _apply_substitutions_to_lines(
    lines: tuple[ str, ... ],
) -> tuple[ str, ... ]:
    ''' Apply the semantic ``_RENDERING_REPLACEMENTS`` table to
        every line. ``str.replace`` replaces multi-code-unit
        decorations (e.g., the variation-selector-16 form of the
        trash emoji) as a unit.
    '''
    adapted: list[ str ] = list( lines )
    for decorated, label in _RENDERING_REPLACEMENTS:
        adapted = [ line.replace( decorated, label ) for line in adapted ]
    return tuple( adapted )


def _adapt_rendered_lines(
    lines: tuple[ str, ... ],
    encoding: __.typx.Optional[ str ],
) -> tuple[ str, ... ]:
    ''' Adapt ``lines`` for safe output under ``encoding``.

        ``render_as_markdown`` returns a pure, stream-independent
        representation; encoding is a presentation concern handled
        here. On a UTF-capable stream the lines are returned
        unchanged. On a stream whose declared encoding cannot
        represent the decorated characters, the substitutions
        above are applied first and any text that still cannot
        encode is escaped with ``backslashreplace`` so user
        paths and messages are not silently dropped. An unknown
        encoding name falls through to the same safe path using
        ASCII as the safest universally-supported target.
    '''
    if encoding is None:
        return lines
    for candidate in ( lines, _apply_substitutions_to_lines( lines ) ):
        if _encodes_cleanly( candidate, encoding ):
            return candidate
    safe_encodings: list[ str ] = []
    if encoding not in ( None, 'ascii' ):
        safe_encodings.append( encoding )
    safe_encodings.append( 'ascii' )
    adapted = _apply_substitutions_to_lines( lines )
    for safe in safe_encodings:
        result = _backslash_replace( adapted, safe )
        if result is not None:
            return result
    return adapted


def _backslash_replace(
    lines: tuple[ str, ... ],
    encoding: str,
) -> __.typx.Optional[ tuple[ str, ... ] ]:
    ''' Round-trip ``lines`` through ``encoding`` with
        ``backslashreplace`` error handling. Returns ``None`` if
        the encoding name is unknown (caller falls back to the
        next safe encoding).
    '''
    try:
        return tuple(
            line.encode( encoding, errors = 'backslashreplace' ).decode(
                encoding, errors = 'backslashreplace' )
            for line in lines
        )
    except LookupError:
        return None


def _encodes_cleanly(
    candidate: tuple[ str, ... ],
    encoding: __.typx.Optional[ str ],
) -> bool:
    ''' True iff ``candidate`` encodes without error under
        ``encoding``. ``LookupError`` is treated as not clean so
        unknown encoding names fall through to the safe path.
    '''
    if encoding is None:
        return True
    try:
        '\n'.join( candidate ).encode( encoding )
    except ( UnicodeEncodeError, LookupError ):
        return False
    return True


def _print_rendered_lines(
    lines: tuple[ str, ... ],
    stream: __.typx.Optional[ __.typx.Any ] = None,
) -> None:
    ''' Print rendered CLI lines, adapting to ``stream``'s encoding.

        ``stream`` is resolved at call time (not as a default
        argument) so the helper picks up encoding changes such as
        pytest's capture, application-level redirection, or
        embedding contexts. The default falls back to the
        current value of ``sys.stdout``.
    '''
    if stream is None:
        stream = __.sys.stdout
    encoding = getattr( stream, 'encoding', None )
    adapted = _adapt_rendered_lines( lines, encoding )
    print( '\n'.join( adapted ), file = stream )


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
                    _print_rendered_lines( renderer( ) )
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
    _print_rendered_lines( result.render_as_markdown( ) )


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
    ''' Validates Copier templates against configuration variants. '''

    version: __.typx.Annotated[
        bool,
        __.tyro.conf.arg(
            help = 'Display version and exit.',
            prefix_name = False ),
    ] = False

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
        if self.version:
            from . import __version__
            print( f"copiertv {__version__}" )
            raise SystemExit( 0 )
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
