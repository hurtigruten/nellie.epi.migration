"""

This script imports excursions from Episerver to Contentful if they already are not added
to Contentful. This is checked by Contentful entry ID. For imported excursions it is the
same as entry id in Epi. To update excursions they first need to be deleted from Contentful
and then imported from Episerver by this script.

"""
import config
import helpers
import logging
import re
import unicodedata
from argparse import ArgumentParser

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

CMS_API_URLS = {
    "en": "https://global.hurtigruten.com/rest/b2b/excursions",
    "en-US": "https://www.hurtigruten.com/rest/b2b/excursions",
    "en-AU": "https://www.hurtigruten.com.au/rest/b2b/excursions",
    "de-DE": "https://www.hurtigruten.de/rest/b2b/excursions",
    "en-GB": "https://www.hurtigruten.co.uk/rest/b2b/excursions",
    "gsw-CH": "https://www.hurtigruten.ch/rest/b2b/excursions",
    "sv-SE": "https://www.hurtigrutenresan.se/rest/b2b/excursions",
    "nb-NO": "https://www.hurtigruten.no/rest/b2b/excursions",
    "da-DK": "https://www.hurtigruten.dk/rest/b2b/excursions",
    "fr-FR": "https://www.hurtigruten.fr/rest/b2b/excursions",
}
excursions_by_locale = {}

difficulty_dict = {
    "1": "Level 1 - For everyone",
    "2": "Level 2 - Easy",
    "3": "Level 3 - Medium",
    "4": "Level 4 - Hard",
}

season_dict = {
    "1": "Winter (Nov - Mar)",
    "2": "Spring (Apr - May)",
    "4": "Summer (Jun - Aug)",
    "8": "Autumn (Sep - Oct)",
}


def relative_url_to_absolute_url(url):
    if (url[0] == '/'):
        return 'https://www.hurtigruten.co.uk' + url
    return url

def prepare_environment():
    logging.info("Setup Contentful environment")
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID, config.CTFL_ENV_ID, config.CTFL_MGMT_API_KEY
    )

    logging.info("Using Contentful environment: %s" % config.CTFL_ENV_ID)
    logging.info(
        "Get all excursions for locales: %s"
        % (", ".join([key for key, _ in CMS_API_URLS.items()]))
    )
    
    try:
        cf_es = contentful_environment.entries().all({ 'select': 'sys.id', 'limit': '999', 'content_type': 'excursion' })
        cf_eids = [int(es.id) for es in cf_es if es.id.isnumeric()]
    except Exception as e:
        print(e)
        raise Exception('gggggg')
    # return cf_eids, contentful_environment

    excursion_ids = []
    epi_excursion_ids = []

    for locale, url in CMS_API_URLS.items():
        excursions_by_locale[locale] = helpers.read_json_data(url)
        excursion_ids += [
            excursion["id"]
            for excursion in excursions_by_locale[locale]
            #if helpers.skip_entry_if_not_updated(excursion, locale, excursion["id"])
        ]
        epi_excursion_ids += [
            str(excursion["id"]) for excursion in excursions_by_locale[locale]
        ]
        # logging.info(
        #     "Number of excursions in EPI: %s for locale: %s"
        #     % (len(excursions_by_locale[locale]), locale)
        # )

    # logging.info("-----------------------------------------------------")
    # logging.info("")

    # # Create distinct list
    # excursion_ids = set(excursion_ids)
    # epi_excursion_ids = set(epi_excursion_ids)

    # logging.info("Number of migrating excursions: %s" % len(epi_excursion_ids))
    # # logging.info("")

    # # logging.info("Excursion IDs to migrate: ")
    # # for excursion_id in epi_excursion_ids:
    # #     logging.info(excursion_id)

    # logging.info("-----------------------------------------------------")
    # logging.info("")

    return cf_eids, contentful_environment

def remove_fields_if_fallback(dict, isFallback):
    if (not isFallback):
        return dict
    
    
    retain = ["bookingCode", "currency"]
    
    out = {}
    for field in retain:
        out[field] = dict.get(field)
        
    out['price'] = dict.get('price') or dict.get('priceValue')
    return out
    

