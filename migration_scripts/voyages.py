"""

This script imports voyages from Episerver to Contentful if they already are not added
to Contentful. This is checked by Contentful entry ID. For imported voyages it is the
same as entry id in Epi. To update voyages they first need to be deleted from Contentful
and then imported from Episerver by this script. When adding voyage, entries and assets
that has been previously linked to the old imported voyage and thus have the same id are
deleted and re-imported.

"""

import config
import helpers
import logging
from argparse import ArgumentParser


logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')

CMS_API_URL = "https://www.hurtigruten.com/rest/b2b/voyages"


def prepare_environment():
    logging.info('Setup Contentful environment')
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID,
        config.CTFL_ENV_ID,
        config.CTFL_MGMT_API_KEY)

    logging.info('Get all voyages')
    voyages = helpers.read_json_data(CMS_API_URL)
    logging.info('Number of voyages in EPI: %s' % len(voyages))
    logging.info('')
    logging.info('-----------------------------------------------------')
    logging.info('Voyage IDs to migrate: ')
    for voyage in voyages:
        logging.info(voyage['id'])
    logging.info('-----------------------------------------------------')
    logging.info('')

    return voyages, contentful_environment


def update_voyage(contentful_environment, voyage):
    logging.info('Voyage migration started with ID: %s' % voyage['id'])

    # load all fields for the particular voyage by calling GET voyages/{id}
    voyage_detail = helpers.read_json_data("%s/%s" % (CMS_API_URL, voyage['id']))

    helpers.add_entry(
        environment = contentful_environment,
        id = str(voyage_detail['id']),
        content_type_id = "voyage",
        fields = helpers.field_localizer('en-US', {
            'name': voyage_detail['heading'],
            'description': voyage_detail['intro'],
            'included': helpers.convert_to_contentful_rich_text(voyage_detail['includedInfo']),
            'notIncluded': helpers.convert_to_contentful_rich_text(voyage_detail['notIncludedInfo']),
            'travelSuggestionCodes': voyage_detail['travelSuggestionCodes'],
            'duration': voyage_detail['durationText'],
            'destinations': [helpers.entry_link(voyage_detail['destinationId'])],
            'fromPort': helpers.entry_link(voyage_detail['fromPort']),
            'toPort': helpers.entry_link(voyage_detail['toPort']),
            'notes': helpers.convert_to_contentful_rich_text(voyage_detail['notes']),
            'usps': [
                helpers.add_entry(
                    environment = contentful_environment,
                    id = "usp%d-%d" % (voyage_detail['id'], i),
                    content_type_id = "usp",
                    fields = helpers.field_localizer('en-US', {'text': usp})
                ) for i, usp in enumerate(voyage_detail['sellingPoints'])
            ],
            'map': helpers.add_asset(
                environment = contentful_environment,
                asset_uri = voyage_detail['largeMap']['highResolutionUri'],
                id = "voyageMap%d" % voyage_detail['id'],
                title = voyage_detail['largeMap']['alternateText'],
                file_name = voyage_detail['largeMap']['alternateText']
            ),
            'media': [
                helpers.add_asset(
                    environment = contentful_environment,
                    asset_uri = media_item['highResolutionUri'],
                    id = "voyagePicture%d-%d" % (voyage_detail['id'], i),
                    title = media_item['alternateText']
                ) for i, media_item in enumerate(voyage_detail['mediaContent'])
            ],
            'itinerary': [
                helpers.add_entry(
                    environment = contentful_environment,
                    id = "itday%d-%d" % (voyage_detail['id'], i),
                    content_type_id = "itineraryDay",
                    fields = helpers.field_localizer('en-US', {
                        'day': itinerary_day['day'],
                        'location': itinerary_day['location'],
                        'name': itinerary_day['heading'],
                        'description': helpers.convert_to_contentful_rich_text(itinerary_day['body']),
                        'images': [
                            helpers.add_asset(
                                environment = contentful_environment,
                                asset_uri = media_item['highResolutionUri'],
                                id = "itdpic%d-%s-%d" % (voyage_detail['id'], helpers.camelize(itinerary_day['day']), i),
                                title = media_item['alternateText']
                            ) for i, media_item in enumerate(itinerary_day['mediaContent'])
                        ]
                    })
                ) for i, itinerary_day in enumerate(voyage_detail['itinerary'])
            ]
        })
    )

    logging.info('Voyage migration finished with ID: %s' % voyage['id'])


def run_sync(**kwargs):
    voyage_ids = kwargs.get('content_ids')
    include = kwargs.get('include')
    if voyage_ids is not None:
        if include:
            logging.info('Running voyages sync on specified IDs: %s' % voyage_ids)
        else:
            logging.info('Running voyages sync, skipping IDs: %s' % voyage_ids)
    else:
        logging.info('Running voyages sync')
    voyages, contentful_environment = prepare_environment()
    for voyage in voyages:
        if voyage_ids is not None:
            # run only included voyages
            if include and voyage['id'] not in voyage_ids:
                continue
            # skip excluded voyages
            if not include and voyage['id'] in voyage_ids:
                continue
        update_voyage(contentful_environment, voyage)


parser = ArgumentParser(prog = 'voyages.py', description = 'Run voyage sync between Contentful and EPI')
parser.add_argument("-ids", "--content_ids", nargs='+', type=int, help = "Provide voyage IDs")
parser.add_argument("-include", "--include", nargs='+', type=bool, help = "Specify if you want to include or exclude "
                                                                         "voyage IDs")
args = parser.parse_args()


if __name__ == '__main__':
    ids = vars(args)['content_ids']
    include = vars(args)['include']
    run_sync({"content_ids": ids, "include": include})
