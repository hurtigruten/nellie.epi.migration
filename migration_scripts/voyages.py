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
from typing import List
import linecache
import sys

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

CMS_API_URLS = {
    "en": "https://global.hurtigruten.com/rest/b2b/voyages",
    "en-US": "https://www.hurtigruten.com/rest/b2b/voyages",
    "en-AU": "https://www.hurtigruten.com.au/rest/b2b/voyages",
    "en-GB": "https://www.hurtigruten.co.uk/rest/b2b/voyages",
    "de-DE": "https://www.hurtigruten.de/rest/b2b/voyages",
    "gsw-CH": "https://www.hurtigruten.ch/rest/b2b/voyages",
    "sv-SE": "https://www.hurtigrutenresan.se/rest/b2b/voyages",
    "nb-NO": "https://www.hurtigruten.no/rest/b2b/voyages",
    "da-DK": "https://www.hurtigruten.dk/rest/b2b/voyages",
    "fr-FR": "https://www.hurtigruten.fr/rest/b2b/voyages",
}


def get_api_urls(market):
    if market:
        return {market: CMS_API_URLS[market]}
    return CMS_API_URLS


def extract_slug(url: str) -> str:
    # remove the trailing forward slash
    url = url[:-1]
    return url.split("/")[-1]


def make_port_entry_id(location: str) -> str:
    location.replace(", ", "")


def remove_new_line_characters(text: str) -> str:
    return text.replace("\n", "")


def remove_nones_from_list(list: List[str]) -> List[str]:
    return [item for item in list if item]


def prepare_environment(market):
    logging.info("Setup Contentful environment")
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID, config.CTFL_ENV_ID, config.CTFL_MGMT_API_KEY
    )

    api_urls = get_api_urls(market)
    logging.info("Using Contentful environment: %s" % config.CTFL_ENV_ID)
    logging.info(
        "Get all voyages for locales: %s"
        % (", ".join([key for key, value in api_urls.items()]))
    )

    logging.info('getting cf ids')
    
    cf_ids_raw = contentful_environment.content_types().find('voyage').entries().all({"limit": 1000, "select": "sys.id"})
    voyage_ids = [e.id for e in cf_ids_raw if e.id.isnumeric()]

    # voyage_ids = []
    # epi_voyage_ids = []
    # for key, value in api_urls.items():
    #     # you can just do one for loop here and append to two separate lists in the same for loop
    #     # instead of looping the entire entries twice over.
    #     voyage_ids += [
    #         voyage["id"]
    #         for voyage in helpers.read_json_data(value)
    #         # commmenting this line means all entries in EPI will be migrated
    #         # if helpers.skip_entry_if_not_updated(voyage, key, voyage["id"])
    #         if voyage["brandingType"] == "expedition"
    #     ]
    #     # epi_voyage_ids += [voyage["id"] for voyage in helpers.read_json_data(value)]

    # # Create distinct list
    # voyage_ids = set(voyage_ids)
    # epi_voyage_ids = set(epi_voyage_ids)

    # logging.info("Number of voyages in EPI: %s" % len(epi_voyage_ids))
    
    # logging.info("Voyage IDs to migrate: ")
    # for voyage_id in voyage_ids:
    #     logging.info(voyage_id)
    # logging.info("-----------------------------------------------------")
    # logging.info("")

    return voyage_ids, contentful_environment


def getInternalName(heading, bookingCodes):
    if bookingCodes is None:
        return heading
    return heading + "".join(bookingCodes)

def map_epi_locale_to_cf_locale(locale):
    if (locale == 'de-CH'):
        return 'gsw-CH'

    return locale

