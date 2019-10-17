import contentful_management
import helpers as hs
import config as cf
from urllib.parse import urlparse
from os.path import splitext, basename

CMS_API_URL = "http://api.development.hurtigruten.com:80/api/CmsShips"

data = hs.readJsonData(CMS_API_URL)
ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)

for ship_from_list in data:

    ship = hs.readJsonData("%s/%s" % ("https://www.hurtigruten.com/rest/b2b/ships", ship_from_list['mapUrl'][-2:]))

    hs.addEntry(
        environment=ctfl_env,
        id=ship['shipId'],
        content_type_id="ship",
        fields=hs.fieldLocalizer('en-US',
        {
            'code': "[TODO rewrite] " + ship['shipId'],
            'name': ship['heading'],
            'description': hs.convertToContentfulRichText("TODO"),
            'shipInfo': [
                hs.addEntry(
                    environment=ctfl_env,
                    id=ship['shipId'] + "constry",
                    
                )
            ],
            'images': None,
            'additionalInfo': None
        })
    )
    break