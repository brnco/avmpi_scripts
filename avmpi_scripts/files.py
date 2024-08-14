'''
object classes for files on disk
'''
import json
import logging
import pathlib
import services.airtable.airtable as airtable


logger = logging.getLogger('main_logger')


def get_field_map(obj_type):
    '''
    returns dictionary of field mappings for Excel <-> BWF Metadata
    '''
    module_dirpath = pathlib.Path(__file__).parent.absolute()
    field_map_filepath = module_dirpath / 'field_mappings.json'
    with open(field_map_filepath, 'r') as field_map_file:
        field_mapping = json.load(field_map_file)
    return field_mapping[obj_type]


class CodingHistory(object):
    '''
    this BWF field is complicated so it gets its own object
    '''

    @classmethod
    def from_atbl(cls, digital_asset_id):
        '''
        creates coding history from Digital Asset Airtable record
        '''
        instance = cls()
        setattr(instance, 'algorithm', 'A=ANALOG')
        field_map = get_field_map('History')
        atbl_base = airtable.connect_one_base("Assets")
        atbl_tbl = atbl_base['Digital Assets']
        atbl_rec_digital_asset = airtable.find(digital_asset_id, "Digital Asset ID", atbl_tbl, True)
        txtfs_fields = ['txtfs_equipment_model', 'txtfs_equipment_sn',
                        'txtfs_speed_value', 'txtfs_speed_type']
        if not atbl_rec_digital_asset:
            raise RuntimeError(f"no records found for Digital Asset ID {digital_asset_id}")
        for field, mapping in field_map.items():
            try:
                foo = mapping['atbl']
            except (KeyError, TypeError):
                continue
            try:
                value = atbl_rec_digital_asset['fields'][mapping['atbl']['name']]
            except KeyError:
                # means this field wasn't included in response
                # i.e. this field isn't filled in
                continue
            except TypeError:
                # means this is a txtfs field
                try:
                    value = atbl_rec_digital_asset['fields'][mapping['atbl']]
                except KeyError:
                    details = "Was this created with the old workflow? Exiting..."
                    raise RuntimeError(f"not enough info to create Coding History for this asset. {details}")
            if isinstance(value, list):
                if len(value) == 1:
                    value = value[0]
                else:
                    value = ','.join(value)
            try:
                value = mapping['atbl']['prefix'] + value
            except (KeyError, TypeError):
                pass
            setattr(instance, field, value)
        _codinghistory = []
        for field in field_map.keys():
            try:
                element = getattr(instance, field)
                codinghistory.append(element)
            except Exception:
                pass
        codinghistory = '; '.join(_codinghistory)
        setattr(instance, "CodingHistory", codinghistory)
        return instance


class BWFDescription(object):
    '''
    BWF Description field is a mess so it gets its own class
    '''

    @classmethod
    def from_atbl(cls, digital_asset_id):
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
                foo = mapping['atbl']
            except (KeyError, TypeError):
                continue
            try:
                value = atbl_rec_digital_asset['fields'][mapping['atbl']['name']]
            except:
                raise RuntimeError(f"returned Digital Asset Record missing field {field}")
            try:
                value = mapping['atbl']['prefix'] + value
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
            except Exception as exc:
                pass
        for attr_name in optional_fields:
            try:
                setattr(self, attr_name, kwargs[attr_name])
            except Exception:
                pass

    @classmethod
    def from_xlsx(cls, row):
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
    def from_atbl(cls, digital_asset_id):
        '''
        gets BWF metadata from Digital Asset Record
        '''
        field_map = get_field_map('BroadcastWaveFile')
        instance = cls()
        post_process_fields = ['Originator', 'originatorReference', 'ISRF', 'codingHistory']
        atbl_base = airtable.connect_one_base("Assets")
        atbl_tbl = atbl_base['Digital Assets']
        atbl_rec_digital_asset = airtable.find(digital_asset_id, "Digital Asset ID", atbl_tbl, True)
        if not atbl_rec_digital_asset:
            raise RuntimeError(f"no records found for Digital Asset ID {digital_asset_id}")
        for field, mapping in field_map.items():
            try:
                foo = mapping['atbl']
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
                if field == 'History':
                    bwf_codhist = CodingHistory().from_atbl(digital_asset_id)
                    value = getattr(bwf_codhist, "CodingHistory")
                else:
                    continue
            if isinstance(value, list):
                if len(value) == 1:
                    value = value[0]
            setattr(instance, field, value)
        return instance

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
