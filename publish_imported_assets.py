"""
This script published all unpublished assets with asset ID
starting with one of the keywords defined in the keywords array
"""

import helpers
import config
import logging
import contentful_management
from argparse import ArgumentParser

logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')

asset_types = {
    "excursions": ["excp"],
    "voyages": ["voyagePicture", "itdpic", "voyageMap"],
    "ships": ["shippic-", "shCabCatPic-", "shCabGr-", "deckPic-"],
    # "programs": ["programPicture"]
}


def prepare_environment():
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID,
        config.CTFL_ENV_ID,
        config.CTFL_MGMT_API_KEY)
    return contentful_environment


def publish_asset(contentful_environment, asset_keyword, limit):
    items_in_last_iteration = 1
    i = 0
    while items_in_last_iteration > 0:

        assets = contentful_environment.assets().all(query={
            "sys.id[match]": asset_keyword,
            "skip": limit * i,
            "limit": limit})

        items_in_last_iteration = len(assets)
        i += 1

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


def run_publish(only_with_asset_types=None):
    if only_with_asset_types is not None:
        logging.info('Running asset publish on specified types: %s' % only_with_asset_types)
    else:
        logging.info('Running asset publish')
    contentful_environment = prepare_environment()
    for asset_type in asset_types:
        if only_with_asset_types is not None and asset_type not in only_with_asset_types:
            continue
        for keyword in asset_types[asset_type]:
            publish_asset(contentful_environment, keyword, 1000)


parser = ArgumentParser(prog = 'publish_imported_assets.py', description = 'Run publish for import assets in Contentful')
parser.add_argument("-types", "--asset_types", nargs='+', type=str, help = "Provide the asset types you want to publish")
args = parser.parse_args()


if __name__ == '__main__':
    types = vars(args)['asset_types']
    run_publish(only_with_asset_types = types)
