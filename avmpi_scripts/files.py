'''
object classes for files on disk
'''
import logging

logger = logging.getLogger('main_logger')

class BroadcastWaveFile(object):
    '''
    class for BWF WAVE

    BWF fields - required:
    Description
    Originator
    Origination Date
    Origination Time
    Originator Reference
    Version
    Coding History
    IARL
    ICOP
    ICRD
    INAM
    ITCH
    ISFT
    ISRC

    BWF fields - optional:
    UMID
    Time Reference
    ICMT
    IENG
    IKEY
    ISBJ
    ISRF
    '''
    def __init__(self, **kwargs):
        required_fields = ['Description', 'Originator', 'originationDate',
                           'originationTime', 'originatorReference', 'Version',
                           'codingHistory', 'IARL', 'ICOP', 'ICRD', 'INAM',
                           'ITCH', 'ISFT', 'ISRC']
        optional_fields = ['UMID', 'timeReference', 'ICMT', 'IENG', 'IKEY',
                           'ISBJ', 'ISRF']
        for attr_name in required_fields:
            try:
                setattr(self, attr_name, kwargs[attr_name])
            except Exception as exc:
                pass
        for attr_name in optional_fields:
            try:
                setattr(self, attr_name, kwargs[attr_name])
            except Exception:
                pass

    def to_bwf_meta_str(self):
        '''
        converts attributes into string that can be read by BWF MetaEdit
        '''
        bwf_meta_str = ''
        for attr_name, value in self.__dict__.items():
            chunk_str = '--' + attr_name + '="' + value + '" '
            bwf_meta_str += chunk_str
        return bwf_meta_str.strip()

    def to_bwf_meta_list(self):
        '''
        convert attributes into list for subprocess implementaiton of BWF MetaEdit
        '''
        bwf_meta_list = []
        for attr_name, value in self.__dict__.items():
            chunk_str = '--' + attr_name
            chunk = [chunk_str, value]
            bwf_meta_list.extend(chunk)
        return bwf_meta_list

