'''
This script published all unpublished assets with asset ID
starting with one of the keywords defined in the keywords array
'''

import helpers as hs
import config as cf
import contentful_management

ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)

step = 1000
keywords = ["programPicture", "excp", "deckPic-", "shCabGr-", "shCabCatPic-", "voyagePicture", "itdpic", "voyageMap"]

for keyword in keywords:
    items_in_last_iteration = 1
    i = 0
    while items_in_last_iteration > 0:
        assets = ctfl_env.assets().all(query={"sys.id[match]": keyword, "skip": step * i, "limit": step})
        items_in_last_iteration = len(assets)
        i = i + 1
        for asset in assets:
            if asset.is_published:
                continue
            print("Publishing %s" % asset.sys['id'])
            try:
                asset.publish()
            except contentful_management.errors.UnprocessableEntityError:
                print("Asset cannot be processed, deleting asset")
                asset.delete()


