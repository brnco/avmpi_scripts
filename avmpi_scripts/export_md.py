'''
exports metadata from Airtable to CSV format
'''
import configparser
import argparse
import os
import pathlib
import logging
import subprocess
import csv
from pprint import pformat
import make_log
import util
import services.airtable.airtable as airtable


def make_output_path(args):
    '''
    creates the output path for the csv
    '''
    if args.output:
        output = args.output
    else:
        downloads = util.get_downloads_path()
        if not args.view:
            excel_path = pathlib.Path(args.excel_input)
            filename = pathlib.Path(excel_path.name)
            filename = filename.with_suffix(".csv")
        else:
            filename = args.view + ".csv"
        output = downloads / filename
    output_is_only_filename = util.is_only_filename_with_extension(output)
    if output_is_only_filename:
        downloads = util.get_downloads_path()
        output = downloads / output
    return output


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
    if args.no_validation:
        kwvars['input_validation'] = False
    else:
        kwvars['input_validation'] = True
    if not args.view and not args.excel_input:
        raise RuntimeError("no view and no excel input file provided. too many records to export. exiting...")
    kwvars['excel_input'] = args.excel_input
    kwvars['view'] = args.view
    kwvars['output'] = make_output_path(args)
    
    return kwvars


def init_args():
    '''
    initializes the arguments form command line
    '''
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-q', '--quiet', dest='quiet',
                        action='store_true', default=False,
                        help="run script in quiet mode. "
                        "only print warnings and errors to command line")
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true', default=False,
                        help="run script in verbose mode. "
                        "print all log messages to the command line")
    parser.add_argument('--no-validation', dest='no_validation',
                       action='store_true', default=False,
                       help="overrides the validation "
                       "of required fields for the table")
    parser.add_argument('--view', dest='view', default=None,
                        help="the view we want to export from. "
                        "you must provide a view or an excel_input")
    parser.add_argument('--excel_input', dest='excel_input',
                        default=None,
                        help="for batched records, "
                        "the input Excel file that you want "
                        "exported from Airtable")
    parser.add_argument('-o', '--output', dest='output',
                        default=None,
                        help="the output file path and name"
                        "where we want to write to. "
                        "the default save path is "
                        "your Downloads folder. "
                        "the default file name is "
                        "the same as the view's name (.csv)")
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
    logger.info(pformat(kwvars))
    # export_metadata(kwvars)
    logger.info("export_md has completed successfully")


if __name__ == "__main__":
    main()
