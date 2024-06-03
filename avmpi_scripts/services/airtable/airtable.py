'''
handler for Airtable calls for AVMPI
'''
import time
import json
import pathlib
import logging
import requests
from datetime import timedelta
from pprint import pformat
from pyairtable import Api, Table
from pyairtable import metadata as atbl_mtd
from pyairtable.orm import Model, fields
from pyairtable.formulas import match


logger = logging.getLogger('main_logger')


def config():
    '''
    creates/ returns config object for Airtable setup
    airtable_config.json located in same dir as this script
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    with open(this_dirpath / 'airtable_config.json', 'r') as config_file:
        atbl_config = json.load(config_file)
    return atbl_config


def get_api_key():
    '''
    returns the airtable API key from the config file
    '''
    atbl_config = config()
    return atbl_config['main']['api_key']


def get_field_map(obj_type):
    '''
    returns dictionary of field mappings for attr <-> Airtable <-> XLSX
    for specified object type, e.g. PhysicalAssetRecord
    '''
    module_dirpath = pathlib.Path(__file__).parent.parent.parent.absolute()
    field_map_filepath = module_dirpath / 'field_mappings.json'
    with open(field_map_filepath, 'r') as field_map_file:
        field_mapping = json.load(field_map_file)
    return field_mapping[obj_type]


class AVMPIAirtableRecord:
    '''
    super class for the various AirtableRecord() classes we'll create later
    defines a few methods we'll use for all Airtable records
    notably, send() and from_xlsx()
    '''
    primary_field = None

    def _fix_problem_attrs(self, attr_name, value):
        '''
        for some of these we need an extra layer of formatting
        '''
        if 'asset_barcode' in attr_name:
            value = str(int(value))
        if attr_name == 'color' or attr_name == 'sound':
            value = [value]
        if attr_name == 'secondary_asset_id':
            value = str(value)
        if attr_name == 'asset_duration':
            if ':' in value:
                time_components = value.split(':')
                if len(time_components) == 2:
                    # assume mm:ss
                    minutes, seconds = map(int, value.split(':'))
                    value = timedelta(minutes=minutes, seconds=seconds)
                elif len(time_components) == 3:
                    # hh:mm:ss
                    hours, minutes, seconds = map(int, value.split(':'))
                    value = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        return value

    def _set_link_field(self, attr_name, value):
        '''
        sets the values for a linked field
        little bit of a hack but it works great
        '''
        atbl_api_key = get_api_key()
        atbl_api = Api(atbl_api_key)
        atbl_conf = config()
        base_id = atbl_conf['bases']['Assets']['base_id']
        if attr_name == 'DigitalAsset':
            table_name = 'Digital Assets'
            primary_key_name = 'Digital Asset ID'
            the_class = DigitalAssetRecord()
        elif attr_name == 'PhysicalAsset':
            table_name = 'Physical Assets'
            primary_key_name = 'Phsyical Asset ID'
            the_class = PhysicalAssetRecord()
        elif attr_name == 'PhysicalFormat':
            table_name = 'AV Formats'
            primary_key_name = 'Term'
            the_class = PhysicalFormatRecord()
        elif attr_name == 'Collection':
            table_name = 'Collections'
            primary_key_name = 'Collection Title'
            the_class = CollectionRecord()
        elif 'Location' in attr_name:
            table_name = 'Locations'
            primary_key_name = 'Name'
            the_class = LocationRecord()
        elif 'Container' in attr_name:
            table_name = 'Containers'
            primary_key_name = 'Container Name'
            the_class = ContainerRecord()

    @classmethod
    def from_xlsx(cls, row, field_map):
        '''
        creates an Airtable record from a row of an XLSX spreadsheet
        '''
        instance = cls()
        problem_attrs = ['asset_barcode', 'color', 'sound', 'asset_duration',
                         'secondary_asset_id', 'physical_asset_barcode']
        link_field_attrs = ['DigitalAsset', 'PhysicalAsset', 'PhysicalFormat',
                            'LocationPrep', 'LocationDelivery', 'Collection',
                            'Container']
        for attr_name, mapping in field_map.items():
            try:
                assert mapping['xlsx']
            except KeyError:
                continue
            try:
                column = mapping['xlsx']['column']
            except TypeError:
                column = mapping['xlsx']
            except Exception as exc:
                raise RuntimeError
            value = row[column]
            if attr_name in problem_attrs:
                value = instance._fix_problem_attrs(attr_name, value)
            if attr_name in link_field_attrs:
                value = instance._set_link_field(attr_name, value)
            try:
                setattr(instance, attr_name, value)
            except TypeError as exc:
                logger.error(attr_name)
                logger.error(value)
                logger.error(exc, stack_info=True)
                raise RuntimeError
        return instance

    def send(self):
        '''
        primary means of updating / inserting

        looks up value of primary field in Airtable
        if found, updates record
        if not found, creates a new record
        '''
        logger.info("sending local record to Airtable...")
        atbl_tbl = self.get_table()
        atbl_tbl_schema = atbl_mtd.get_table_schema(atbl_tbl)
        primary_field_id = atbl_tbl_schema['primaryFieldId']
        for field in atbl_tbl_schema['fields']:
            if field['id'] == primary_field_id:
                primary_field_name = field['name']
                break
        try:
            self.primary_field_value = self._fields[primary_field_name]
        except KeyError:
            logger.warning(f"no value for primary field {primary_field_name} in record")
            logger.warning(f"using AVMPIAirtableRecord() attribute instead = {self.primary_field}")
            self_primary_field_value = self.primary_field
        logger.debug(f"searching for existing record, with:\
                    \nprimary_key = {primary_field_name}\
                    \nfield_value{self_primary_field_value}")
        response = atbl_tbl.all(formula=match({primary_field_name: self_primary_field_value}))
        if len(response) > 1:
            logger.error(f"too many results for {self_primary_field_value} in field {primary_field_name}")
            raise ValueError("duplicate records in table")
        elif len(response) > 0:
            logger.debug("result found, updating Airtable record with local values...")
            atbl_rec_remote = self.from_id(response[0]['id'])
            fnam = atbl_rec_remote._field_name_attribute_map()
            for field, value in self._fields.items():
                try:
                    attr_name = fnam[field]
                    setattr(atbl_rec_remote, attr_name, value)
                except (KeyError, TypeError) as exc:
                    logger.exception(exc, stack_info=True)
                    continue
        else:
            logger.debug("no results found")
            atbl_rec_remote = self
        try:
            atbl_rec_remote.save()
            time.sleep(0.1)
            if atbl_rec_remote.exists():
                return atbl_rec_remote
            else:
                raise RuntimeError("there was a problem saving that record")
        except requests.exceptions.HTTPError as exc:
            logger.exception(exc, stack_info=True)
            err = exc.response.json()
            result = ''
            result = re.search(r'"[A-Za-z].*"', err['error']['message'])
            if result:
                field_name = result.group().replace('"', '')
                attr_name = fnam[field_name]
                attr_value = getattr(self, attr_name)
                logger.warning(f"field {field_name} has a problem with value {attr_value}")
                logger.warning("trying to remove field and re-save")
                setattr(atbl_rec_remote, attr_name, '')
            atbl_rec_remote.save()
            time.sleep(0.1)
            return atbl_rec_remote


class PhysicalAssetRecord(Model, AVMPIAirtableRecord):
    '''
    object class for Physical Assets at AVMPI
    '''
    field_map = get_field_map('PhysicalAssetRecord')
    '''
    add every key in the field map as an attribute to the class
    each attribute is an Airtable field with a type
    '''
    for field, mapping in field_map.items():
        '''
        I DON'T KNWO WHY THIS DOESN'T WORK
        ASSERTION ERROR
        try:
            assert mapping['atbl']
        except KeyError:
            continue
        '''
        try:
            field_type = mapping['atbl']['type']
            field_name = mapping['atbl']['name']
            if field_type == 'singleSelect':
                vars()[field] = fields.SelectField(field_name)
            elif field_type == 'multipleSelect':
                vars()[field] = fields.MultipleSelectField(field_name)
            elif field_type == 'number':
                vars()[field] = fields.NumberField(field_name)
            elif field_type == 'float':
                vars()[field] = fields.FloatField(field_name)
        except (KeyError, TypeError):
            vars()[field] = fields.TextField(mapping['atbl'])

    class Meta:
        base_id = "appU0Fh8L9xVZBeok"
        table_name = "Physical Assets"

        @staticmethod
        def api_key():
            return get_api_key()

    def from_xlsx(self, row):
        '''
        creates an Airtable record from a row in an Excel file
        using field mapping
        '''
        return super().from_xlsx(row, self.field_map)


class DigitalAssetRecord(Model, AVMPIAirtableRecord):
    '''
    object class for Digital Assets records
    '''
    field_map = get_field_map('DigitalAssetRecord')
    for field, mapping in field_map.items():
        '''
        try:
            assert mapping[field]['atbl']
        except KeyError:
            continue
        '''
        try:
            field_type = mapping['atbl']['type']
            field_name = mapping['atbl']['name']
            if field_type == 'singleSelect':
                vars()[field] = fields.SelectField(field_name)
            elif field_type == 'multipleSelect':
                vars()[field] = fields.MultipleSelectField(field_name)
            elif field_type == 'number':
                vars()[field] = fields.NumberField(field_name)
            elif field_type == 'duration':
                vars()[field] = fields.DurationField(field_name)
        except (KeyError, TypeError):
            vars()[field] = fields.TextField(mapping['atbl'])

    class Meta:
        base_id = 'appU0Fh8L9xVZBeok'
        table_name = 'Digital Assets'

        @staticmethod
        def api_key():
            return get_api_key()

    def from_xlsx(self, row):
        '''
        creates an Airtable record from a row in an Excel file
        using field mapping
        '''
        return super().from_xlsx(row, self.field_map)


class PhysicalAssetActionRecord(Model, AVMPIAirtableRecord):
    '''
    object class for Physical Assets at AVMPI
    '''
    field_map = get_field_map('PhysicalAssetActionRecord')
    for field, mapping in field_map.items():
        vars()[field] = fields.TextField(mapping['atbl'])

    class Meta:
        base_id = 'appU0Fh8L9xVZBeok'
        table_name = 'Physical Asset Action Log'

        @staticmethod
        def api_key():
            return get_api_key()

    def from_xlsx(self, row):
        '''
        creates an Airtable record from a row in an Excel file
        using field mapping
        '''
        return super().from_xlsx(row, self.field_map)


class PhysicalFormatRecord(Model, AVMPIAirtableRecord):
    '''
    bare-bones class for representing Physical Formats
    in their syncd table in Assets base
    '''
    class Meta:
        base_id = 'appU0Fh8L9xVZBeok'
        table_name = 'AV Formats'

        @staticmethod
        def api_key():
            return get_api_key()


class CollectionRecord(Model, AVMPIAirtableRecord):
    '''
    bare-bones class for representing Collections
    in their syncd table in Assets base
    '''
    class Meta:
        base_id = 'appU0Fh8L9xVZBeok'
        table_name = 'Collections'

        @staticmethod
        def api_key():
            return get_api_key()


class LocationRecord(Model, AVMPIAirtableRecord):
    '''
    bare-bones class for representing Locations
    in their syncd table in Assets base
    '''
    class Meta:
        base_id = 'appU0Fh8L9xVZBeok'
        table_name = 'Locations'

        @staticmethod
        def api_key():
            return get_api_key()


class ContainerRecord(Model, AVMPIAirtableRecord):
    '''
    bare-bones class for representing Containers
    '''
    class Meta:
        base_id = 'appU0Fh8L9xVZBeok'
        table_name = 'Containers'
        
        @staticmethod
        def api_key():
            return get_api_key() 


def set_link_fields():
    '''
    adds class attributes for above classes for link fields
    happens here + called globally because
    we need all of the Record() classes definied before linking them
    '''
    setattr(PhysicalAssetRecord, 'DigitalAsset', fields.LinkField('Digital Asset', DigitalAssetRecord))
    setattr(PhysicalAssetRecord, 'PhysicalFormat', fields.LinkField('Physical Format', PhysicalFormatRecord))
    setattr(PhysicalAssetRecord, 'LocationPrep', fields.LinkField('Current Location', LocationRecord))
    setattr(PhysicalAssetRecord, 'LocationDelivery', fields.LinkField('Delivery Location', LocationRecord))
    setattr(PhysicalAssetRecord, 'Collection', fields.LinkField('Collection', CollectionRecord))
    setattr(DigitalAssetRecord, 'PhysicalAsset', fields.LinkField('Original Physical Asset', PhysicalAssetRecord))
    setattr(DigitalAssetRecord, 'Container', fields.LinkField('Container', ContainerRecord))


set_link_fields()


def connect_one_base(base_name):
    '''
    returns a connection to every table in a base
    '''
    logger.debug(f"connecting to all tables in {base_name}")
    atbl_conf = config()
    atbl_base = {}
    atbl_base_id = atbl_conf['bases'][base_name]['base_id']
    api = Api(atbl_conf['main']['api_key'])
    for table_name in atbl_conf['bases'][base_name]['tables']:
        atbl_tbl = api.table(atbl_base_id, table_name)
        atbl_base.update({table_name: atbl_tbl})
    return atbl_base
