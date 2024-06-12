'''
utility functions
'''
import subprocess
import logging


logger = logging.getLogger('main_logger')


def run_command(cmd, return_output=False):
    '''
    wrapper for subprocess.run(), basically
    '''
    logger.info(f"running command: {cmd}")
    try:
        output = subprocess.run(cmd, shell=True, capture_output=True)
        if not output.returncode == '0':
            logger.error(f"return code: {output.returncode}")
            logger.error(f"error description: {output.stderr.decode('utf-8')}")
            raise RuntimeError("there was a problem running that command")
        else:
            if return_output:
                return output.stdout.decode('utf-8')
    except Exception as exc:
        logger.error(exc, stack_info=True)
        raise RuntimeError("the script encountered a problem while tyring to run that command")
