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
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

CMS_API_URLS = {
    # "en-US": "https://www.hurtigruten.com/rest/b2b/voyages"
    "en": "https://global.hurtigruten.com/rest/b2b/excursions",
    # "EN-AMERICAS": "https://www.hurtigruten.com/rest/excursion/excursions",
    "en-GB": "https://www.hurtigruten.co.uk/rest/b2b/excursions",
    "en-AU": "https://www.hurtigruten.com.au/rest/b2b/excursions",
    # "de": "https://www.hurtigruten.de/rest/excursion/excursions",
    # "fr-FR": "https://www.hurtigruten.fr/rest/excursion/excursions"
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


def prepare_environment():
    logging.info("Setup Contentful environment")
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID, config.CTFL_ENV_ID, config.CTFL_MGMT_API_KEY
    )

    logging.info("Using Contentful environment: %s" % config.CTFL_ENV_ID)
    logging.info(
        "Get all excursions for locales: %s"
        % (", ".join([key for key, value in CMS_API_URLS.items()]))
    )

    excursion_ids = []
    epi_excursion_ids = []

    for locale, url in CMS_API_URLS.items():
        excursions_by_locale[locale] = helpers.read_json_data(url)
        excursion_ids += [
            excursion["id"]
            for excursion in excursions_by_locale[locale]
            if helpers.skip_entry_if_not_updated(excursion, locale, excursion["id"])
        ]
        epi_excursion_ids += [
            excursion["id"] for excursion in excursions_by_locale[locale]
        ]
        logging.info(
            "Number of excursions in EPI: %s for locale: %s"
            % (len(excursions_by_locale[locale]), locale)
        )

    logging.info("-----------------------------------------------------")
    logging.info("")

    # Create distinct list
    excursion_ids = set(excursion_ids)
    epi_excursion_ids = set(epi_excursion_ids)

    logging.info("Number of migrating excursions: %s" % len(epi_excursion_ids))
    logging.info("")

    logging.info("Excursion IDs to migrate: ")
    for excursion_id in epi_excursion_ids:
        logging.info(excursion_id)

    logging.info("-----------------------------------------------------")
    logging.info("")

    return epi_excursion_ids, contentful_environment


def update_excursion(contentful_environment, excursion_id):
    logging.info("Excursion migration started with ID: %s" % excursion_id)

    excursion_by_locale = {}

    for locale, excursions in excursions_by_locale.items():
        # Filter down to the one excursion by locale from all the excursions
        excursion = next(
            (excursion for excursion in excursions if excursion["id"] == excursion_id),
            None,
        )
        if excursion is not None:
            excursion_by_locale[locale] = excursion

    default_excursion = excursion_by_locale[config.DEFAULT_LOCALE]

    if default_excursion is None:
        logging.info(
            "Could not find default excursion detail for excursion ID: %s"
            % excursion_id
        )
        return

    image_link = (
        helpers.add_or_reuse_asset(
            environment=contentful_environment,
            asset_uri=default_excursion["image"]["imageUrl"],
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

    image_wrapper_link = (
        helpers.add_entry(
            environment=contentful_environment,
            id="excp-%s" % default_excursion["id"],
            content_type_id="imageWrapper",
            market=None,
            fields=helpers.merge_localized_dictionaries(
                *(
                    helpers.field_localizer(
                        locale,
                        {
                            "internalName": excursion["image"]["altText"]
                            if excursion["image"] is not None
                            else "",
                            "image": image_link,
                            "additionalMetadata": excursion["image"]["caption"]
                            if excursion["image"] is not None
                            else "",
                        },
                        None,
                    )
                    for locale, excursion in excursion_by_locale.items()
                )
            ),
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

    helpers.add_entry(
        environment=contentful_environment,
        id=str(excursion_id),
        content_type_id="excursion",
        market=None,
        fields=helpers.merge_localized_dictionaries(
            *(
                helpers.field_localizer(
                    locale,
                    {
                        "internalName": excursion.get("heading")
                        or excursion.get("title"),
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
                        "years": [year["text"] for year in excursion["years"]],
                        "seasons": [
                            season_dict[season["id"]] for season in excursion["seasons"]
                        ],
                        "destinations": destination_links,
                        "duration": excursion.get("duration")
                        or excursion.get("durationText"),
                        "requirements": excursion.get("requirements"),
                        "difficulty": excursion["physicalLevel"][0]["text"],
                        "bookingCode": excursion.get("bookingCode")
                        or excursion.get("code"),
                        "sellingPoints": list(
                            filter(None, excursion.get("sellingPoints") or [])
                        ),
                        "price": excursion.get("priceValue")
                        or excursion.get("price")
                        or 0,
                        "currency": excursion.get("currency")
                        or helpers.remove_digits(excursion.get("price") or ""),
                        "minimumNumberOfGuests": excursion.get("minimumNumberOfGuests"),
                        "maximumNumberOfGuests": excursion.get("maximumNumberOfGuests"),
                        "activityCategory": [
                            activityCategory["text"]
                            for activityCategory in excursion.get("activityCategory")
                            or []
                        ],
                        "media": [image_wrapper_link]
                        if image_wrapper_link is not None
                        else [],
                    },
                    None,
                )
                for locale, excursion in excursion_by_locale.items()
            )
        ),
    )

    for locale, url in CMS_API_URLS.items():
        helpers.update_entry_database(excursion_id, locale)

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
    excursion_ids, contentful_environment = prepare_environment()

    for excursion_id in excursion_ids:
        if parameter_excursion_ids is not None:
            # run only included excursions
            if include and excursion_id not in parameter_excursion_ids:
                continue
            # skip excluded excursions
            if not include and excursion_id in parameter_excursion_ids:
                continue
        try:
            update_excursion(contentful_environment, excursion_id)
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
