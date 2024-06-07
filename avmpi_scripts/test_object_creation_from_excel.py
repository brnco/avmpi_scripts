'''
who even knows
'''
import services.airtable.airtable as airtable
import services.excel.excel as excel
from pprint import pprint, pformat
unit_asset_metadata = "/home/bcoates/code/avmpi_scripts/tests/Unit-AssetsMetadata-template20240209_tests.xlsx"
vendor_asset_metadata = "/home/bcoates/code/avmpi_scripts/tests/Vendor-AssetsMetadata-template20240307_tests.xlsx"
workbook = excel.load_all_worksheets(vendor_asset_metadata)
sheet = workbook['Digital Assets']
for row in sheet:
    print(row)
    atbl_rec = airtable.DigitalAssetRecord().from_xlsx(sheet[row])
    input(pformat(atbl_rec.to_record()))
    atbl_rec.send()
