'''
takes metadata form Airtable and pops it into WAVE files
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
import files
import services.airtable.airtable as airtable
import services.excel.excel as excel


def embed_bwf(path, metadata):
    '''
    actually embeds the metadata to file at path

    metadata here is a list of BWFMetaEdit flags
    '''
    cmd = "bwfmetaedit " + metadata + " " + str(path)
    util.run_command(cmd)


def process_rows(rows, kwvars):
    '''
    processes the rows for eventual embedding
    '''
    if kwvars['input_validation']:
        # validate it
        logger.debug("validating sheet against required fields...")
        missing_fields = excel.validate_required_fields(list(rows.values()), 'BroadcastWaveFile')
        if missing_fields:
            logger.error(pformat(missing_fields))
            raise ValueError("Excel file is missing required fields")
        logger.debug("validation complete")
    # parse each row to BroadcastWaveFile object, send for embedding
    logger.info("parsing row to BWF...")
    for row in rows:
        logger.debug(pformat(rows[row]))
        bwf = files.BroadcastWaveFile().from_xlsx(rows[row])
        wav_path = pathlib.Path(rows[row]['A'])
        '''
        if not wav_path.exists():
            raise FileNotFoundError(f"no file found at path {wav_path}")
        '''
        embed_bwf(str(wav_path), bwf.to_bwf_meta_list())


def load_bwf_md_from_excel(kwvars):
    '''
    loads bwf metadata from excel sheet
    '''
    workbook = excel.load_all_worksheets(kwvars['input'])
    sheet = workbook['Fields_InUse']
    if not kwvars['row']:
        rows = sheet
    else:
        try:
            rows = {kwvars['row']: sheet[kwvars['row']]}
        except KeyError:
            raise RuntimeError(f"specified row {kwvars['row']} is empty or does not exist")
    return rows


def embed_metadata(kwvars):
    '''
    manages the process of embedding metadata
    '''
    logger.info("preparing to embed metadata into wave files...")    
    if kwvars['input']:
        rows = load_bwf_md_from_excel(kwvars)
        process_rows(rows, kwvars)
    elif kwvars['daid']:
        bwf = files.BroadcastWaveFile().from_atbl(kwvars['daid'])
        logger.info(pformat(bwf.__dict__))
        if kwvars['dadir']:
            wav_path = pathlib.Path(kwvars['dadir'])
        else:
            wav_path = os.getcwd()
            wav_path = pathlib.Path(wav_path)
        wav_name = kwvars['daid']
        wav_fullpath = wav_path / wav_name
        embed_bwf(wav_fullpath, bwf.to_bwf_meta_str())


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
    try:
        kwvars['input'] = pathlib.Path(args.input)
    except TypeError:
        kwvars['input'] = None
    kwvars['row'] = args.row
    kwvars['daid'] = args.daid
    kwvars['dadir'] = args.dadir
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
    parser.add_argument('-i', '--input', dest='input',metavar='',
                        help="the input Excel spreadsheet")
    parser.add_argument('--no_validation', dest='no_validation', action='store_true', default=False, 
                        help="overrides the validation of required fields for input Excel xlsx files")
    parser.add_argument('-r', '--row', dest='row', default=0, type=int,
                        help="uploads an individual row by row number, e.g. -r 5 will upload row 5")
    parser.add_argument('-daid', '--digital_asset_id', dest='daid', default=None,
                        help="the Digital Asset ID we would like to embed metadata for")
    parser.add_argument('-dadir', '--digital_asset_directory', dest='dadir', default=None,
                        help="the directory where the Digital Asset is located")
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
    logger.info("embed_md has completed successfully")

if __name__ == "__main__":
    main()