def update_excursion(contentful_environment, excursion_id):
    logging.info("Excursion migration started with ID: %s" % excursion_id)

    excursion_by_locale = {}

    for locale, excursions in excursions_by_locale.items():
        # # Dont overwrite en
        # if locale == 'en':
        #     continue
        
        # Filter down to the one excursion by locale from all the excursions
        excursion = next(
            (excursion for excursion in excursions if excursion["id"] == int(excursion_id)),
            None,
        )
        if excursion is not None:
            excursion_by_locale[locale] = excursion

    default_excursion = excursion_by_locale.get(config.DEFAULT_LOCALE)
    if (default_excursion is None and len(list(excursion_by_locale.values())) > 0):
        default_excursion = list(excursion_by_locale.values())[0]

    if default_excursion is None:
        logging.info(excursion_by_locale)
        logging.info(
            "Could not find default excursion detail for excursion ID: %s"
            % excursion_id
        )
        return
    

    image_link = (
        helpers.add_or_reuse_asset(
            environment=contentful_environment,
            asset_uri= relative_url_to_absolute_url(default_excursion["image"]["imageUrl"]),
            id="excp-%s" % default_excursion["id"],
            title=default_excursion["image"]["altText"]
            or default_excursion.get("heading")
            or default_excursion.get("title"),
            file_name=default_excursion["image"]["altText"]
            or default_excursion.get("heading")
            or default_excursion.get("title"),
        )
        if default_excursion["image"] is not None
        else None
    )
    
        
    localized_image_wrapper_fields = [
        helpers.field_localizer(
            locale,
            {
                "caption": excursion['image'].get('altText') or excursion['image'].get('caption'),
                "additionalMetadata": excursion["image"].get("caption")
                if excursion.get('image') is not None
                else "",
            },
            None,
        )
        for locale, excursion in excursion_by_locale.items()
    ] if image_link is not None else None
    
    
    localized_image_wrapper_fields.append(
        helpers.field_localizer(
            config.DEFAULT_LOCALE,
            {
                "internalName": default_excursion["image"]["altText"]
                if default_excursion["image"] is not None
                else "",
                "image": image_link,
                
            },
            None,
        )
    ) if image_link is not None else None
    
    

    image_wrapper_link = (
        helpers.add_entry(
            environment=contentful_environment,
            id="excp-%s" % default_excursion["id"],
            content_type_id="imageWrapper",
            market=None,
            fields=helpers.merge_localized_dictionaries(*localized_image_wrapper_fields),
        )
        if image_link is not None
        else None
    )
    
    
    destination_ids = list(
        filter(
            None,
            [
                helpers.destination_name_to_cf_id(contentful_environment, d)
                for d in default_excursion.get("destinations")
            ],
        )
    )
    destination_links = [helpers.entry_link(di) for di in destination_ids]
    
    def epi_slug(exc):
        parts = exc.get('url', '').split('/')
        parts = list(filter(lambda x: x, parts))
        slug = parts[-1]
        return slug
    
    def get_slug(exc, locale):   
        if (locale == 'de-DE' or locale == 'gsw-CH' or True):
            return epi_slug(exc)
        slug = (exc.get("heading") or exc.get("title")).lower().strip().replace(' ', '-')
        slug = re.sub(r'[^a-zA-Z0-9-_]+', '', slug)
        slug = unicodedata.normalize('NFD', slug).encode('ascii', 'ignore').decode('utf8')
        return slug

    localized_excursion_fields = [
        helpers.field_localizer(
            locale,
            remove_fields_if_fallback({
                "slug": epi_slug(excursion),
                # "slug": get_slug(excursion, locale),
                "isOnlyBookableOnboard": excursion.get("isOnlyBookableOnboard"),
                "name": excursion.get("heading") or excursion.get("title"),
                "introduction": excursion.get("intro"),
                "description": helpers.convert_to_contentful_rich_text(
                    excursion.get("body")
                    or excursion.get("summary")
                    or default_excursion.get("body")
                ),
                "practicalInformation": helpers.convert_to_contentful_rich_text(
                    excursion.get("secondaryBody")
                )
                if excursion.get("secondaryBody")
                else None,
                "duration": excursion.get("duration")
                or excursion.get("durationText"),
                "requirements": excursion.get("requirements"),
                "difficulty": excursion["physicalLevel"][0]["text"],
                "bookingCode": excursion.get("bookingCode")
                or excursion.get("code"),
                "sellingPoints": [usp[0:255] for usp in list(
                    filter(None, excursion.get("sellingPoints") or [])
                )],
                "price": excursion.get("priceValue") or excursion.get("price") or 0,
                "currency": excursion.get("currency")
                or helpers.remove_digits(excursion.get("price") or ""),
 
                "activityCategory": [
                    re.sub(r'\s+', '', activityCategory["text"])
                    for activityCategory in excursion.get("activityCategory")
                    or []
                ],
                # "media": [image_wrapper_link] if image_wrapper_link is not None else [],
            }, excursion.get("isFallbackContent") or False),
            None,
        )
        for locale, excursion in excursion_by_locale.items()
    ]
    
    localized_excursion_fields.append(
        helpers.field_localizer(
            config.DEFAULT_LOCALE,
            {
                "internalName": default_excursion.get("heading") or default_excursion.get("title"),
                "years": [year["text"] for year in default_excursion["years"]],
                "seasons": [
                    season_dict[season["id"]] for season in default_excursion["seasons"]
                ],
                "destinations": destination_links,             
                "minimumNumberOfGuests": default_excursion.get("minimumNumberOfGuests"),
                "maximumNumberOfGuests": default_excursion.get("maximumNumberOfGuests"),
                "media": [image_wrapper_link] if image_wrapper_link is not None else [],
            },
            None,
        )
    )

    helpers.add_entry(
        environment=contentful_environment,
        id=str(excursion_id),
        content_type_id="excursion",
        market=None,
        fields=helpers.merge_localized_dictionaries(*localized_excursion_fields),
    )

    logging.info("Excursion migration finished with ID: %s" % excursion_id)


