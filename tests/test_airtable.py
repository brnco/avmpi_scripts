'''
tests the Airtable module
'''
import os
import pytest
import pathlib
import avmpi_scripts.airtable.airtable as airtable

is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
'''
pytestmark = pytest.mark.skipif(
        os.getenv('GITHUB_ACTIONS') == 'true',
        reason="skipping because GitHub Actions do not have Airtable api_key in airtable_config.json")
'''


def test_get_field_map():
    field_map = airtable.get_field_map('PhysicalAssetRecord')
    assert field_map['physical_asset_id']


@pytest.mark.skipif(is_github_actions, reason='github')
def test_connect_one_base():
    atbl_base = airtable.connect_one_base('Assets')
    assert atbl_base['Physical Assets']
