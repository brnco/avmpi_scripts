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
            try:
                value = str(int(value))
            except:
                pass
        if attr_name == 'asset_size':
            value = float(value)
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
            primary_key_name = 'Physical Asset ID'
            the_class = PhysicalAssetRecord()
        elif attr_name == 'PhysicalFormat':
            table_name = 'AV Formats'
            primary_key_name = 'Term'
            the_class = PhysicalFormatRecordSyncd()
        elif attr_name == 'Collection':
            table_name = 'Collections'
            primary_key_name = 'Collection Title'
            the_class = CollectionRecordSyncd()
        elif 'Location' in attr_name:
            table_name = 'Locations'
            primary_key_name = 'Name'
            the_class = LocationRecordSyncd()
        elif 'Container' in attr_name:
            table_name = 'Containers'
            primary_key_name = 'Container Name'
            the_class = ContainerRecord()
        if isinstance(self, PhysicalAssetRecord) and table_name == 'Digital Assets':
            atbl_recs = []
            if ',' in value:
                digital_assets = value.split(',')
            elif ';' in value:
                digital_assets = value.split(';')
            else:
                digital_assets = [value.strip()]
            digital_assets = [da.strip() for da in digital_assets]
            for digital_asset in digital_assets:
                atbl_tbl = atbl_api.table(base_id, table_name)
                logger.debug(f"searching for {digital_asset} in field {primary_key_name} in table {table_name}")
                result = atbl_tbl.all(formula=match({primary_key_name: digital_asset}))
                if not result:
                    logger.warning(f"while parsing linked field, no record was in linked table for:")
                    logger.warning(f"\ndigital_asset: {digital_asset}\nprimary_key_name: {primary_key_name}\ntable: {table_name}")
                    logger.warning("creating bare record to link to")
                    result = atbl_tbl.create({primary_key_name: digital_asset})
                    result = [result]
                    logger.debug(f"result: {result[0]}")
                atbl_rec = the_class.from_id(result[0]['id'])
                logger.debug(pformat(atbl_rec))
                atbl_recs.append(atbl_rec)
            return atbl_recs
        atbl_tbl = atbl_api.table(base_id, table_name)
        result = atbl_tbl.all(formula=match({primary_key_name: value}))
        if not result:
            logger.warning(f"table: {table_name}\nprimary key: {primary_key_name}\nvalue: {value} did not return any results initially")
            logger.warning("creating bare record to link to...")
            try:
                result = atbl_tbl.create({primary_key_name: value})
                result = [result]
            except requests.exceptions.HTTPError as exc:
                logger.error("the script encountered an error while trying to create a bare linked record")
                logger.error("this was likely because the value does not exist in a linked, sync'd table")
                logger.error(f"linked table: {table_name}")
                logger.error(f"value: {value}")
                # logger.exception(exc, stack_info=True)
                raise RuntimeError("please ensure the value above exists in the table and try again")
        try:
            atbl_rec = the_class.from_id(result[0]['id'])
            atbl_rec.save()
        except:
            print(the_class)
        return [atbl_rec]

    @classmethod
    def from_xlsx(cls, row, field_map):
        '''
        creates an Airtable record from a row of an XLSX spreadsheet
        '''
        instance = cls()
        problem_attrs = ['asset_barcode', 'color', 'sound', 'asset_duration', 'asset_size',
                         'secondary_asset_id', 'physical_asset_barcode']
        link_field_attrs = ['DigitalAsset', 'PhysicalAsset', 'PhysicalFormat',
                            'LocationPrep', 'LocationDelivery', 'Collection',
                            'Container']
        for attr_name, mapping in field_map.items():
            try:
                assert mapping['xlsx']
            except KeyError:
                continue
            if not mapping['atbl']:
                continue
            try:
                column = mapping['xlsx']['column']
            except TypeError:
                column = mapping['xlsx']
            except Exception as exc:
                raise RuntimeError
            value = row[column]
            if not value:
                continue
            if attr_name in problem_attrs:
                value = instance._fix_problem_attrs(attr_name, value)
            if attr_name in link_field_attrs:
                value = instance._set_link_field(attr_name, value)
            try:
                setattr(instance, attr_name, value)
            except TypeError as exc:
                logger.error(f"attr_name: {attr_name}")
                logger.error(f"value: {value}")
                logger.error(exc, stack_info=True)
                raise RuntimeError
        return instance

    def _get_primary_key_info(self):
        '''
        for send()
        gets primary key name and value
        '''
        atbl_tbl = self.get_table()
        atbl_tbl_schema = atbl_mtd.get_table_schema(atbl_tbl)
        primary_field_id = atbl_tbl_schema['primaryFieldId']
        for field in atbl_tbl_schema['fields']:
            if field['id'] == primary_field_id:
                primary_field_name = field['name']
                break
        try:
            self_primary_field_value = self._fields[primary_field_name]
        except KeyError:
            logger.warning(f"no value for primary field {primary_field_name} in record")
            logger.warning(f"using AVMPIAirtableRecord() attribute instead = {self.primary_field}")
            self_primary_field_value = self.primary_field
        return primary_field_name, self_primary_field_value

    def _search_on_primary_field(self, primary_field_name, self_primary_field_value):
        '''
        searches for self_primary_field_value in primary_field_name
        '''
        atbl_tbl = self.get_table()
        logger.debug(f"searching table {atbl_tbl.name}")
        logger.debug(f"in field {primary_field_name}")
        logger.debug(f"for value {self_primary_field_value}")
        response = atbl_tbl.all(formula=match({primary_field_name: self_primary_field_value}))
        if len(response) > 1:
            logger.error(f"too many results for {self_primary_field_value} in field {primary_field_name}")
            raise ValueError("duplicate records in table")
        elif len(response) > 0:
            logger.debug("result found, updating Airtable record with local values...")
            atbl_rec_remote = self.from_id(response[0]['id'])
        else:
            logger.debug("no results found")
            return None
        return atbl_rec_remote

    def _fill_remote_rec_from_local(self, atbl_rec_remote):
        '''
        ugh we can't just assign a record id to an unsaved record
        and have that overwrite a remote record
        so instead we do this,
        where we take the remote record and fill it with local values
        '''
        for field, value in self._fields.items():
            try:
                atbl_rec_remote._fields[field] = value
            except (KeyError, TypeError) as exc:
                logger.exception(exc, stack_info=True)
                continue
        return atbl_rec_remote

    def _save_rec(self, atbl_rec):
        '''
        actually save the damn record
        '''
        try:
            atbl_rec.save()
            time.sleep(0.1)
            if atbl_rec.exists():
                return atbl_rec
            else:
                raise RuntimeError("there was a problem saving that record")
        except requests.exceptions.HTTPError as exc:
            logger.exception(exc, stack_info=True)
            raise RuntimeError("there was a problem saving that record")

    def send(self):
        '''
        primary means of updating / inserting

        looks up value of primary field in Airtable
        if found, updates record
        if not found, creates a new record
        '''
        logger.info("sending local record to Airtable...")
        primary_field_name, self_primary_field_value = self._get_primary_key_info()
        logger.debug(f"searching for existing record, with:\
                    \nprimary_key = {primary_field_name}\
                    \nfield_value{self_primary_field_value}")
        # atbl_rec_remote here is not Model object
        atbl_rec_remote = self._search_on_primary_field(
                            primary_field_name, self_primary_field_value)
        if atbl_rec_remote:
            atbl_rec_remote = self._fill_remote_rec_from_local(atbl_rec_remote)
        else:
            atbl_rec_remote = self
        atbl_rec_remote = self._save_rec(atbl_rec_remote)
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
        try:
            field_type = mapping['atbl']['type']
            field_name = mapping['atbl']['name']
            if field_type == 'singleSelect':
                vars()[field] = fields.SelectField(field_name, typecast=False)
            elif field_type == 'multipleSelect':
                vars()[field] = fields.MultipleSelectField(field_name, typecast=False)
            elif field_type == 'number':
                vars()[field] = fields.NumberField(field_name)
            elif field_type == 'float':
                vars()[field] = fields.FloatField(field_name)
            elif field_type == 'integer':
                vars()[field] = fields.IntegerField(field_name)
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
        try:
            field_type = mapping['atbl']['type']
            field_name = mapping['atbl']['name']
            if field_type == 'singleSelect':
                vars()[field] = fields.SelectField(field_name, typecast=False)
            elif field_type == 'multipleSelect':
                vars()[field] = fields.MultipleSelectField(field_name, typecast=False)
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
        try:
            field_type = mapping['atbl']['type']
            field_name = mapping['atbl']['name']
            if field_type == 'singleSelect':
                vars()[field] = fields.SelectField(field_name, typecast=False)
            elif field_type == 'multipleSelect':
                vars()[field] = fields.MultipleSelectField(field_name, typecast=False)
            elif field_type == 'number':
                vars()[field] = fields.NumberField(field_name)
            elif field_type == 'float':
                vars()[field] = fields.FloatField(field_name)
        except (KeyError, TypeError):
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

    def send(self):
        '''
        because the primary key field for thsi table is a formula
        we can't search on it
        so, we make our own custom search here
        '''
        atbl_tbl = self.get_table()
        filter_formula = "AND({Asset} = '" + self.PhysicalAsset[0].physical_asset_id + "', "\
                "{Activity Type} = '" + self.activity_type + "')"
        response = atbl_tbl.all(formula=filter_formula)
        if len(response) > 1:
            logger.error(f"too many results for {self_primary_field_value} in field {primary_field_name}")
            raise ValueError("duplicate records in table")
        elif len(response) > 0:
            logger.debug("result found, updating Airtable record with local values...")
            atbl_rec_remote = self.from_id(response[0]['id'])
            for field, value in self._fields.items():
                try:
                    atbl_rec_remote._fields[field] = value
                except (KeyError, TypeError) as exc:
                    logger.exception(exc, stack_info=True)
                    continue
        else:
            logger.debug("no results found")
            atbl_rec_remote = self
        logger.debug(atbl_rec_remote.__dict__)
        try:
            atbl_rec_remote.save()
            time.sleep(0.1)
            if atbl_rec_remote.exists():
                return atbl_rec_remote
            else:
                raise RuntimeError("there was a problem saving that record")
        except Exception as exc:
            logger.exception(exc, stack_info=True)
            raise RuntimeError("there was a problem saving that record")


