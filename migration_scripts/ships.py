"""

This script imports ship data from Epi that are not yet added to Contentful.
Only ships that are already in Contentful are updated. The script:
- imports ship picture from Epi server if the picture is not existing already
- migrates all cabin class and grade data if not existing already
- migrates all deck plans if not existing already

Distinction between what is existing and what is not is made by Contentful entry ID.
Contentful entry ID is the same as entry ID in Epi for imported items.
To re-import entries and assets from Episerver, first delete the particular ship picture,
cabin class container or deck plan form Contentful; then run this script.
Please note that deleting the link between a ship and associated item
e.g. cabin class container will not trigger update.
The class container entry needs to be deleted.

"""

import helpers
import config
import logging
from urllib.parse import urlparse
from os.path import splitext, basename
from argparse import ArgumentParser

logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')


def prepare_environment():
    logging.info('Setup Contentful environment')
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID, config.CTFL_ENV_ID,
        config.CTFL_MGMT_API_KEY
    )

    logging.info('Using Contentful environment: %s' % config.CTFL_ENV_ID)
    logging.info('Get all ships from Contentful')
    contentful_ships = contentful_environment.entries().all(query = {"content_type": "ship"})
    logging.info('Number of ships in Contentful: %s' % len(contentful_ships))
    logging.info('')
    logging.info('-----------------------------------------------------')
    logging.info('Ship IDs to migrate: ')
    for ship in contentful_ships:
        logging.info(ship.id)
    logging.info('-----------------------------------------------------')
    logging.info('')
    return contentful_ships, contentful_environment