def update_voyage(contentful_environment, voyage_id, market):
    logging.info("Voyage migration started with ID: %s" % voyage_id)

    voyage_detail_by_locale = {}
    update_api_urls = get_api_urls(None)
    # print(update_api_urls)

    # {"uk": "uk json content for voyage with id: voyage_id", "au": "au json content for au voyage with id: voyage_id"}

    for locale, url in update_api_urls.items():
        # load all fields for the particular voyage by calling GET voyages/{id}
        contentful_locale = map_epi_locale_to_cf_locale(locale)
        voyage_detail_by_locale[contentful_locale] = helpers.read_json_data(
            "%s/%s" % (url, voyage_id)
        )

    if (voyage_detail_by_locale.get(config.DEFAULT_LOCALE)):
        default_voyage_detail = voyage_detail_by_locale.get(config.DEFAULT_LOCALE)
    else:
        default_voyage_detail = list(voyage_detail_by_locale.values())[0]
    default_locale = 'en'
    if not default_voyage_detail:
        default_locale = (voyage_detail_by_locale.keys())[0]
        default_voyage_detail = list(voyage_detail_by_locale.values())[0]

    if default_voyage_detail is None:
        logging.info(
            "Could not find default voyage detail for voyage ID: %s" % voyage_id
        )
        return

    map_wrappers = {}
    map_assets = {}
    
    asset_ = helpers.add_asset(
                        environment=contentful_environment,
                        asset_uri=default_voyage_detail["largeMap"]["highResolutionUri"],
                        id=default_voyage_detail["largeMap"]["id"].replace(":", "-") + '-' + locale.replace('-', '').lower(),
                        title=default_voyage_detail["largeMap"]["alternateText"],
                        file_name=default_voyage_detail["largeMap"]["alternateText"],
                    ) if "largeMap" in default_voyage_detail and "highResolutionUri" in (default_voyage_detail["largeMap"] or {}) else None
    
    if (asset_):
        map_assets[default_locale] = asset_
    
    try:
        for locale, voyage in voyage_detail_by_locale.items():
            if voyage is None:
                logging.info('Voyage not available for locale %s' % locale)
                continue
            if "largeMap" in voyage and "highResolutionUri" in (voyage["largeMap"] or {}):
                asset_uri = voyage["largeMap"]["highResolutionUri"]
                if (locale != 'en' and map_assets.get("en") is not None and asset_uri == (default_voyage_detail["largeMap"] or {}).get("highResolutionUri")):
                    asset = map_assets["en"]
                else:
                    asset = helpers.add_asset(
                        environment=contentful_environment,
                        asset_uri=voyage["largeMap"]["highResolutionUri"],
                        id=voyage["largeMap"]["id"].replace(":", "-") + '-' + locale.replace('-', '').lower(),
                        title=voyage["largeMap"]["alternateText"],
                        file_name=voyage["largeMap"]["alternateText"],
                    )
                    map_assets[locale] = asset
                
                if asset is None:
                    continue
                logging.info('adding map iwrapper')
                wrapper = helpers.add_entry(
                    environment=contentful_environment,
                    id=(default_voyage_detail["largeMap"] or voyage["largeMap"])["id"].replace(":", "-") + '-' + locale.replace('-', '').lower(),
                    content_type_id="imageWrapper",
                    market=market or None,
                    fields={
                            "internalName": { "en": (default_voyage_detail.get("largeMap", {}) or {}).get("alternateText") or default_voyage_detail["heading"] },
                            "caption": { locale: voyage["heading"] },
                            "image": { "en": asset }
                        },
                )
                
                map_wrappers[locale] = wrapper
    except:
        PrintException()


    image_gallery_id = ""
    image_wrapper_links = []
    for i, media_item in enumerate(default_voyage_detail["mediaContent"]):
        media_link = helpers.add_or_reuse_asset(
            environment=contentful_environment,
            asset_uri=media_item["highResolutionUri"],
            id=media_item["id"],
            title=media_item["alternateText"],
        )
        image_gallery_id += media_item["id"]

        localized_image_wrapper_fields = [
            helpers.field_localizer(
                locale,
                {
                    "caption": voyage_detail["mediaContent"][i]["alternateText"] or '',
                    # "internalName": media_item["alternateText"] or '',
                    # "image": media_link,
                    "additionalMetadata": media_item["alternateText"],
                },
                None,
            ) for locale, voyage_detail in voyage_detail_by_locale.items() if len(voyage_detail["mediaContent"]) > i
        ]
        localized_image_wrapper_fields.append(
            helpers.field_localizer(
                config.DEFAULT_LOCALE,
                {
                    "internalName": media_item["alternateText"] or '',
                    "image": media_link,
                },
                None,
            )
        )

        image_wrapper_link = helpers.add_entry(
            environment=contentful_environment,
            id=media_item["id"],
            content_type_id="imageWrapper",
            market=market or None,
            fields=helpers.merge_localized_dictionaries(*localized_image_wrapper_fields),
        )
        image_wrapper_links.append(image_wrapper_link)

    image_gallery_id += "_gallery"

    if (helpers.is_entry_exists(contentful_environment, image_gallery_id)):
        image_gallery_link = helpers.entry_link(image_gallery_id)
    else:
        image_gallery_link = helpers.add_entry(
            environment=contentful_environment,
            id=image_gallery_id,
            content_type_id="imageGallery",
            market=market or None,
            fields=helpers.field_localizer(
                config.DEFAULT_LOCALE,
                {
                    "internalName": default_voyage_detail["heading"],
                    "images": image_wrapper_links,
                    "title": default_voyage_detail["heading"],
                },
                None,
            ),
        )

    # Assuming that itinerary days are the same for every locale
    # Check if there's available itinerary for a given locale, and filter out locales which don't have any itineraries
    voyage_detail_by_locale_itineraries = {}
    itinerary_list = []
    length_of_list = len(default_voyage_detail["itinerary"])
    for locale, locale_voyage_detail in voyage_detail_by_locale.items():
        if (
            "itinerary" not in locale_voyage_detail
            or len(locale_voyage_detail["itinerary"]) == 0
        ):
            logging.warning(
                "Itinerary is not available in %s for %s" % (locale, voyage_id)
            )
        if len(locale_voyage_detail["itinerary"]) != length_of_list:
            logging.error(
                "Itinerary has to many itineraries. Rerun migration for %s" % locale
            )
        else:
            voyage_detail_by_locale_itineraries[locale] = locale_voyage_detail
            itinerary_list = locale_voyage_detail["itinerary"]

    all_itinerary_day_images = []
    for i, day in enumerate(itinerary_list):
        itinerary_day_images = []
        it_day_media_content = day["mediaContent"]
        for media_item in it_day_media_content:
            it_day_image_wrapper = helpers.add_entry(
                environment=contentful_environment,
                id=media_item["id"],
                content_type_id="imageWrapper",
                market=market or None,
                fields=helpers.merge_localized_dictionaries(
                    helpers.field_localizer(
                      locale,
                      {
                          "caption": media_item["alternateText"],
                      },
                      None
                    ),
                    helpers.field_localizer(
                        config.DEFAULT_LOCALE,
                        {
                            "internalName": media_item["alternateText"],
                            "image": helpers.add_or_reuse_asset(
                                environment=contentful_environment,
                                asset_uri=media_item["highResolutionUri"],
                                id=media_item["id"],
                                title=media_item["alternateText"],
                            ),
                            # "additionalMetadata": media_item["alternateText"],
                        },
                        None,
                    )
                ),
            )
            itinerary_day_images.append(it_day_image_wrapper)
        all_itinerary_day_images.append(itinerary_day_images)
    # logging.info("All it day images")
    # logging.info(all_itinerary_day_images)
    
    itinerary = []
    for i, _ in enumerate(itinerary_list):
        itinerary_localized_fields = [
            helpers.field_localizer(
                locale,
                {
           
                    "day": locale_voyage_detail["itinerary"][i]["day"],
                    "title": locale_voyage_detail["itinerary"][i]["heading"] or default_voyage_detail["itinerary"][i]["day"],
                    "longDescription": helpers.convert_to_contentful_rich_text(
                        locale_voyage_detail["itinerary"][i]["body"]
                    ),
          
                },
                market,
            )
            for locale, locale_voyage_detail in voyage_detail_by_locale_itineraries.items() if not locale_voyage_detail["itinerary"][i]["isFallbackContent"]
        ]
        itinerary_localized_fields.append(
            helpers.field_localizer(
                config.DEFAULT_LOCALE,
                {
                    "internalName": default_voyage_detail["itinerary"][i][
                        "heading"
                    ] or default_voyage_detail["itinerary"][i]["day"],
             
                    "highlightedImage": all_itinerary_day_images[i],
                    "availableExcursions": [eid for eid in [
                        helpers.entry_link(excursion_id)
                        for excursion_id in locale_voyage_detail["itinerary"][
                            i
                        ]["includedExcursions"] if excursion_id
                    ] if eid],
                },
                None,
        ))

        itinerary.append(
            helpers.add_entry(
            environment=contentful_environment,
            id="itday%s-%d" % (voyage_id, i),
            content_type_id="itinerary",
            market=market or None,
            fields=helpers.merge_localized_dictionaries(*itinerary_localized_fields),
            )
        )    

    destination_cfid = helpers.destination_epi_id_to_cf_id(
        contentful_environment, default_voyage_detail["destinationId"]
    )
    logging.info("Found dcfid %s" % destination_cfid)
    destination_links = (
        [helpers.entry_link(destination_cfid)] if destination_cfid is not None else []
    )
    
    excursions_url = "https://www.hurtigruten.com/rest/excursion/voyages/" + str(voyage_id) + "/excursions"
    programs_url = "https://www.hurtigruten.com/rest/program/voyages/" + str(voyage_id) + "/excursions"
    
    excursions = helpers.read_json_data(excursions_url)
    programs = helpers.read_json_data(programs_url)
    
    excursion_links =[helpers.entry_link(excursion) for excursion in excursions if excursion is not None and helpers.is_entry_exists(contentful_environment, excursion)]
    program_links = [helpers.entry_link(program) for program in programs if program is not None and helpers.is_entry_exists(contentful_environment, program)]
  
    all_booking_codes = [voyage_detail["travelSuggestionCodes"] for locale, voyage_detail in voyage_detail_by_locale.items()]
    all_booking_codes = [e for v in all_booking_codes for e in v]
    all_booking_codes = [bc.strip() for bc in all_booking_codes]
    all_booking_codes = list(set(all_booking_codes))
    
    def get_subtitle(heading):
        titles = heading.split('-')
        if (len(titles) > 1):
            return titles[1].strip()
        return ''

    def extract_slug(url):
        if not url:
            return None
        try:    
             return  [p for p in url.split("/") if p][-1]
        except:
            return None
        
    
    
    voyage_localized_fields = [
        helpers.field_localizer(
            locale,
            {
                "map": map_wrappers.get(locale),
                "isAttemptVoyage": voyage_detail['isAttemptVoyage'],
                "attemptText": helpers.convert_to_contentful_rich_text(voyage_detail['attemptText']),
                "name": voyage_detail["heading"],
                "title": voyage_detail["heading"].split('-')[0],
                "subtitle": get_subtitle(voyage_detail["heading"]),
                "slug": extract_slug(voyage_detail["url"]) or voyage_detail["heading"].strip().lower().replace(' ', '-').replace(',',''),
                "bookingCode": voyage_detail["travelSuggestionCodes"],
                "shortDescription": helpers.convert_to_contentful_rich_text(
                    voyage_detail["itineraryOneLiner"]
                ),
                "longDescription": helpers.convert_to_contentful_rich_text(
                    voyage_detail["itineraryIntro"]
                ),
                "included": helpers.convert_to_contentful_rich_text(
                    voyage_detail["includedInfo"]
                ),
                "notIncluded": helpers.convert_to_contentful_rich_text(
                    voyage_detail["notIncludedInfo"]
                ),
                "usPs": [
                    usp[:255]
                    for usp in remove_nones_from_list(
                        voyage_detail["sellingPoints"]
                    )
                ],
                "bookable": voyage_detail["isBookable"], 
            },
            market,
        )
        for locale, voyage_detail in voyage_detail_by_locale.items() if not voyage_detail["isFallbackContent"]
    ]
    
    # Some fields should be migrated regardless of fallback. For now, just booking codes
    fallback_count = 0
    for idx, (locale, voyage_detail) in enumerate(voyage_detail_by_locale.items()):
        if (voyage_detail["isFallbackContent"]):
            voyage_localized_fields.append({"bookingCode": { locale: voyage_detail["travelSuggestionCodes"] }})
            fallback_count += 1
        else:
            voyage_localized_fields[idx - fallback_count]["bookingCode"] = { locale: voyage_detail["travelSuggestionCodes"] }
        
    
    
    voyage_localized_fields.append(
        helpers.field_localizer(
            config.DEFAULT_LOCALE,
            {
                "internalName": ",".join(all_booking_codes) + ' - ' + default_voyage_detail["heading"],
                "highlightedImage": image_wrapper_links[-1],
                "itinerary": itinerary,
                "ships": helpers.get_cf_ship_link_from_ship_code(contentful_environment,
                    default_voyage_detail["shipCodes"]
                ),
                "destination": destination_links,
                "productType": "Expedition",
                "excursions": excursion_links,
                "programs": program_links,
                "images": image_gallery_link,
            },
            None
        )
    )
    
    merged_fields = helpers.merge_localized_dictionaries(*voyage_localized_fields)
    # Update bookable separately, it's exempt from fallback rules
    for locale, voyage_detail in voyage_detail_by_locale.items():
        if not "bookable" in merged_fields:
            merged_fields["bookable"] = {}
        merged_fields["bookable"] = {**merged_fields["bookable"], **{ locale: voyage_detail["isBookable"] }}
    
    helpers.add_entry(
        environment=contentful_environment,
        id=str(voyage_id),
        content_type_id="voyage",
        market=market or None,
        fields=merged_fields,
    )

    for locale, url in update_api_urls.items():
        helpers.update_entry_database(voyage_id, locale)

    logging.info("Voyage migration finished with ID: %s" % voyage_id)




