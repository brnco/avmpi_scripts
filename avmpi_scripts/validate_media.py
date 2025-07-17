'''
uses MediaConch to validate media files
'''
import os
import json
import logging
import pathlib
import subprocess
import argparse
from pprint import pformat
import services.airtable.airtable as airtable
import make_log
import util
from typing import Optional

def config() -> dict:
    '''
    creates/ returns config object for MediaConch/ validation setup
    validate_media_config.json located in same dir as this script
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    with open(this_dirpath / 'validate_media_config.json', 'r') as config_file:
        validation_config = json.load(config_file)
    return validation_config


def run_mediaconch(media_fullpath: pathlib.Path, policy_fullpath: pathlib.Path) -> bool | str:
    '''
    actually calls MediaConch and handles output

    returncode == 0 means that MC ran on the file
    returncode == 1 means that MC had a problem, like file didn't exist

    output.stdout == True when MC runs successfully
    output.stdout == False when MC has a problem
    output.stderr == True when MC has a problem

    output.stdout.startswith('pass') when file passes
    output.stdout.startswith('fail') when file fails
    '''
    cmd = ["mediaconch", "-p", str(policy_fullpath), str(media_fullpath)]
    output = util.run_command(cmd, return_output=True)
    if output.startswith('pass'):
        logger.info(f"file {media_fullpath.name} passed validation")
        return True
    elif output.startswith('fail'):
        logger.info(f"file {media_fullpath.name} failed validation")
        return output
    else:
        raise RunetimeError("the script encountered an error trying to validate that file")


def get_linked_digital_asset_record(daid: str, atbl_base: pyairtable.Base):
    '''
    QC Log table links to digital asset table
    we need to pop record_id from Digital Assets record into QC Log, for new records
    '''
    atbl_tbl = atbl_base['Digital Assets']
    result = airtable.find(daid, "Digital Asset ID", atbl_tbl, True)
    if result:
        return result
    else:
        raise RuntimeError(f"no asset found in {atbl_tbl} with Digital Asset ID {daid}")


def send_results_to_airtable(passes, fails):
    '''
    actually sends the results of the validation to Airtable QC Log
    '''
    logger.info("sending results to Airtable...")
    atbl_base = airtable.connect_one_base('Assets')
    atbl_tbl = atbl_base['QC Log']
    for passed_file in passes:
        result = airtable.find(passed_file['daid'], "Digital Asset", atbl_tbl, True)
        if result:
            logger.info(f"updating QC Log record for {passed_file['daid']}")
            atbl_tbl.update(result['id'], {"MediaConch": ["Pass"], "QC Issues": ""})
        else:
            logger.info(f"creating new QC Log record for {passed_file['daid']}")
            atbl_rec_digital_asset = get_linked_digital_asset_record(passed_file['daid'], atbl_base)
            atbl_tbl.create({"Digital Asset": [atbl_rec_digital_asset['id']],
                             "MediaConch": ["Pass"], "QC Issues": ""})
    for failed_file in fails:
        result = airtable.find(failed_file['daid'], "Digital Asset", atbl_tbl, True)
        if result:
            logger.info(f"updating QC Log record for {failed_file['daid']}")
            atbl_tbl.update(result['id'], {"MediaConch": ["Fail"], "QC Issues": failed_file['log']})
        else:
            logger.info(f"creating new QC Log record for {failed_file['daid']}")
            atbl_rec_digital_asset = get_linked_digital_asset_record(failed_file['daid'], atbl_base)
            atbl_tbl.create({"Digital Asset": [atbl_rec_digital_asset['id']],
                             "MediaConch": ['Fail'], "QC Issues": failed_file['log']})


def detect_policy_for_file(file, conf):
    '''
    determines which policy in config to use for which file
    '''
    file_path = pathlib.Path(file)
    policies = conf['policies']
    file_ext = file_path.suffix
    try:
        file_validation_policy = policies[file_ext]
    except Exception:
        raise RuntimeError(f"No policy specified for {file_ext} for file {str(file_path)}")
    return pathlib.Path(file_validation_policy)


def get_files_to_validate(folder_path):
    '''
    if we're running this in batch mode
    we need to get every file with .mkv or .dv extension
    '''
    if not folder_path.is_dir():
        raise RuntimeError(f"supplied directory {folder_path} does not exist")
    extensions_to_check = [".mkv", ".dv"]
    files_to_check = []
    all_files = []
    for ext in extensions_to_check:
        files_w_this_ext = folder_path.glob('**/*' + ext)
        all_files.extend(files_w_this_ext)
    files_to_check = [file for file in all_files if not file.name.startswith('.')]
    return files_to_check


def review_failed_files(failed_files):
    '''
    UX for reviewing the files that failed validation
    '''
    rev_fails = []
    rev_passes = []
    for failed_file in failed_files:
        _log_lst = failed_file['log'].split("  --  ")
        log_list = [x.strip() for x in _log_lst]
        logger.warning(f"Digital Asset ID: {failed_file['daid']}")
        logger.warning(pformat(log_list))
        while True:
            user_input = input("press F to Fail this file, press P to Pass it: ").upper()
            if user_input not in ['F', 'P']:
                print("invalid choice, please type F or P")
            else:
                break
        if user_input == "F":
            rev_fails.append(failed_file)
        else:
            rev_passes.append({"daid": failed_file['daid']})
    return rev_passes, rev_fails


def validate_media(kwvars):
    '''
    manages the process of validating media files with MediaConch
    '''
    conf = config()
    fails = []
    passes = []
    if not kwvars['daid']:
        logger.info(f"validating every file in {kwvars['dadir']}")
        files_to_validate = get_files_to_validate(kwvars['dadir'])
        logger.info(f"found {len(files_to_validate)} files to validate")
    else:
        if kwvars['dadir']:
            media_path = pathlib.Path(kwvars['dadir'])
        else:
            media_path = os.getcwd()
            logger.warning(f"no Digital Asset Directory (-dadir) supplied, using current working directory: {media_path}")
            media_path = pathlib.Path(media_path)
        files_to_validate = [media_path / kwvars['daid']]
    for file in files_to_validate:
        if kwvars['policy']:
            policy_fullpath = pathlib.Path(kwvars['policy'])
        else:
            policy_fullpath = detect_policy_for_file(file, conf)
        logger.info(f"validating {file}...")
        result = run_mediaconch(file, policy_fullpath)
        if result is not True:
            fails.append({"daid": file.name, "log": result})
        else:
            passes.append({"daid": file.name})
    if fails:
        logger.warning(f"{len(fails)} of {len(files_to_validate)} files failed validation")
        while True:
            user_input = input("Do you want to review the failed files? y/n ").lower()
            if user_input not in ['y', 'n']:
                print("invalid choice, please type y or n")
            else:
                break
        if user_input == 'y':
            reviewed_passes, reviewed_fails = review_failed_files(fails)
            passes.extend(reviewed_passes)
        else:
            reviewed_fails = fails
            reviewed_passes = passes
    else:
        reviewed_fails = []
        reviewed_passes = passes
    formatted_passes = [item['daid'] for item in passes]
    formatted_fails = [item['daid'] for item in fails]
    logger.info("here's the Digital Asset IDs for passing files:")
    logger.info(pformat(formatted_passes))
    input("press any key to continue")
    logger.info("here's the Digital Asset IDs for failing files:")
    logger.info(pformat(formatted_fails))
    input("press any key to continue")
    send_results_to_airtable(reviewed_passes, reviewed_fails)


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
    kwvars['daid'] = args.daid
    if args.dadir:
        kwvars['dadir'] = pathlib.Path(args.dadir)
    else:
        kwvars['dadir'] = None
    kwvars['policy'] = args.policy
    return kwvars


def init_args():
    '''
    initializes arguments from the command line
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
    parser.add_argument('-daid', '--digital_asset_id', dest='daid', default=None,
                        help="the Digital Asset ID we would like to embed metadata for")
    parser.add_argument('-dadir', '--digital_asset_directory', dest='dadir', default=None,
                        help="the directory where the Digital Asset is located")
    parser.add_argument('-p', '--policy', dest='policy', default=None,
                        help="the MediaConch policy that we want to validate against\n"
                        "leave out this option and the script will auto-detect the policy\n"
                        "based on the file extension in validate_media_config.json")
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
    validate_media(kwvars)
    logger.info("embed_md has completed successfully")


if __name__ == '__main__':
    main()
