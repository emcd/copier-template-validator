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


''' Tests for configuration module. '''


from pathlib import Path
from typing import Any

from absence import absent

from copiertv.configuration import (
    Configuration,
    ValidationCommand,
    detect_project_root,
    interpolate_command,
    merge_configurations,
)


def test_100_validation_command_basic( ):
    ''' Creates command with args only. '''
    cmd = ValidationCommand( args = ( 'echo', 'hello' ) )
    assert cmd.args == ( 'echo', 'hello' )
    assert cmd.cwd is absent


def test_110_validation_command_with_cwd( ):
    ''' Creates command with args and cwd. '''
    cmd = ValidationCommand(
        args = ( 'make', 'test' ),
        cwd = '{project_directory}',
    )
    assert cmd.args == ( 'make', 'test' )
    assert cmd.cwd == '{project_directory}'


def test_120_configuration_defaults( ):
    ''' Has expected default values. '''
    config = Configuration( )
    assert config.answers_directory is absent
    assert config.commands is absent
    assert config.template_directory is absent
    assert config.preserve is absent
    assert config.vcs_ref is absent
    assert config.unsafe is absent


def test_130_merge_configurations_override_answers( ):
    ''' Override answers_directory takes precedence. '''
    base = Configuration( answers_directory = Path( '/base' ) )
    override = Configuration( answers_directory = Path( '/override' ) )
    result = merge_configurations( base, override )
    assert result.answers_directory == Path( '/override' )


def test_140_merge_configurations_base_preserved( ):
    ''' Base values preserved when override is absent. '''
    base = Configuration( preserve = True )
    override = Configuration( )
    result = merge_configurations( base, override )
    assert result.preserve is True


def test_150_merge_configurations_override_preserve( ):
    ''' Override preserve takes precedence. '''
    base = Configuration( preserve = False )
    override = Configuration( preserve = True )
    result = merge_configurations( base, override )
    assert result.preserve is True


def test_155_merge_configurations_false_overrides_true( ):
    ''' Explicit false can override true. '''
    base = Configuration( preserve = True, unsafe = True )
    override = Configuration( preserve = False, unsafe = False )
    result = merge_configurations( base, override )
    assert result.preserve is False
    assert result.unsafe is False


def test_160_interpolate_command_basic( fs ):
    ''' Interpolates placeholders in args. '''
    template_directory = Path( '/template' )
    project_directory = Path( '/project' )
    temporary_directory = Path( '/temp' )
    cmd = ValidationCommand(
        args = ( 'check', '--source', '{project_directory}' ) )
    args, cwd = interpolate_command(
        cmd, template_directory, project_directory,
        temporary_directory, 'default' )
    assert args == ( 'check', '--source', str( project_directory ) )
    assert cwd == template_directory


def test_170_interpolate_command_cwd_placeholder( fs ):
    ''' Interpolates cwd placeholder. '''
    template_directory = Path( '/template' )
    project_directory = Path( '/project' )
    temporary_directory = Path( '/temp' )
    cmd = ValidationCommand(
        args = ( 'make', ),
        cwd = '{project_directory}',
    )
    _, cwd = interpolate_command(
        cmd, template_directory, project_directory,
        temporary_directory, 'default' )
    assert cwd == project_directory


def test_180_interpolate_command_variant_placeholder( fs ):
    ''' Interpolates variant placeholder. '''
    template_directory = Path( '/template' )
    project_directory = Path( '/project' )
    temporary_directory = Path( '/temp' )
    cmd = ValidationCommand(
        args = ( 'echo', '{variant}' ) )
    args, _ = interpolate_command(
        cmd, template_directory, project_directory,
        temporary_directory, 'maximum' )
    assert args == ( 'echo', 'maximum' )


def test_190_detect_project_root_git_found( fs ):
    ''' Returns directory containing .git. '''
    fs.create_dir( '/project/.git' )
    fs.create_dir( '/project/src' )
    import os
    os.chdir( '/project/src' )
    root = detect_project_root( )
    # Compare path without drive letter for Windows compatibility.
    expected = Path( '/project' )
    assert (
        root.relative_to( root.anchor )
        == expected.relative_to( expected.anchor ) )


def test_200_detect_project_root_no_vcs( fs ):
    ''' Returns CWD when no VCS marker found. '''
    fs.create_dir( '/plain/dir' )
    import os
    os.chdir( '/plain/dir' )
    root = detect_project_root( )
    # Compare path without drive letter for Windows compatibility.
    expected = Path( '/plain/dir' )
    assert (
        root.relative_to( root.anchor )
        == expected.relative_to( expected.anchor ) )


# --- Field-level validation errors ---