class PhysicalFormatRecord(Model, AVMPIAirtableRecord):
    '''
    bare-bones class for representing Physical Formats
    in their origin table in Metadata base
    '''
    class Meta:
        base_id = 'appWtd175HSokQgQP'
        table_name = 'AV Formats'

        @staticmethod
        def api_key():
            return get_api_key()


class PhysicalFormatRecordSyncd(Model, AVMPIAirtableRecord):
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
    in their origin table in Metadata base
    '''
    class Meta:
        base_id = 'appWtd175HSokQgQP'
        table_name = 'Collections'

        @staticmethod
        def api_key():
            return get_api_key()


class CollectionRecordSyncd(Model, AVMPIAirtableRecord):
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
    in their origin table in Metadata base
    '''
    class Meta:
        base_id = 'appWtd175HSokQgQP'
        table_name = 'Locations'

        @staticmethod
        def api_key():
            return get_api_key()



class LocationRecordSyncd(Model, AVMPIAirtableRecord):
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
    setattr(PhysicalAssetRecord, 'DigitalAsset', fields.LinkField('Digital Assets', DigitalAssetRecord))
    setattr(PhysicalAssetRecord, 'PhysicalFormat', fields.LinkField('Physical Format', PhysicalFormatRecordSyncd))
    setattr(PhysicalAssetRecord, 'LocationPrep', fields.LinkField('Current Location', LocationRecordSyncd))
    setattr(PhysicalAssetRecord, 'LocationDelivery', fields.LinkField('Delivery Location', LocationRecordSyncd))
    setattr(PhysicalAssetRecord, 'Collection', fields.LinkField('Collection', CollectionRecordSyncd))
    setattr(DigitalAssetRecord, 'PhysicalAsset', fields.LinkField('Original Physical Asset', PhysicalAssetRecord))
    setattr(DigitalAssetRecord, 'Container', fields.LinkField('Container', ContainerRecord))
    setattr(PhysicalAssetActionRecord, 'PhysicalAsset', fields.LinkField('Asset', PhysicalAssetRecord))


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


def parse_asset_actions(atbl_rec):
    '''
    uh each action in the log gets its own record
    so the initial Asset Action Record might need to be several records
    contains 0-n actions in that raw conversion, etc. and so on
    '''
    logger.debug("parsing asset action record for each action...")
    atbl_recs = []
    actions = getattr(atbl_rec, 'activity_type')
    physical_asset = getattr(atbl_rec, 'PhysicalAsset')
    atbl_rec_par = PhysicalAssetRecord()
    atbl_rec_par.physical_asset_id = physical_asset[0].physical_asset_id
    atbl_rec_par = atbl_rec_par.send()
    if not actions:
        actions = ['A-D Transfer']
    elif ';' in actions:
        actions = actions.split(';')
    elif ',' in actions:
        actions = actions.split(',')
    else:
        actions = [actions]
    for action in actions:
        atbl_rec_paar = PhysicalAssetActionRecord(
                activity_type=action.strip(),
                PhysicalAsset=[atbl_rec_par])
        atbl_recs.append(atbl_rec_paar)
    return atbl_recs

