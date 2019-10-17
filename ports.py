import contentful_management
import helpers as hs
import config as cf
from urllib.parse import urlparse
from os.path import splitext, basename
import pycountry

CMS_API_URL = "https://www.hurtigruten.com/rest/b2b/ports"

data = hs.readJsonData(CMS_API_URL)
ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)

for port in data:
    hs.addEntry(
        environment=ctfl_env,
        id=port['code'],
        content_type_id = "port",
        fields = hs.fieldLocalizer('en-US',
            {
                'code': port['code'],
                'name': port['name'],
                'country': pycountry.countries.get(alpha_2=port['countryCode']).name
            }
        )
    )