def run_sync(**kwargs):
    parameter_voyage_ids = kwargs.get("content_ids")
    include = kwargs.get("include")
    market = kwargs.get("market")

    if parameter_voyage_ids is not None:
        if include:
            logging.info(
                "Running voyages sync on specified IDs: %s" % parameter_voyage_ids
            )
            # [
            #     helpers.prepare_included_environment(parameter_voyage_ids, locale)
            #     for locale, url in CMS_API_URLS.items()
            # ]
        else:
            logging.info(
                "Running voyages sync, skipping IDs: %s" % parameter_voyage_ids
            )
    else:
        logging.info("Running voyages sync")

    voyage_ids, contentful_environment = prepare_environment(None)
    
    logging.info("")
    logging.info("Number of voyages to update: %s" % len(voyage_ids))
    logging.info("-----------------------------------------------------")

    total_voyages = len(voyage_ids)
    
    for idx, voyage_id in enumerate(voyage_ids):
        if parameter_voyage_ids is not None:
            # run only included voyages
            if include and voyage_id not in parameter_voyage_ids:
                continue
            # skip excluded voyages
            if not include and voyage_id in parameter_voyage_ids:
                continue
        try:
            logging.info('yay')
            update_voyage(contentful_environment, voyage_id, market)
        except Exception as e:
            PrintException()
            logging.info(f"Error is {e}")
            logging.error(
                "Voyage migration error with ID: %s, error: %s" % (voyage_id, e)
            )
            logging.info("Entry %s/%s" % (idx, len(voyage_ids)))
           
        logging.info("-----------------------------------------------------")
        logging.info(f"Completed {idx+1}/{total_voyages} Voyages.")
        logging.info("-----------------------------------------------------")


parser = ArgumentParser(
    prog="voyages.py", description="Run voyage sync between Contentful and EPI"
)
parser.add_argument(
    "-ids", "--content_ids", nargs="+", type=int, help="Provide voyage IDs"
)
parser.add_argument(
    "-include",
    "--include",
    nargs="?",
    type=helpers.str2bool,
    const=True,
    default=True,
    help="Specify if you want to include or exclude voyage IDs",
)
args = parser.parse_args()

if __name__ == "__main__":
    ids = vars(args)["content_ids"]
    include = vars(args)["include"]
    run_sync(**{"content_ids": ids, "include": include})