def update_ship(contentful_environment, ship):

    logging.info("Migrating data for ship %s, %s, %s" % (ship.name, ship.id, ship.code))

    ship_data = helpers.read_json_data("%s/%s" % ("https://www.hurtigruten.com/rest/b2b/ships", ship.code))

    image_id = "shippic-%s" % ship.code

    # add ship image
    full_image_url = "https://www.hurtigruten.com%s" % ship_data['imageUrl']
    ship.images = [
        helpers.add_asset(
            environment = contentful_environment,
            asset_uri = full_image_url,
            id = image_id,
            title = ship.name)
    ]

    try:
        ship.save()
    except Exception as e:
        logging.error('Ship could not be saved: %s' % image_id)

    try:
        ship.publish()
        logging.info("Ship %s image updated: %s" % (ship.name, image_id))
    except Exception as e:
        logging.error('Ship image could not be published: %s' % image_id)

    # add cabin categories
    for cabinCategory in ship_data['cabinCategories']:
        cabinCategoryCode = "%s-%s" % (ship.code, helpers.extract_first_letters(cabinCategory['title']))
        helpers.add_entry(
            environment = contentful_environment,
            id = cabinCategoryCode,
            content_type_id = "cabinCategory",
            fields = helpers.field_localizer(config.DEFAULT_LOCALE, {
                'code': cabinCategoryCode,
                'name': cabinCategory['title'],
                'description': helpers.convert_to_contentful_rich_text(cabinCategory['description'])
            })
        )

    # add cabin category containers with media and cabin grades if not added already
    cabin_category_container_links = []
    is_links_updated = False
    for cabinCategory in ship_data['cabinCategories']:
        cabin_container_id = "cabcatcont-%s-%s" % (ship.code, helpers.extract_first_letters(cabinCategory['title']))
        cabin_category_container_link = {}

        cabCatId = "%s-%s" % (ship.code, helpers.extract_first_letters(cabinCategory['title']))

        is_links_updated = True
        cabin_category_container_link = helpers.add_entry(
            environment = contentful_environment,
            id = "cabcatcont-%s-%s" % (ship.code, helpers.extract_first_letters(cabinCategory['title'])),
            content_type_id = "cabinCategoryContainer",
            fields = helpers.field_localizer(config.DEFAULT_LOCALE, {
                'category': helpers.entry_link(cabCatId),
                'media': [helpers.add_asset(
                    environment = contentful_environment,
                    asset_uri = media_item['highResolutionUri'],
                    id = "shCabCatPic-%s-%s-%d" % (ship.code, helpers.extract_first_letters(cabinCategory['title']), i),
                    title = media_item['alternateText']
                ) for i, media_item in enumerate(cabinCategory['media'])],
                'cabinGrades': [
                    helpers.add_entry(
                        environment = contentful_environment,
                        id = "cg-%s-%s-%s" % (
                            ship.code, helpers.extract_first_letters(cabinCategory['title']), cabinGrade['code'].replace(' ', '')
                        ),
                        content_type_id = "cabinGrade",
                        fields = helpers.field_localizer(config.DEFAULT_LOCALE, {
                            'code': cabinGrade['code'].replace(' ', ''),
                            'name': cabinGrade['title'],
                            'shortDescription': helpers.convert_to_contentful_rich_text(cabinGrade['shortDescription']),
                            'longDescription': helpers.convert_to_contentful_rich_text(cabinGrade['longDescription']),
                            'extraInformation': helpers.convert_to_contentful_rich_text(cabinGrade['extraInformation']),
                            'sizeFrom': cabinGrade['sizeFrom'],
                            'sizeTo': cabinGrade['sizeTo'],
                            'features': [x for x in [
                                'bathroom' if cabinGrade['hasBathroom'] else None,
                                'balcony' if cabinGrade['hasBalcony'] else None,
                                'sofa' if cabinGrade['hasSofa'] else None,
                                'tv' if cabinGrade['hasTv'] else None,
                                'dinnerTable' if cabinGrade['hasDinnerTable'] else None] if x is not None],
                            'bed': helpers.add_entry_with_code_if_not_exist(
                                contentful_environment, "bed",
                                cabinGrade['bed']),
                            'window': helpers.add_entry_with_code_if_not_exist(
                                contentful_environment, "window",
                                cabinGrade['window']),
                            'isSpecial': cabinGrade['isSpecial'],
                            'media': [
                                helpers.add_asset(
                                    environment = contentful_environment,
                                    asset_uri = image_url,
                                    id = "shCabGr-%s-%s-%i" % (ship.code, cabinGrade['code'].replace(' ', ''), i),
                                    title = helpers.clean_asset_name(
                                        splitext(basename(urlparse(image_url).path))[0],
                                        "shCabGr-%s-%s-%i" % (ship.code, cabinGrade['code'].replace(' ', ''), i)
                                    )
                                )
                                for i, image_url in enumerate(cabinGrade['cabinGradeImages'])]
                        })
                    )
                    for cabinGrade in cabinCategory['cabinGrades']
                ]
            })
        )

        cabin_category_container_links.append(cabin_category_container_link)

    if is_links_updated:
        ship.cabinCategories = cabin_category_container_links

        try:
            ship.save()
        except Exception as e:
            logging.error('Could not save ship cabin categories with name: %s, error: %s' % (ship.name, e))

        try:
            ship.publish()
            logging.info('Ship %s cabin categories updated' % ship.name)
        except Exception as e:
            logging.error('Could not publish ship cabin categories with name: %s, error: %s' % (ship.name, e))

    # add deck plans if not added already
    deck_plan_links = []
    is_deck_plans_updated = False
    for deck in ship_data['decks']:
        deck_number = int(deck['number'])
        deck_plan_id = "dplan-%s-%d" % (ship.code, deck_number)

        is_deck_plans_updated = True
        deck_plan_link = helpers.add_entry(
            environment = contentful_environment,
            id = deck_plan_id,
            content_type_id = "deckPlan",
            fields = helpers.field_localizer(config.DEFAULT_LOCALE, {
                "deck": deck_number,
                "plan": helpers.add_asset(
                    environment = contentful_environment,
                    asset_uri = deck['deck']['highResolutionUri'],
                    id = "deckPic-%s-%d" % (ship.code, deck_number),
                    title = helpers.clean_asset_name(
                        deck['deck']['alternateText'],
                        "deckPic-%s-%d" % (ship.code, deck_number)
                    )
                )
             })
        )

        deck_plan_links.append(deck_plan_link)

    if is_deck_plans_updated:
        ship.deckPlans = deck_plan_links
        try:
            ship.save()
        except Exception as e:
            logging.error('Could not save ship deck plans with name: %s, error: %s' % (ship.name, e))
        try:
            ship.publish()
            logging.info('Ship %s deck plans updated' % ship.name)
        except Exception as e:
            logging.error('Could not publish ship deck plans with name: %s, error: %s' % (ship.name, e))


def run_sync(**kwargs):
    ship_ids = kwargs.get('content_ids')
    include = kwargs.get('include')
    if ship_ids is not None:
        if include:
            logging.info('Running ship sync on specified IDs: %s' % ship_ids)
        else:
            logging.info('Running ship sync, skipping IDs: %s' % ship_ids)
    else:
        logging.info('Running ships sync')
    ships, contentful_environment = prepare_environment()
    for ship in ships:
        if ship_ids is not None:
            # run only included voyages
            if include and ship.id not in ship_ids:
                continue
            # skip excluded voyages
            if not include and ship.id in ship_ids:
                continue
        try:
            update_ship(contentful_environment, ship)
        except Exception as e:
            logging.error('Ship migration error with ID: %s, error: %s' % (ship.id, e))


parser = ArgumentParser(prog = 'ships.py', description = 'Run ship sync between Contentful and EPI')
parser.add_argument("-ids", "--content_ids", nargs='+', type=int, help = "Provide ship IDs")
parser.add_argument("-include", "--include", nargs='?', type=helpers.str2bool,
                    help = "Specify if you want to include or exclude ship IDs")
args = parser.parse_args()


if __name__ == '__main__':
    ids = vars(args)['content_ids']
    include = vars(args)['include']
    run_sync(**{"content_ids": ids, "include": include})
