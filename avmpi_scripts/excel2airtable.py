'''
uploads metadata in Excel spreadsheets to Airtable
'''
import configparser
import argparse
import os
import pathlib
import logging
from pprint import pformat
import make_log
import services.airtable.airtable as airtable
import services.excel.excel as excel


def get_record_type_from_sheet(sheet_name):
    '''
    with given sheet name
    return name of class of related Airtable record
    '''
    if sheet_name == 'Physical Assets':
        record_type = 'PhysicalAssetActionRecord'
    elif sheet_name == 'Digital Assets':
        record_type = 'DigitalAssetRecord'
    elif sheet_name == 'Assets-Unit-Provided-template':
        record_type = 'PhysicalAssetRecord'
    elif sheet_name == 'PhysicalFormats':
        record_type = None
    else:
        raise RuntimeError("there was a problem identifying relevant record type, " 
                            "probably because of the sheet name")
    return record_type
    

def process_rows(rows, record_type, kwvars):
    '''
    processes row(s) in sheet
    '''
    if kwvars['input_validation']:
        # validate it
        logger.debug("validating sheet against required fields...")
        missing_fields = excel.validate_required_fields(list(rows.values()), record_type)
        if missing_fields:
            logger.error(pformat(missing_fields))
            raise ValueError("Excel file is missing required fields")
        logger.debug("validation complete")
    # parse each row to AirtableRecord() object
    logger.info("parsing row to Airtable record...")
    for row in rows:
        logger.debug(pformat(rows[row]))
        if record_type == "PhysicalAssetRecord":
            atbl_rec = airtable.PhysicalAssetRecord().from_xlsx(rows[row])
            atbl_recs = [atbl_rec]
        elif record_type == "DigitalAssetRecord":
            atbl_rec = airtable.DigitalAssetRecord().from_xlsx(rows[row])
            atbl_recs = [atbl_rec]
        else:
            atbl_rec = airtable.PhysicalAssetActionRecord().from_xlsx(rows[row])
            # Physical Asset Action rows can have multiple records
            atbl_recs = airtable.parse_asset_actions(atbl_rec)
        for atbl_rec in atbl_recs:
            logger.info("sending record to Airtable...")
            logger.info(pformat(atbl_rec.__dict__))
            input("press any key to upload")
            atbl_rec.send()
            logger.info("row processed successfully")


def excel_to_airtable(kwvars):
    '''
    manages the upload of an Excel sheet to Airtable
    '''
    logger.info("preparing to parse Excel metadata to Airtable...")
    # get the spreadsheet
    workbook = excel.load_all_worksheets(kwvars['input'])
    if kwvars['sheet']:
        sheet = workbook[kwvars['sheet']]
        record_type = get_record_type_from_sheet(kwvars['sheet'])
        if not record_type:
            return
        if not kwvars['row']:
            rows = sheet
        else:
            try:
                rows = {kwvars['row']: sheet[kwvars['row']]}
            except KeyError:
                raise RuntimeError(f"specified row {kwvars['row']} is empty or does not exist")
        process_rows(rows, record_type, kwvars)
    else:
        for sheet_name, rows in workbook.items():
            record_type = get_record_type_from_sheet(sheet_name)
            if not record_type:
                continue
            process_rows(rows, record_type, kwvars)
        


def parse_args(args):
    '''
    returns dictionary of arguments parsed for our use
    '''
    kwvars = {}
    if args.quiet:
        kwvars['loglevel_print'] = logging.WARNING
    elif args.verbose:
        kwvars['loglevel_print'] = logging.DEBUG
    else:
        kwvars['loglevel_print'] = logging.INFO
    kwvars['input'] = pathlib.Path(args.input)
    if args.no_validation:
        kwvars['input_validation'] = False
    else:
        kwvars['input_validation'] = True
    kwvars['sheet'] = args.sheet
    kwvars['row'] = args.row
    return kwvars


def init_args():
    '''
    initializes the arguments from the command line
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-q', '--quiet', dest='quiet',
                        action='store_true', default=False,
                        help="run script in quiet mode. "
                        "only print warnings and errors to command line")
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true', default=False,
                        help="run script in verbose mode. "
                        "print all log messages to command line")
    parser.add_argument('-i', '--input', dest='input',
                        metavar='',
                        help="the input spreadsheet to upload")
    parser.add_argument('--no_validation', dest='no_validation', action='store_true', default=False, 
                        help="overrides the validation of required fields for input Excel xlsx files")
    parser.add_argument('-s', '--sheet', dest='sheet', default=None,
                        help="uploads an individual sheet by name, e.g. Assets-Unit-Provided-template")
    parser.add_argument('-r', '--row', dest='row', default=0, type=int,
                        help="uploads an individual row by row number, e.g. -r 5 will upload row 5")
    args = parser.parse_args()
    return args
                            

def main():
    '''
    do the thing
    '''
    print("starting...")
    args = init_args()
    kwvars = parse_args(args)
    global logger
    logger = make_log.init_log(loglevel_print=kwvars['loglevel_print'])
    excel_to_airtable(kwvars)
    logger.info("excel2airtable has completed successfully")

if __name__ == "__main__":
    main()
