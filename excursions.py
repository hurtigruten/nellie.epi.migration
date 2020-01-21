"""

This script imports excursions from Episerver to Contentful if they already are not added
to Contentful. This is checked by Contentful entry ID. For imported excursions it is the
same as entry id in Epi. To update excursions they first need to be deleted from Contentful
and then imported from Episerver by this script.

"""
import config
import helpers
import logging
from argparse import ArgumentParser

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


def prepare_environment():
    logging.info('Setup Contentful environment')
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID,
        config.CTFL_ENV_ID,
        config.CTFL_MGMT_API_KEY)

    logging.info('Get all excursions')
    excursions = helpers.read_json_data(CMS_API_URL)
    logging.info('Number of excursions in EPI: %s' % len(excursions))
    return excursions, contentful_environment


def update_excursion(contentful_environment, excursion, only_with_excursion_ids=None):

    if only_with_excursion_ids is not None and excursion['id'] not in only_with_excursion_ids:
        return

    logging.info('Excursion migration started with ID: %s' % excursion['id'])

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
                    title = helpers.clean_asset_name(excursion['image']['altText'] or excursion['title'],
                                                     excursion['id']))
            ] if excursion['image'] is not None else []
        })
    )

    logging.info('Excursion migration finished with ID: %s' % excursion['id'])


def run_sync(only_with_excursion_ids=None):
    if only_with_excursion_ids is not None:
        logging.info('Running excursions migration sync on specified IDs: %s' % only_with_excursion_ids)
    else:
        logging.info('Running excursions migration sync')
    excursions, contentful_environment = prepare_environment()
    for excursion in excursions:
        update_excursion(contentful_environment, excursion, only_with_excursion_ids)


parser = ArgumentParser(prog = 'excursions.py', description = 'Run excursion sync between Contentful and EPI')
parser.add_argument("-ids", "--content_ids", nargs='+', type=int, help = "Provide the IDs you want to run the sync on")
args = parser.parse_args()

if __name__ == '__main__':
    ids = vars(args)['content_ids']
    run_sync(only_with_excursion_ids = ids)