_BAD_CONFIGS: dict[ str, dict[ str, Any ] ] = {
    'options.preserve': { 'options': { 'preserve': 'yes' } },
    'options.unsafe': { 'options': { 'unsafe': 1 } },
    'options.template_directory':
        { 'options': { 'template-directory': 42 } },
    'answers': { 'answers': [ 'bad' ] },
    'commands': { 'commands': 'bad' },
    'commands_entry': { 'commands': [ 'bad' ] },
    'commands_args': { 'commands': [ { 'args': 'hatch' } ] },
    'commands_arg_element':
        { 'commands': [ { 'args': [ 'hatch', 42 ] } ] },
}


def _bad( key: str ) -> None:
    ''' Triggers parse on a known-bad configuration. '''
    from copiertv.configuration import _parse_configuration_data
    _parse_configuration_data( _BAD_CONFIGS[ key ] )


def test_210_invalid_preserve_type( ):
    ''' Raises with field info when preserve is not bool. '''
    import pytest
    from copiertv import exceptions
    with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
        _bad( 'options.preserve' )
    message = str( info.value )
    assert 'options.preserve' in message
    assert 'bool' in message
    assert "'yes'" in message


def test_220_invalid_unsafe_type( ):
    ''' Raises with field info when unsafe is not bool. '''
    import pytest
    from copiertv import exceptions
    with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
        _bad( 'options.unsafe' )
    message = str( info.value )
    assert 'options.unsafe' in message
    assert 'bool' in message


def test_230_invalid_template_directory_type( ):
    ''' Raises when template-directory is not a string. '''
    import pytest
    from copiertv import exceptions
    with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
        _bad( 'options.template_directory' )
    message = str( info.value )
    assert 'options.template-directory' in message
    assert 'str' in message


def test_260_invalid_answers_type( ):
    ''' Raises when answers is not a mapping. '''
    import pytest
    from copiertv import exceptions
    with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
        _bad( 'answers' )
    assert 'answers' in str( info.value )


def test_270_invalid_commands_type( ):
    ''' Raises when commands is not a sequence. '''
    import pytest
    from copiertv import exceptions
    with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
        _bad( 'commands' )
    assert 'commands' in str( info.value )


def test_280_invalid_command_entry_type( ):
    ''' Raises when command entry is not a mapping. '''
    import pytest
    from copiertv import exceptions
    with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
        _bad( 'commands_entry' )
    assert 'commands[0]' in str( info.value )


def test_290_invalid_command_args_type( ):
    ''' Raises when command args is not a sequence. '''
    import pytest
    from copiertv import exceptions
    with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
        _bad( 'commands_args' )
    message = str( info.value )
    assert 'commands[0].args' in message


def test_300_invalid_command_arg_element_type( ):
    ''' Raises when command arg element is not a string. '''
    import pytest
    from copiertv import exceptions
    with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
        _bad( 'commands_arg_element' )
    message = str( info.value )
    assert 'commands[0].args[1]' in message
    assert 'str' in message


def test_310_valid_full_configuration( tmp_path ):
    ''' Parses a complete valid configuration. '''
    from copiertv.configuration import _parse_configuration_data
    data = {
        'answers': { 'directory': str( tmp_path / 'answers' ) },
        'commands': [ { 'args': [ 'hatch', 'test' ] } ],
        'options': {
            'template-directory': str( tmp_path / 'template' ),
            'preserve': True,
            'unsafe': False,
            'vcs-ref': 'main',
        },
    }
    config = _parse_configuration_data( data )
    assert config.answers_directory == tmp_path / 'answers'
    assert config.commands is not absent
    assert len( config.commands ) == 1
    assert config.template_directory == tmp_path / 'template'
    assert config.preserve is True
    assert config.unsafe is False
    assert config.vcs_ref == 'main'


# --- Regression tests for review findings ---


def test_320_missing_boolean_overrides_correctly( tmp_path ):
    ''' Missing boolean in user config preserves project value.

        Regression for Finding 1: _expect_bool return value previously
        was discarded, leaving a raw ``None`` that merge treated as an
        explicit override.
    '''
    from copiertv.configuration import (
        _parse_configuration_data, merge_configurations,
    )
    base = _parse_configuration_data(
        { 'options': { 'preserve': True, 'unsafe': True } } )
    override = _parse_configuration_data( { } )
    result = merge_configurations( base, override )
    assert result.preserve is True
    assert result.unsafe is True


def test_330_vcs_ref_falsy_non_string_rejected( ):
    ''' Vcs-ref values such as false or 0 are not silently accepted.

        Regression for Finding 2: presence was previously tested via
        truthiness, so ``false``/``0`` slipped through as ``absent``.
    '''
    import pytest
    from copiertv import exceptions
    from copiertv.configuration import _parse_configuration_data
    for bad in ( False, 0, [ ] ):
        with pytest.raises( exceptions.ConfigurationInvalidity ) as info:
            _parse_configuration_data(
                { 'options': { 'vcs-ref': bad } } )
        assert 'options.vcs-ref' in str( info.value )


