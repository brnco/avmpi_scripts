'''
object classes for files on disk
'''
import json
import logging
import pathlib
import services.airtable.airtable as airtable


logger = logging.getLogger('main_logger')


def get_field_map(obj_type: str) -> dict:
    '''
    returns dictionary of field mappings for Excel <-> BWF Metadata
    '''
    module_dirpath = pathlib.Path(__file__).parent.absolute()
    field_map_filepath = module_dirpath / 'field_mappings.json'
    with open(field_map_filepath, 'r') as field_map_file:
        field_mapping = json.load(field_map_file)
    return field_mapping[obj_type]


class BWFDescription(object):
    '''
    BWF Description field is a mess so it gets its own class
    '''

    @classmethod
    def from_atbl(cls, digital_asset_id: str):
        '''
        creates BWF Description from Digital Asset Airtable record
        '''
        instance = cls()
        field_map = get_field_map('BWFDescription')
        atbl_base = airtable.connect_one_base("Assets")
        atbl_tbl = atbl_base['Digital Assets']
        atbl_rec_digital_asset = airtable.find(digital_asset_id, "Digital Asset ID", atbl_tbl, True)
        if not atbl_rec_digital_asset:
            raise RuntimeError(f"no records found for Digital Asset ID {digital_asset_id}")
        for field, mapping in field_map.items():
            try:
                if 'atbl' in mapping:
                    pass
            except (KeyError, TypeError):
                continue
            try:
                value = atbl_rec_digital_asset['fields'][mapping['atbl']['name']]
            except Exception:
                raise RuntimeError(f"returned Digital Asset Record missing field {field}")
            try:
                value = mapping['atbl']['prefix'] + str(value)
            except (KeyError, TypeError):
                pass
            setattr(instance, field, value)
        every_descriptor = []
        for field in field_map.keys():
            try:
                value = getattr(instance, field)
            except Exception:
                pass
            every_descriptor.append(value)
        print(every_descriptor)
        description = '; '.join(every_descriptor)
        setattr(instance, "Description", description[:256])
        return instance
            

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
                           'History', 'IARL', 'ICOP', 'ICRD', 'INAM',
                           'ITCH', 'ISFT', 'ISRC']
        optional_fields = ['UMID', 'timeReference', 'ICMT', 'IENG', 'IKEY',
                           'ISBJ', 'ISRF']
        for attr_name in required_fields:
            try:
                setattr(self, attr_name, kwargs[attr_name])
            except Exception:
                pass
        for attr_name in optional_fields:
            try:
                setattr(self, attr_name, kwargs[attr_name])
            except Exception:
                pass

    @classmethod
    def from_xlsx(cls, row: dict):
        '''
        creates BWF object from a row in Excel metadata template
        '''
        field_map = get_field_map('BroadcastWaveFile')
        instance = cls()
        for attr_name, mapping in field_map.items():
            try:
                column = mapping['xlsx']['column']
            except TypeError:
                column = mapping['xlsx']
            except Exception as exc:
                raise RuntimeError(exc)
            value = row[column]
            if not value:
                continue
            try:
                setattr(instance, attr_name, value)
            except Exception as exc:
                logger.error(f"attr_name: {attr_name}")
                logger.error(f"type(attr_name): {type(attr_name)}")
                logger.error(f"value: {value}")
                logger.error(f"type(value): {type(value)}")
                logger.error(exc, stack_info=True)
                raise RuntimeError("there was a problem parsing that value")
        return instance

    @classmethod
    def from_atbl(cls, digital_asset_id: str):
        '''
        gets BWF metadata from Digital Asset Record
        '''
        field_map = get_field_map('BroadcastWaveFile')
        instance = cls()
        # post_process_fields = ['Originator', 'originatorReference', 'ISRF']
        atbl_base = airtable.connect_one_base("Assets")
        atbl_tbl = atbl_base['Digital Assets']
        # results = atbl_tbl.first()
        atbl_rec_digital_asset = airtable.find(digital_asset_id, "Digital Asset ID", atbl_tbl, True)
        if not atbl_rec_digital_asset:
            raise RuntimeError(f"no records found for Digital Asset ID {digital_asset_id}")
        for field, mapping in field_map.items():
            try:
                if mapping['atbl']:
                    pass
            except KeyError: 
                if field == 'Description':
                    bwf_description = BWFDescription().from_atbl(digital_asset_id)
                    value = getattr(bwf_description, "Description")
                    setattr(instance, field, value)
                    continue
            except TypeError:
                continue
            try:
                value = atbl_rec_digital_asset['fields'][mapping['atbl']]
            except KeyError:
                continue
            if isinstance(value, list):
                if len(value) == 1:
                    value = value[0]
            setattr(instance, field, value.replace("\n", ""))
        setattr(instance, 'OriginationDate', 'TIMESTAMP')
        setattr(instance, 'OriginationTime', 'TIMESTAMP')
        return instance

    def to_bwf_meta_str(self) -> str:
        '''
        converts attributes into string that can be read by BWF MetaEdit
        '''
        bwf_meta_str = ''
        for attr_name, value in self.__dict__.items():
            chunk_str = '--' + attr_name + '="' + value + '" '
            bwf_meta_str += chunk_str
        return bwf_meta_str.strip()

    def to_bwf_meta_list(self) -> list:
        '''
        convert attributes into list for subprocess implementaiton of BWF MetaEdit
        '''
        bwf_meta_list = []
        for attr_name, value in self.__dict__.items():
            chunk_str = '--' + attr_name
            chunk = [chunk_str, value]
            bwf_meta_list.extend(chunk)
        return bwf_meta_list
