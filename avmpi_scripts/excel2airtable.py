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
import services.excel.excel as excel


def excel_to_airtable(kwvars):
    '''
    manages the upload of an Excel sheet to Airtable
    '''
    logger.info("preparing to upload Excel metadata to Airtable...")
    # get the spreadsheet
    workbook = excel.load_all_worksheets(kwvars['input'])
    for sheet_name, rows in workbook.items():
        # validate it
        logger.debug("validating sheet against required fields...")
        missing_fields = excel.validate_required_fields(list(rows.values()), kwvars['obj_type'])
        if missing_fields:
            logger.error(pformat(missing_fields))
            raise ValueError("Excel file is missing required fields")


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
    kwvars['obj_type'] = args.obj_type
    if kwvars['obj_type'] == 'DigitalAsset':
        kwvars['sheets'] = ['Physical Assets', 'Digital Assets']
    elif kwvars['obj_type'] == 'Physical Asset':
        kwvars['sheets'] = ['Assets-Unit-Provided-template']
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
    parser.add_argument('--obj_type', dest='obj_type', default=False, required=True,
                        choices=['PhysicalAssetRecord', 'DigitalAssetRecord'],
                        help="the type of object we're uploading metadata about")
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
