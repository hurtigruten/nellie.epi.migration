"""

This script imports programs from Episerver to Contentful if they already are not added
to Contentful. This is checked by Contentful entry ID. For imported programs it is the
same as entry id in Epi. To update programs they first need to be deleted from Contentful
and then imported from Episerver by this script.

"""
import config
import helpers
import logging
import unicodedata
import re
from argparse import ArgumentParser

logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')

CMS_API_URLS = {
    # "en-US": "https://www.hurtigruten.com/rest/b2b/voyages"
    "en": "https://global.hurtigruten.com/rest/b2b/programs",
    # "EN-AMERICAS": "https://www.hurtigruten.com/rest/program/programs",
    "en-GB": "https://www.hurtigruten.co.uk/rest/b2b/programs",
    "en-AU": "https://www.hurtigruten.com.au/rest/b2b/programs",
    # "de": "https://www.hurtigruten.de/rest/program/programs",
    # "fr-FR": "https://www.hurtigruten.fr/rest/program/programs"
}

programs_by_locale = {}

season_dict = {
    '1': 'Winter (Nov - Mar)',
    '2': 'Spring (Apr - May)',
    '4': 'Summer (Jun - Aug)',
    '8': 'Autumn (Sep - Oct)'
}


def prepare_environment():
    logging.info('Setup Contentful environment')
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID,
        config.CTFL_ENV_ID,
        config.CTFL_MGMT_API_KEY)

    logging.info('Using Contentful environment: %s' % config.CTFL_ENV_ID)
    logging.info('Get all programs for locales: %s' % (", ".join([key for key, value in CMS_API_URLS.items()])))

    epi_program_ids = []

    for locale, url in CMS_API_URLS.items():
        programs_by_locale[locale] = helpers.read_json_data(url)
        epi_program_ids += [program['id'] for program in programs_by_locale[locale]]
        logging.info(
            'Number of programs in EPI: %s for locale: %s' % (len(programs_by_locale[locale]), locale))

    logging.info('-----------------------------------------------------')
    logging.info('')

    # Create distinct list
    epi_program_ids = set(epi_program_ids)

    logging.info('Number of migrating programs: %s' % len(epi_program_ids))
    logging.info('')

    logging.info('Program IDs to migrate: ')
    for program_id in epi_program_ids:
        logging.info(program_id)

    logging.info('-----------------------------------------------------')
    logging.info('')

    return epi_program_ids, contentful_environment


