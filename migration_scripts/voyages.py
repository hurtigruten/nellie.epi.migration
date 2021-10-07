"""

This script imports voyages from Episerver to Contentful if they already are not added
to Contentful. This is checked by Contentful entry ID. For imported voyages it is the
same as entry id in Epi. To update voyages they first need to be deleted from Contentful
and then imported from Episerver by this script. When adding voyage, entries and assets
that has been previously linked to the old imported voyage and thus have the same id are
deleted and re-imported.

"""
import csv
import config
import helpers
import logging
import json
from argparse import ArgumentParser

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

CMS_API_URLS = {
    "en": "https://global.hurtigruten.com/rest/b2b/voyages",
    "EN-AMERICAS": "https://www.hurtigruten.com/rest/b2b/voyages",
    "EN-APAC": "https://www.hurtigruten.com.au/rest/b2b/voyages",
    "de": "https://www.hurtigruten.de/rest/b2b/voyages",
    "en-GB": "https://www.hurtigruten.co.uk/rest/b2b/voyages",
    "de-CH": "https://www.hurtigruten.ch/rest/b2b/voyages",
    "sv-SE": "https://www.hurtigrutenresan.se/rest/b2b/voyages",
    "nb-NO": "https://www.hurtigruten.no/rest/b2b/voyages",
    "da-DK": "https://www.hurtigruten.dk/rest/b2b/voyages",
    "fr-FR": "https://www.hurtigruten.fr/rest/b2b/voyages"
}


def get_api_urls(market):
    if market:
        return {market: CMS_API_URLS[market]}
    else:
        return CMS_API_URLS


def prepare_environment(market):
    logging.info('Setup Contentful environment')
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID,
        config.CTFL_ENV_ID,
        config.CTFL_MGMT_API_KEY)

    api_urls = get_api_urls(market)

    logging.info('Using Contentful environment: %s' % config.CTFL_ENV_ID)
    logging.info('Get all voyages for locales: %s' % (", ".join([key for key, value in api_urls.items()])))

    voyage_ids = []
    epi_voyage_ids = []
    for key, value in api_urls.items():
        voyage_ids += [voyage['id'] for voyage in helpers.read_json_data(value) if
                       helpers.skip_entry_if_not_updated(voyage, key, voyage['id'])]
        epi_voyage_ids += [voyage['id'] for voyage in helpers.read_json_data(value)]

    # Create distinct list
    voyage_ids = set(voyage_ids)
    epi_voyage_ids = set(epi_voyage_ids)

    logging.info('Number of voyages in EPI: %s' % len(epi_voyage_ids))
    logging.info('')
    logging.info('Number of voyages changed: %s' % len(voyage_ids))
    logging.info('-----------------------------------------------------')
    logging.info('Voyage IDs to migrate: ')
    for voyage_id in voyage_ids:
        logging.info(voyage_id)
    logging.info('-----------------------------------------------------')
    logging.info('')

    return voyage_ids, contentful_environment


