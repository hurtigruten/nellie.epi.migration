import contentful_management
import helpers as hs
import config as cf
from urllib.parse import urlparse
from os.path import splitext, basename

ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)

while True:
    hs.deleteContentOfType(ctfl_env, "itineraryDay")

while True:
    assets = ctfl_env.entries().all(query={"sys.id[match]": "usp"})
    for asset in assets:
        asset.unpublish()
        asset.delete()
        print("Entry %s deleted" % asset.sys['id'])