def run_sync(**kwargs):
    parameter_excursion_ids = kwargs.get("content_ids")
    include = kwargs.get("include")
    if parameter_excursion_ids is not None:
        if include:
            logging.info(
                "Running excursion sync on specified IDs: %s" % parameter_excursion_ids
            )
            [
                helpers.prepare_included_environment(parameter_excursion_ids, locale)
                for locale, url in CMS_API_URLS.items()
            ]
        else:
            logging.info(
                "Running excursion sync, skipping IDs: %s" % parameter_excursion_ids
            )
    else:
        logging.info("Running excursions sync")
    epi_excursion_ids, contentful_environment = prepare_environment()
    epi_excursion_ids = [str(i) for i in epi_excursion_ids]

    for eei, excursion_id in enumerate(parameter_excursion_ids):
        if parameter_excursion_ids is not None:
            # run only included excursions
            if include and excursion_id not in parameter_excursion_ids:
                continue
            # skip excluded excursions
            if not include and excursion_id in parameter_excursion_ids:
                continue
        try:
            update_excursion(contentful_environment, excursion_id)
            logging.info("Updated %s/%s excursions" % (eei, len(parameter_excursion_ids)))
        except Exception as e:
            logging.error(
                "Excursion migration error with ID: %s, error: %s" % (excursion_id, e)
            )
            [
                helpers.remove_entry_id_from_memory(excursion_id, locale)
                for locale, url in CMS_API_URLS.items()
            ]


parser = ArgumentParser(
    prog="excursions.py", description="Run excursion sync between Contentful and EPI"
)
parser.add_argument(
    "-ids", "--content_ids", nargs="+", type=int, help="Provide excursion IDs"
)
parser.add_argument(
    "-include",
    "--include",
    nargs="?",
    type=helpers.str2bool,
    const=True,
    default=True,
    help="Specify if you want to include or exclude " "excursion IDs",
)
args = parser.parse_args()

if __name__ == "__main__":
    ids = vars(args)["content_ids"]
    include = vars(args)["include"]
    run_sync(**{"content_ids": ids, "include": include})
