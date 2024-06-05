'''
for figuring out how the heck to
ID which fields in a table are linked,
which of those links are syncd
'''
from pprint import pprint, pformat
from pyairtable import Api, Base, Table
import airtable

api_key = airtable.get_api_key()
api = Api(api_key)
base_id_Assets = "appU0Fh8L9xVZBeok"
base_Assets = api.base(base_id_Assets)
tables = base_Assets.tables()
for atbl_tbl in tables:
    for field in atbl_tbl.schema().fields:
        input(pformat(field))