def test_340_vcs_ref_empty_string_treated_as_absent( ):
    ''' Empty-string vcs-ref is treated as absent (not invalid). '''
    from copiertv.configuration import _parse_configuration_data
    config = _parse_configuration_data(
        { 'options': { 'vcs-ref': '' } } )
    assert config.vcs_ref is absent


def test_350_empty_commands_clears_inheritance( tmp_path ):
    ''' Explicit ``commands = []`` clears inherited commands in merge.

        Regression for Finding 3: previously empty and absent were
        indistinguishable, so users could not intentionally clear
        inherited commands.
    '''
    from copiertv.configuration import (
        _parse_configuration_data, merge_configurations,
    )
    base = _parse_configuration_data(
        { 'commands': [ { 'args': [ 'hatch', 'test' ] } ] } )
    override = _parse_configuration_data( { 'commands': [ ] } )
    result = merge_configurations( base, override )
    assert result.commands is not absent
    assert len( result.commands ) == 0


def test_360_missing_commands_preserves_inheritance( tmp_path ):
    ''' Missing ``commands`` key preserves inherited commands in merge. '''
    from copiertv.configuration import (
        _parse_configuration_data, merge_configurations,
    )
    base = _parse_configuration_data(
        { 'commands': [ { 'args': [ 'hatch', 'test' ] } ] } )
    override = _parse_configuration_data( { } )
    result = merge_configurations( base, override )
    assert result.commands is not absent
    assert len( result.commands ) == 1


# --- Todo 10 audit: every field type's merge-clobber behavior ---


def test_370_answers_directory_present_inherits( ):
    ''' Answers-directory set in base survives absent override. '''
    from copiertv.configuration import (
        _parse_configuration_data, merge_configurations,
    )
    base = _parse_configuration_data(
        { 'answers': { 'directory': '/project/answers' } } )
    override = _parse_configuration_data( { } )
    result = merge_configurations( base, override )
    assert result.answers_directory == Path( '/project/answers' )


def test_400_template_directory_present_inherits( ):
    ''' Template-directory set in base survives absent override. '''
    from copiertv.configuration import (
        _parse_configuration_data, merge_configurations,
    )
    base = _parse_configuration_data(
        { 'options': { 'template-directory': '/tpl' } } )
    override = _parse_configuration_data( { } )
    result = merge_configurations( base, override )
    assert result.template_directory == Path( '/tpl' )


def test_410_vcs_ref_present_inherits( ):
    ''' Vcs-ref set in base survives absent override. '''
    from copiertv.configuration import (
        _parse_configuration_data, merge_configurations,
    )
    base = _parse_configuration_data(
        { 'options': { 'vcs-ref': 'main' } } )
    override = _parse_configuration_data( { } )
    result = merge_configurations( base, override )
    assert result.vcs_ref == 'main'


def test_420_vcs_ref_present_overridden_by_override( ):
    ''' Vcs-ref in override replaces base value. '''
    from copiertv.configuration import (
        _parse_configuration_data, merge_configurations,
    )
    base = _parse_configuration_data(
        { 'options': { 'vcs-ref': 'main' } } )
    override = _parse_configuration_data(
        { 'options': { 'vcs-ref': 'develop' } } )
    result = merge_configurations( base, override )
    assert result.vcs_ref == 'develop'


def test_430_unsafe_inherits_when_missing( ):
    ''' Unsafe flag set in base survives absent override. '''
    from copiertv.configuration import (
        _parse_configuration_data, merge_configurations,
    )
    base = _parse_configuration_data(
        { 'options': { 'unsafe': True } } )
    override = _parse_configuration_data( { } )
    result = merge_configurations( base, override )
    assert result.unsafe is True


def test_440_missing_keys_become_absent( ):
    ''' Every field of an empty TOML parsing result must be absent.

        Documents and locks in that missing fields become ``absent``
        through the parser, never ``None`` or another raw sentinel
        that merge would misclassify as an explicit override.
    '''
    from copiertv.configuration import _parse_configuration_data
    config = _parse_configuration_data( { } )
    for field in (
        'answers_directory', 'commands', 'template_directory',
        'preserve', 'vcs_ref', 'unsafe',
    ):
        value = getattr( config, field )
        assert value is absent, (
            f"field {field!r} produced {value!r} for empty input "
            f"(should be absent)" )


def test_450_explicit_empty_collection_signals_clear( ):
    ''' Explicit empty ``commands = []`` survives the parser as an
        empty tuple (not converted to ``absent``), which is the wire
        signal for "clear inheritance" through merge.
    '''
    from copiertv.configuration import _parse_configuration_data
    commands_config = _parse_configuration_data(
        { 'commands': [ ] } )
    assert commands_config.commands is not absent
    assert commands_config.commands == ( )
