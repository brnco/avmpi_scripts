'''
handles testing of excel.py
'''
import pytest
import pathlib
from pprint import pformat
import avmpi_scripts.services.excel.excel as excel
'''
write a fixture here
where the path to the worksheets changes if run with tox vs run with pytest
good luck
'''


def test_load_all_worksheets():
    parent_dir = pathlib.Path(__file__).parent.absolute()
    unit_filepath = parent_dir / 'Unit-AssetsMetadata-template20240209_tests.xlsx'
    vendor_filepath = parent_dir / 'Vendor-AssetsMetadata-template20240307_tests.xlsx'
    unit_sheet = excel.load_all_worksheets(unit_filepath)
    print(unit_sheet['Assets-Unit-Provided-template'][5])
    assert unit_sheet['Assets-Unit-Provided-template'][5]['A'] == 'NMAI_019_33901000000018'
    vendor_sheet = excel.load_all_worksheets(vendor_filepath)
    assert vendor_sheet['Digital Assets'][4]['A'] == 'aaa_spernanc_31027000938700_cass1of2_side2.wav'


def test_load_field_mapping():
    module_dir = pathlib.Path(__file__).parent.parent.absolute()
    field_mapping = excel.load_field_mappings()
    print(pformat(field_mapping))
    assert field_mapping['DigitalAssetRecord'] is not None


def test_validate_required_fields():
    parent_dir = pathlib.Path(__file__).parent.absolute()
    unit_filepath = parent_dir / 'Unit-AssetsMetadata-template20240209_tests.xlsx'
    workbook = excel.load_all_worksheets(unit_filepath)
    rows = [workbook['Assets-Unit-Provided-template'][5]]
    missing_fields = excel.validate_required_fields(rows, 'PhysicalAssetRecord')
    assert not missing_fields
