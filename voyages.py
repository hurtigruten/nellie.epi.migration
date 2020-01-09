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
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')

CMS_API_URL = "https://www.hurtigruten.com/rest/b2b/voyages"

logging.info('Setup Contentful environment')
contentful_environment = helpers.create_contentful_environment(
    config.CTFL_SPACE_ID,
    config.CTFL_ENV_ID,
    config.CTFL_MGMT_API_KEY)

logging.info('Get all voyages')
voyages = helpers.read_json_data(CMS_API_URL)
logging.info('Number of voyages in EPI: %s' % len(voyages))


# pVoyages = [50526,49665,50189,50417,50548,50705,50727,50739,51069,51081,40019,49628]

def update_voyage(voyage):
    logging.info('Voyage migration started with ID: %s' % voyage['id'])

    # if voyage['id'] not in pVoyages:
    #     return
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

    return voyage['id']


def main():
    with ThreadPoolExecutor(max_workers = 1) as executor:
        running_tasks = {executor.submit(update_voyage, voyage): voyage for voyage in voyages}
        for task in as_completed(running_tasks):
            logging.info('Voyage migration finished with ID: %s' % task.result())


main()
