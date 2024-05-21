'''
handles testing of excel.py
'''
import pytest
import pathlib
import avmpi_scripts.excel as excel

def test_load_all_worksheets_dict():
    parent_dir = pathlib.Path('__file__').parent.parent.absolute()
    unit_filepath = parent_dir / 'Unit-AssetsMetadata-template20240209_tests.xlsx'
    vendor_filepath = parent_dir / 'Vendor-AssetsMetadata-template20240307_tests.xlsx'
    unit_sheet = excel.load_all_worksheets_dict(unit_filepath)
    print(unit_sheet['Assets-Unit-Provided-template'][5])
    assert unit_sheet['Assets-Unit-Provided-template'][5]['A'] == 'NMAI_019_33901000000018'
    vendor_sheet = excel.load_all_worksheets_dict(vendor_filepath)
    assert vendor_sheet['Digital Assets'][4]['A'] == 'aaa_spernanc_31027000938700_cass1of2_side2.wav'
