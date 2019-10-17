import contentful_management
import helpers as hs
import config as cf
from urllib.parse import urlparse
from os.path import splitext, basename

CMS_API_URL = "https://www.hurtigruten.com/rest/b2b/destinations"
VOYAGE_FIELD_TYPE_ID = "destination"

data = hs.readJsonData(CMS_API_URL)
ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)

for destination in data:
    attributes = {
        'content_type_id': VOYAGE_FIELD_TYPE_ID,
        'fields': {
            'name': {
                'en-US': "[TODO rewrite] %s" % destination['heading']
            }
        }
    }

    id = str(destination['id'])
    ctfl_env.entries().create(
        id,
        attributes
    )
    ctfl_env.entries().find(id).publish()

    print("Destination %s added" % id)