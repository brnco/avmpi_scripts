'''
tests the Airtable module
'''
import pytest
import pathlib
import avmpi_scripts.airtable.airtable as airtable


def test_get_field_map():
    field_map = airtable.get_field_map('PhysicalAssetRecord')
    assert field_map['physical_asset_id']
