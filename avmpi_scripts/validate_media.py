'''
uses MediaConch to validate media files
'''
import os
import logging
import pathlib
import subprocess
import argparse
import make_log
import util


def run_mediaconch(media_fullpath, policy_fullpath):
    '''
    actually calls MediaConch and handles output
    '''
    cmd = ["mediaconch", "-p", policy_fullpath, media_fullpath]
    util.run_command(cmd)


def validate_media(kwvars):
    '''
    manages the process of validating media files with MediaConch
    '''
    logger.info(f"validating {kwvars['daid']}...")
    if kwvars['dadir']:
        media_path = pathlib.Path(kwvars['dadir'])
    else:
        media_path = os.getcwd()
        logger.warning(f"no Digital Asset Directory (-dadir) supplied, using current working directory: {media_path}")
        media_path = pathlib.Path(media_path)
    media_name = kwvars['daid']
    media_fullpath = media_path / media_name
    policy_fullpath = pathlib.Path(kwvars['policy'])
    run_mediaconch(media_fullpath, policy_fullpath)


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
    if not args.daid:
        raise RuntimeError("no Digital Asset ID (-daid) supplied, exiting...")
    kwvars['daid'] = args.daid
    kwvars['dadir'] = args.dadir
    if not args.policy:
        raise RuntimeError("no MediaConch Policy (-p) supplied, exiting...")
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
                        help="the MediaConch policy that we want to validate against")
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
