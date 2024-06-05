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
    else:
        raise RuntimeError("there was a problem identifying relevant record type, " 
                            "probably because of the sheet name")
    return record_type
    

def excel_to_airtable(kwvars):
    '''
    manages the upload of an Excel sheet to Airtable
    '''
    logger.info("preparing to upload Excel metadata to Airtable...")
    # get the spreadsheet
    workbook = excel.load_all_worksheets(kwvars['input'])
    for sheet_name, rows in workbook.items():
        record_type = get_record_type_from_sheet(sheet_name)
        if not kwvars['override_excel_validation']:
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
            logger.info("sending record to Airtable...")
            for atbl_rec in atbl_recs:
                atbl_rec.send()
                '''
                you need to figure out how to save when a record si linked to an unsaved record
                and also handle when there's a record that links to a sync'd table,
                and the value in the record doesn't exist in the sync
                '''


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
    if args.oev:
        kwvars['override_excel_validation'] = True
    else:
        kwvars['override_excel_validation'] = False
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
    parser.add_argument('--override_excel_validation', dest='oev', action='store_true', default=False, 
                        help="overrides the validation of required fields for input Excel xlsx files")
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

if __name__ == "__main__":
    main()
