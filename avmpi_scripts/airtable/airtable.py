'''
handler for Airtable calls for AVMPI
'''
import time
import json
import pathlib
import logging
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


class AVMPIAirtableRecord:
    '''
    super class for the various AirtableRecord() classes we'll create later
    defines a few methods we'll use for all Airtable records
    notably, send() and from_xlsx()
    '''
    primary_field = None

    @classmethod
    def from_xlsx(cls, row, field_map):
        '''
        creates an Airtable record from an XLSX spreadsheet
        '''
        logger.debug(pformat(row))
        logger.debug(pformat(field_map))
        instance = cls()
        for key, key_list in atbl_map.items():
            try:
                '''
                something like
                value = row[key_list['xlsx']]
                '''
            except:
                # stuff here
            setattr(instance, key, value)
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
        logger.debug(f"searching for existing record with,
                    \nprimary_key = {primary_field_name}
                    \nfield_value{self_primary_field_value}")
        response = atbl_tbl.all(formula=match({primary_field_name: self_primary_field_value}))
        if len(response) > 1:
            logger.error(f"too many results for {self_primary_field_value} in field {primary_field_name}")
            raise ValueError("duplicate records in table")
        elif len(response) > 0:
            logger.debug("result found, updating Airtable record with local values...")
            atbl_rec_remote = self.from_id(response[0]['id'])
            fnam = atbl_rec_remote._field_namme_attribute_map()
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
