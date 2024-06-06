'''
who even knows
'''
import services.airtable.airtable as airtable
import services.excel.excel as excel
from pprint import pprint, pformat
unit_asset_metadata = "/home/bcoates/code/avmpi_scripts/tests/Unit-AssetsMetadata-template20240209_tests.xlsx"
workbook = excel.load_all_worksheets(unit_asset_metadata)
sheet = workbook['Assets-Unit-Provided-template']
for row in sheet:
    print(row)
    atbl_rec = airtable.PhysicalAssetRecord().from_xlsx(sheet[row])
    input(pformat(atbl_rec.to_record()))
    atbl_rec.send()