def update_voyage(contentful_environment, voyage_id, market):
    logging.info('Voyage migration started with ID: %s' % voyage_id)

    voyage_detail_by_locale = {}

    update_api_urls = get_api_urls(market)

    for locale, url in update_api_urls.items():
        # load all fields for the particular voyage by calling GET voyages/{id}
        voyage_detail_by_locale[locale] = helpers.read_json_data("%s/%s" % (url, voyage_id))

    if market:
        default_voyage_detail = voyage_detail_by_locale[market]
    else:
        default_voyage_detail = voyage_detail_by_locale[config.DEFAULT_LOCALE]

    if default_voyage_detail is None:
        logging.info('Could not find default voyage detail for voyage ID: %s' % voyage_id)
        return

    # Assuming that number of selling points is the same for every locale
    # Check if there's available usps for a given locale, and filter out locales which don't have any usps
    voyage_detail_by_locale_usps = {}
    usps_list = []
    for locale, locale_voyage_detail in voyage_detail_by_locale.items():
        if locale_voyage_detail['sellingPoints'] is None or locale_voyage_detail['sellingPoints'] == []:
            logging.warning('USPs is not available in %s for %s' % (locale, voyage_id))
        else:
            voyage_detail_by_locale_usps[locale] = locale_voyage_detail
            usps_list = locale_voyage_detail['sellingPoints']

    usps = [
        helpers.add_entry(
            environment=contentful_environment,
            id="usp%s-%d" % (voyage_id, i),
            content_type_id="usp",
            market=market or None,
            fields=helpers.merge_localized_dictionaries(*(
                helpers.field_localizer(
                    locale, {
                        'text': locale_voyage_detail['sellingPoints'][i]
                    },
                    market
                )
                for locale, locale_voyage_detail in voyage_detail_by_locale_usps.items()
            ))
        ) for i, usp in enumerate(usps_list)
    ]

    # Assuming that media is same for every locale
    media = [
        helpers.add_or_reuse_asset(
            environment=contentful_environment,
            asset_uri=media_item['highResolutionUri'],
            id=media_item['id'],
            title=media_item['alternateText']
        ) for i, media_item in enumerate(default_voyage_detail['mediaContent'])
    ]

    map = helpers.add_or_reuse_asset(
        environment=contentful_environment,
        asset_uri=default_voyage_detail['largeMap']['highResolutionUri'],
        id=default_voyage_detail['largeMap']['id'].replace(':', '-'),
        title=default_voyage_detail['largeMap']['alternateText'],
        file_name=default_voyage_detail['largeMap']['alternateText']
    ) if default_voyage_detail['largeMap'] is not None else None

    # Assuming that itinerary days are the same for every locale

    # Check if there's available itinerary for a given locale, and filter out locales which don't have any itineraries
    voyage_detail_by_locale_itineraries = {}
    itinerary_list = []
    length_of_list = len(default_voyage_detail['itinerary'])
    for locale, locale_voyage_detail in voyage_detail_by_locale.items():
        if 'itinerary' not in locale_voyage_detail or len(locale_voyage_detail['itinerary']) == 0:
            logging.warning('Itinerary is not available in %s for %s' % (locale, voyage_id))
        if len(locale_voyage_detail['itinerary']) > length_of_list:
            logging.error('Itinerary has to many itineraries. Rerun migration for %s' % locale)
        else:
            voyage_detail_by_locale_itineraries[locale] = locale_voyage_detail
            itinerary_list = locale_voyage_detail['itinerary']

    itinerary = [
        helpers.add_entry(
            environment=contentful_environment,
            id="itday%s-%d" % (voyage_id, i),
            content_type_id="itineraryDay",
            market=market or None,
            fields=helpers.merge_localized_dictionaries(*(
                helpers.field_localizer(locale, {
                    'day': locale_voyage_detail['itinerary'][i]['day'],
                    'location': locale_voyage_detail['itinerary'][i]['location'],
                    'name': locale_voyage_detail['itinerary'][i]['heading'],
                    'description': helpers.convert_to_contentful_rich_text(
                        locale_voyage_detail['itinerary'][i]['body']
                    ),
                    'images': [
                        helpers.add_or_reuse_asset(
                            environment=contentful_environment,
                            asset_uri=media_item['highResolutionUri'],
                            id=media_item['id'],
                            title=media_item['alternateText']
                        ) for k, media_item in enumerate(locale_voyage_detail['itinerary'][i]['mediaContent'])
                    ],
                    'excursions': [
                        helpers.entry_link(
                            excursion_id
                        ) for excursion_id in locale_voyage_detail['itinerary'][i]['includedExcursions']
                    ],
                    'departureTime': locale_voyage_detail['itinerary'][i]['departureTime'],
                    'arrivalTime': locale_voyage_detail['itinerary'][i]['arrivalTime']
                }, market) for locale, locale_voyage_detail in voyage_detail_by_locale_itineraries.items()
            ))
        ) for i, itinerary_day in enumerate(itinerary_list)
    ]

    helpers.add_entry(
        environment=contentful_environment,
        id=str(voyage_id),
        content_type_id="voyage",
        market=market or None,
        fields=helpers.merge_localized_dictionaries(*(
            helpers.field_localizer(locale, {
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
                'shortDescription': helpers.convert_to_contentful_rich_text(voyage_detail['itineraryOneLiner']),
                'longDescription': helpers.convert_to_contentful_rich_text(voyage_detail['itineraryIntro']),
                'isViaKirkenes': voyage_detail['isViaKirkenes'],
                'isClassicVoyage': voyage_detail['destinationId'] == 20927 and (
                            voyage_detail['fromPort'] == "BGO" or voyage_detail["toPort"] == "BGO") and (
                                               voyage_detail['fromPort'] == "KKN" or voyage_detail["toPort"] == "KKN"),
                'usps': usps,
                'map': map,
                'media': media,
                'itinerary': itinerary
            }, market) for locale, voyage_detail in voyage_detail_by_locale.items()
        ))
    )

    for locale, url in update_api_urls.items():
        helpers.update_entry_database(voyage_id, locale)

    logging.info('Voyage migration finished with ID: %s' % voyage_id)


def run_sync(**kwargs):
    parameter_voyage_ids = kwargs.get('content_ids')
    include = kwargs.get('include')
    market = kwargs.get('market')
    if parameter_voyage_ids is not None:
        if include:
            logging.info('Running voyages sync on specified IDs: %s' % parameter_voyage_ids)
            [helpers.prepare_included_environment(parameter_voyage_ids, locale) for locale, url in CMS_API_URLS.items()]
        else:
            logging.info('Running voyages sync, skipping IDs: %s' % parameter_voyage_ids)
    else:
        logging.info('Running voyages sync')
    voyage_ids, contentful_environment = prepare_environment(market)
    for voyage_id in voyage_ids:
        if parameter_voyage_ids is not None:
            # run only included voyages
            if include and voyage_id not in parameter_voyage_ids:
                continue
            # skip excluded voyages
            if not include and voyage_id in parameter_voyage_ids:
                continue
        try:
            update_voyage(contentful_environment, voyage_id, market)
        except Exception as e:
            logging.error('Voyage migration error with ID: %s, error: %s' % (voyage_id, e))
            [helpers.remove_entry_id_from_memory(voyage_id, locale) for locale, url in CMS_API_URLS.items()]


parser = ArgumentParser(prog='voyages.py', description='Run voyage sync between Contentful and EPI')
parser.add_argument("-ids", "--content_ids", nargs='+', type=int, help="Provide voyage IDs")
parser.add_argument("-include", "--include", nargs='?', type=helpers.str2bool, const=True, default=True,
                    help="Specify if you want to include or exclude voyage IDs")
args = parser.parse_args()

if __name__ == '__main__':
    ids = vars(args)['content_ids']
    include = vars(args)['include']
    run_sync(**{"content_ids": ids, "include": include})