def update_program(contentful_environment, program_id):
    logging.info('Program migration started with ID: %s' % program_id)

    program_by_locale = {}

    for locale, programs in programs_by_locale.items():
        # Filter down to the one program by locale from all the programs
        program = next((program for program in programs if program['id'] == program_id), None)
        if program is not None:
            program_by_locale[locale] = program

    default_program = program_by_locale[config.DEFAULT_LOCALE]

    if default_program is None:
        logging.info('Could not find default program detail for program ID: %s' % program_id)
        return

    # helpers.merge_localized_dictionaries(
    #             *(
    #                 helpers.field_localizer(
    #                     locale,
    #                     {
             
    #                         "availableExcursions": [
    #                             helpers.entry_link(excursion_id)
    #                             for excursion_id in locale_voyage_detail["itinerary"][
    #                                 i
    #                             ]["includedExcursions"]
    #                         ],
    #                     },
    #                     market,
    #                 )
    #                 for locale, locale_voyage_detail in voyage_detail_by_locale_itineraries.items()

    #image_gallery_id = "program-gallery-%s-" % str(program_id)
    #image_wrapper_links = []
    #for i, media_item in enumerate(default_program["mediaContent"]):
    #    media_link = helpers.add_or_reuse_asset(
    #        environment=contentful_environment,
    #        asset_uri=media_item["highResolutionUri"],
    #        id=media_item["id"],
    #        title=media_item["alternateText"],
    #    )
        #image_gallery_id += media_item["id"]#

    #    image_wrapper_link = helpers.add_entry(
    #        environment=contentful_environment,
    #        id=media_item["id"],
    #        content_type_id="imageWrapper",
    #        market=None,
    #        fields=helpers.merge_localized_dictionaries( *(helpers.field_localizer(
    #            locale,
    #            {
    #                "internalName": locale_program["mediaContent"][i]["alternateText"],
    #                "image": media_link,
    #                "additionalMetadata": locale_program["mediaContent"][i]["alternateText"]
    #            },
    #            None,
    #        ) for locale, locale_program in program_by_locale.items()))
    #    )
    #    image_wrapper_links.append(image_wrapper_link)

    #image_gallery_id += "_gallery"

    # image_gallery_link = helpers.add_entry(
    #     environment=contentful_environment,
    #     id=image_gallery_id,
    #     content_type_id="imageGallery",
    #     market=None,
    #     fields=helpers.field_localizer(
    #         config.DEFAULT_LOCALE,
    #         {
    #             "internalName": default_program["heading"],
    #             "images": image_wrapper_links,
    #             "title": default_program["heading"],
    #         },
    #         None,
    #     ),
    # )

    # image_link = helpers.add_or_reuse_asset(
    #     environment=contentful_environment,
    #     asset_uri=default_program["image"]["imageUrl"],
    #     id="excp-%s" % default_program['id'],
    #     title=default_program["image"]["altText"] or default_program.get('heading') or default_program.get('title'),
    #     file_name=default_program["image"]["altText"] or default_program.get('heading') or default_program.get('title'),
    # ) if default_program["image"] is not None else None
    

    # image_wrapper_link = helpers.add_entry(
    #     environment=contentful_environment,
    #     id="excp-%s" % default_program['id'],
    #     content_type_id="imageWrapper",
    #     market=None,
    #     fields=helpers.merge_localized_dictionaries(
    #         *(
    #             helpers.field_localizer(
    #                 locale,
    #                 {
    #                     "internalName": program["image"]['altText'] if program['image'] is not None else '',
    #                     "image": image_link,
    #                     "additionalMetadata": program["image"]['caption'] if program['image'] is not None else '',
    #                 },
    #                 None,
    #             )
    #             for locale, program in program_by_locale.items()
    #         )
    #     ),
    # ) if image_link is not None else None

    destination_ids = list(filter(None, [helpers.destination_name_to_cf_id(contentful_environment, d) for d in default_program.get('destinations')]))
    destination_links = [helpers.entry_link(di) for di in destination_ids]
    
    slug = (program.get("heading") or program.get("title")).lower().strip().replace(' ', '-')
    slug = re.sub(r'[^a-zA-Z0-9-_]+', '', slug)
    slug = unicodedata.normalize('NFD', slug).encode('ascii', 'ignore').decode('utf8')

    helpers.add_entry(
        environment = contentful_environment,
        id = str(program_id),
        content_type_id = "program",
        market = None,
        fields = helpers.merge_localized_dictionaries(*(
            helpers.field_localizer(locale, {
                "slug": slug,
                #'internalName': program.get('heading') or program.get('title'),
                #'name': program.get('heading') or program.get('title'),
                #'introduction': program.get('intro'),
                #'description': helpers.convert_to_contentful_rich_text(program.get('body') or program.get('summary') or default_program.get('body')),
                #'practicalInformation': helpers.convert_to_contentful_rich_text(program.get('secondaryBody')) if program.get('secondaryBody') else None,
                #'years': [year['text'] for year in program.get('years') or []],
                #'seasons': [season_dict[season['id']] for season in program['seasons']],
                #'destinations': destination_links,
                #'durationHours': program.get('durationHours'),
                #'durationDays': program.get('durationDays'),
                #'bookingCode': program.get('bookingCode') or program.get('code'),
                #'sellingPoints': list(filter(None, program.get('sellingPoints') or [])),
                #'price': program.get('priceValue') or program.get('price') or 0,
                #'currency': program.get('currency') or helpers.remove_digits(program.get('price') or ''),
                #'minimumNumberOfGuests': program.get('minimumNumberOfGuests'),
                #'maximumNumberOfGuests': program.get('maximumNumberOfGuests'),
                #'media': image_wrapper_links
            }, None) for locale, program in program_by_locale.items()
        ))
    )

    for locale, url in CMS_API_URLS.items():
        helpers.update_entry_database(program_id, locale)

    logging.info('Program migration finished with ID: %s' % program_id)


def run_sync(**kwargs):
    parameter_program_ids = kwargs.get('content_ids')
    include = kwargs.get('include')
    if parameter_program_ids is not None:
        if include:
            logging.info('Running program sync on specified IDs: %s' % parameter_program_ids)
            [helpers.prepare_included_environment(parameter_program_ids, locale) for locale, url in
             CMS_API_URLS.items()]
        else:
            logging.info('Running program sync, skipping IDs: %s' % parameter_program_ids)
    else:
        logging.info('Running programs sync')
    program_ids, contentful_environment = prepare_environment()
    for idx, program_id in enumerate(program_ids):
        if parameter_program_ids is not None:
            # run only included programs
            if include and program_id not in parameter_program_ids:
                continue
            # skip excluded programs
            if not include and program_id in parameter_program_ids:
                continue
        try:
            logging.info('Updating program %s/%s' % (idx, len(program_ids)))
            update_program(contentful_environment, program_id)
        except Exception as e:
            logging.error('Program migration error with ID: %s, error: %s' % (program_id, e))
            [helpers.remove_entry_id_from_memory(program_id, locale) for locale, url in CMS_API_URLS.items()]


parser = ArgumentParser(prog = 'programs_nellie.py', description = 'Run program sync between Contentful and EPI')
parser.add_argument("-ids", "--content_ids", nargs = '+', type = int, help = "Provide program IDs")
parser.add_argument("-include", "--include", nargs = '?', type = helpers.str2bool, const = True, default = True,
                    help = "Specify if you want to include or exclude "
                           "program IDs")
args = parser.parse_args()

if __name__ == '__main__':
    ids = vars(args)['content_ids']
    include = vars(args)['include']
    run_sync(**{"content_ids": ids, "include": include})
