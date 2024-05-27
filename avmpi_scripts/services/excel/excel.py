'''
handles all things Excel / xlsx for AVMPI
'''
import logging
import pathlib
import json
import openpyxl
from openpyxl.utils import get_column_letter


logger = logging.getLogger('main_logger')


def load_field_mappings():
    '''
    loads field mappings from config
    '''
    module_dirpath = pathlib.Path(__file__).parent.parent.parent.absolute()
    field_mappings_path = module_dirpath / "field_mappings.json"
    with open(field_mappings_path, "r") as field_mappings_file:
        field_mapping = json.load(field_mappings_file)
    return field_mapping


def load_all_worksheets(filepath):
    '''
    loads all worksheets from xlsx at filepath into dictionary
    where each key is the worksheet name
    and each value is a list of rows, which themselves are dictionaries
    of key: value paires where the key is the column letter and value is cell value
    '''
    logger.debug(f"loading Excel spreadsheet from {filepath}...")
    workbook = openpyxl.load_workbook(filepath)
    sheets_data = {}
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        rows_dict = {}
        for row_index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            row_data = {}
            for column_index, cell_value in enumerate(row, start=1):
                column_letter = get_column_letter(column_index)
                row_data[column_letter] = cell_value
            rows_dict[row_index] = row_data
        sheets_data[sheet_name] = rows_dict
    return sheets_data


def validate_row(row, required_columns):
    '''
    validates an individual row against its required columns
    '''
    missing_values = []
    for req_col in required_columns:
        if not row[req_col]:
            missing_values.append(req_col)
    return missing_values


def validate_required_fields(rows, obj_type):
    '''
    uses rules in field_mappings.json to validate sheet_dict
    '''
    logger.debug("validating worksheet...")
    _field_map = load_field_mappings()
    print(_field_map)
    field_map = _field_map[obj_type]
    required_columns = []
    missing_values = []
    for field, mapping in field_map.items():
        print(f"field: {field}")
        print(f"mapping: {mapping}")
        try:
            assert mapping['xlsx']['required']
        except (KeyError, TypeError):
            continue
        if mapping['xlsx']['required']:
                required_columns.append(mapping['xlsx']['column'])
    for row in rows:
        missing_columns = validate_row(row, required_columns)
        if missing_columns:
            missing_values.append({"row": rows.index(row), "columns": miss_cols})
    return missing_values
