'''
utility functions
'''
import subprocess
import logging
from typing import Optional

logger = logging.getLogger('main_logger')


def run_command(cmd: str | list, return_output: bool = False) -> Optional[str]:
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
