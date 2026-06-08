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


''' Tests for validation engine. '''


from pathlib import Path

import pytest

from copiertv import exceptions
from copiertv.configuration import _interpolate_string
from copiertv.engine import (
    ValidationResult,
    survey_variants,
)


class TestSurveyVariants:
    ''' Tests for variant discovery. '''

    def test_000_variants_found( self, fs ):
        ''' Discovers variants from answers files. '''
        answers_dir = Path( '/project/data/copier' )
        fs.create_file( answers_dir / 'answers-default.yaml' )
        fs.create_file( answers_dir / 'answers-maximum.yaml' )
        result = survey_variants( answers_dir )
        assert result == ( 'default', 'maximum' )

    def test_010_no_variants( self, fs ):
        ''' Returns empty tuple when no answers files exist. '''
        answers_dir = Path( '/project/data/copier' )
        fs.create_dir( answers_dir )
        result = survey_variants( answers_dir )
        assert result == ( )

    def test_020_missing_directory( self, fs ):
        ''' Raises ConfigurationAbsence for missing directory. '''
        answers_dir = Path( '/nonexistent' )
        with pytest.raises( exceptions.ConfigurationAbsence ):
            survey_variants( answers_dir )

    def test_030_ignores_non_matching( self, fs ):
        ''' Ignores files that do not match pattern. '''
        answers_dir = Path( '/project/data/copier' )
        fs.create_file( answers_dir / 'answers-default.yaml' )
        fs.create_file( answers_dir / 'README.md' )
        fs.create_file( answers_dir / 'other.yaml' )
        result = survey_variants( answers_dir )
        assert result == ( 'default', )

    def test_040_sorted( self, fs ):
        ''' Returns variants in sorted order. '''
        answers_dir = Path( '/project/data/copier' )
        fs.create_file( answers_dir / 'answers-maximum.yaml' )
        fs.create_file( answers_dir / 'answers-alpha.yaml' )
        fs.create_file( answers_dir / 'answers-default.yaml' )
        result = survey_variants( answers_dir )
        assert result == ( 'alpha', 'default', 'maximum' )


class TestInterpolateString:
    ''' Tests for placeholder interpolation. '''

    def test_000_basic( self ):
        ''' Replaces single placeholder. '''
        placeholders = { '{name}': 'world' }
        result = _interpolate_string( 'hello {name}', placeholders )
        assert result == 'hello world'

    def test_010_multiple( self ):
        ''' Replaces multiple placeholders. '''
        placeholders = {
            '{a}': '1',
            '{b}': '2',
        }
        result = _interpolate_string( '{a} and {b}', placeholders )
        assert result == '1 and 2'

    def test_020_no_placeholders( self ):
        ''' Returns string unchanged when no placeholders match. '''
        result = _interpolate_string( 'plain text', { } )
        assert result == 'plain text'


class TestValidationResult:
    ''' Tests for result rendering. '''

    def test_000_render_success( self, tmp_path ):
        ''' Renders successful validation result. '''
        result = ValidationResult(
            variant = 'default',
            temporary_directory = tmp_path,
            items_attempted = 2,
            items_generated = 2,
            preserved = False,
        )
        lines = result.render_as_markdown( )
        assert len( lines ) == 4
        assert 'default' in lines[ 0 ]
        assert str( tmp_path ) in lines[ 1 ]
        assert '2/2' in lines[ 2 ]
        assert 'cleaned up' in lines[ 3 ]

    def test_010_render_preserved( self, tmp_path ):
        ''' Renders result with preserved directory. '''
        result = ValidationResult(
            variant = 'maximum',
            temporary_directory = tmp_path,
            items_attempted = 3,
            items_generated = 3,
            preserved = True,
        )
        lines = result.render_as_markdown( )
        assert len( lines ) == 4
        assert 'preserved' in lines[ 3 ].lower( )
