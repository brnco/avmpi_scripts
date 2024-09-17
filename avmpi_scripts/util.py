'''
utility functions
'''
import os
import pathlib
import subprocess
import logging


logger = logging.getLogger('main_logger')


def run_command(cmd, return_output=False):
    '''
    wrapper for subprocess.run(), basically
    '''
    logger.info(f"running command: {cmd}")
    try:
        if isinstance(cmd, list):
            shell = False
        elif isinstance(cmd, str):
            shell = True
        output = subprocess.run(cmd, shell=shell, capture_output=True)
        if not output.returncode == 0:
            logger.error(f"return code: {output.returncode}")
            logger.error(f"stderr: {output.stderr.decode('utf-8')}")
            logger.error(f"stdout: {output.stdout.decode('utf-8')}")
            raise RuntimeError("there was a problem running that command")
        else:
            if return_output:
                return output.stdout.decode('utf-8')
    except Exception as exc:
        logger.error(exc, stack_info=True)
        raise RuntimeError("the script encountered a problem while tyring to run that command")


def get_downloads_path():
    '''
    returns Pathlib.Path of user's Downloads folder
    '''
    if os.name == 'nt':
        # Windows
        downloads = pathlib.Path(os.getenv('USERPROFILE')) / "Downloads"
    elif os.name == 'posix':
        # 'nix-like
        home = pathlib.Path.home()
        if (home / 'Downloads').exists():
            downloads = home / "Downloads"
        else:
            downloads = pathlib.Path(
                    os.getenv('XDG_DOWNLOAD_DIR'),
                    home / "Downloads")
    else:
        raise RuntimeError("unable to identify Downloads directory")
    return downloads


def is_only_filename_with_extension(path):
    '''
    checks if path is filename.ext
    '''
    path = pathlib.Path(path)
    return path.parent == pathlib.Path() and \
            path.stem != "" and path.suffix != ""
