"""
This script published all unpublished assets with asset ID
starting with one of the keywords defined in the keywords array
"""

import helpers
import config
import logging
import contentful_management

logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')

contentful_environment = helpers.create_contentful_environment(config.CTFL_SPACE_ID, config.CTFL_ENV_ID, config.CTFL_MGMT_API_KEY)

step = 1000
# excursion
# keywords = ["excp"]
# voyage
keywords = ["voyagePicture", "itdpic", "voyageMap"]
# ships
# keywords = ["shippic-", "shCabCatPic-", "shCabGr-", "deckPic-"]

# all
# keywords = ["programPicture", "excp", "deckPic-", "shCabGr-", "shCabCatPic-", "voyagePicture", "itdpic", "voyageMap", "shippic-"]

for keyword in keywords:
    items_in_last_iteration = 1
    i = 0
    while items_in_last_iteration > 0:
        assets = contentful_environment.assets().all(query={"sys.id[match]": keyword, "skip": step * i, "limit": step})
        items_in_last_iteration = len(assets)
        i = i + 1
        for asset in assets:
            if asset.is_published:
                continue
            logging.info('Publishing %s' % asset.sys['id'])
            try:
                asset.publish()
            except contentful_management.errors.UnprocessableEntityError:
                logging.info("Asset cannot be processed, deleting asset")
                asset.delete()
            except Exception as e:
                logging.error("Asset cannot be processed, error: %s" % e)


