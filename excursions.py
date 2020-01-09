"""

This script imports excursions from Episerver to Contentful if they already are not added
to Contentful. This is checked by Contentful entry ID. For imported excursions it is the
same as entry id in Epi. To update excursions they first need to be deleted from Contentful
and then imported from Episerver by this script.

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

CMS_API_URL = 'https://www.hurtigruten.com/rest/excursion/excursions'
difficulty_dict = {
    '1': 'Level 1 - For everyone',
    '2': 'Level 2 - Easy',
    '3': 'Level 3 - Medium',
    '4': 'Level 4 - Hard'
}

logging.info('Setup Contentful environment')
contentful_environment = helpers.create_contentful_environment(
    config.CTFL_SPACE_ID,
    config.CTFL_ENV_ID,
    config.CTFL_MGMT_API_KEY)

logging.info('Get all excursions')
excursions = helpers.read_json_data(CMS_API_URL)
logging.info('Number of excursions in EPI: %s' % len(excursions))

# exc = [61503,58199,57773,57772,58309,61507,58310,61510,45317,61514,59718,61517,61522,58314,58315,61525,45334,61528,58316,45336,61537,45338,61546,58317,61500]

def update_excursion(excursion):
    logging.info('Excursion migration started with ID: %s' % excursion['id'])

    # if excursion['id'] not in exc:
    #     return

    helpers.add_entry(
        environment = contentful_environment,
        id = str(excursion['id']),
        content_type_id = "excursion",
        fields = helpers.field_localizer('en-US', {
            'name': excursion['title'],
            'description': helpers.convert_to_contentful_rich_text(excursion['summary']),
            'categories': [category['text'] for category in excursion['activityCategory']
                           if category['id'] is not "0"],
            'years': [year['id'] for year in excursion['years']],
            'seasons': [season['text'] for season in excursion['seasons']],
            'location': excursion['details'],
            'directions': [direction['text'].split(' ', 1)[0] for direction in
                           excursion['directions']],
            'duration': excursion['durationText'],
            'difficulty': difficulty_dict[excursion['physicalLevel'][0]['id']],
            'bookingCode': excursion['code'],
            'media': [
                helpers.add_asset(
                    environment = contentful_environment,
                    asset_uri = excursion['image']['imageUrl'],
                    id = "excp%s" % excursion['id'],
                    title = helpers.clean_asset_name(excursion['image']['altText'] or excursion['title'], excursion['id']))
            ] if excursion['image'] is not None else []
        })
    )
    return excursion['id']


def main():
    with ThreadPoolExecutor(max_workers = 1) as executor:
        running_tasks = {executor.submit(update_excursion, excursion): excursion for excursion in excursions}
        for task in as_completed(running_tasks):
            logging.info('Excursion migration finished with ID: %s' % task.result())


main()
