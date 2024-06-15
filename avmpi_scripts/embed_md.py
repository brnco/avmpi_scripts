'''
uploads metadata in Excel spreadsheets to Airtable
'''
import configparser
import argparse
import os
import pathlib
import logging
import subprocess
from pprint import pformat
import make_log
import util
import services.airtable.airtable as airtable
import services.excel.excel as excel



def embed_bwf(path, metadata):
    '''
    actually embeds the metadata to file at path

    metadata here is a list of BWFMetaEdit flags
    '''
    cmd = ["bwfmetaedit"]
    cmd.extend(metadata)
    cmd.append(str(path))
    util.run_cmd(cmd)


def embed_metadata(kwvars):
    '''
    manages the process of embedding metadata
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
    kwvars['input_waves'] = [pathlib.Path(arg)
                             for arg in args.input
                             if '.wav' in arg.lower()]
    kwvars['input_excel'] = [arg
                             for arg in args.input
                             if '.xlsx' in arg.lower()]
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
                        metavar='', action='append',
                        help="the inputs, either AV files or Excel spreadsheet")
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
    embed_metadata(kwvars)
    logger.info("embed_mdata has completed successfully")

if __name__ == "__main__":
    main()
