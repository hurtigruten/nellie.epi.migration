import os
from dotenv import load_dotenv
from contentful_management import Client as CMClient, errors as cm_errors
from contentful import Client as CDClient
from bs4 import BeautifulSoup
import time
import argparse

from get_voyage_included import get_voyage_included
from headings import Heading
from create_usp_collection_entry import create_usp_collection_entry
from soup_to_usp_collection import soup_to_usp_collections

load_dotenv()

CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
CONTENTFUL_CDN_KEY = os.getenv('CONTENTFUL_CDN_KEY_GLOBAL_PREVIEW')
CONTENTFUL_CMA_KEY = os.getenv('CONTENTFUL_CMA_KEY')
CONTENTFUL_ENVIRONMENT = os.getenv('CONTENTFUL_ENVIRONMENT')

parser = argparse.ArgumentParser(description='Migrate included info for voyages')
parser.add_argument('--ids', dest='ids',
                    help='List of comma-separated entry ids', required=False, default=[])

args = parser.parse_args()
voyage_ids = [str(id) for id in args.ids.split(',')]

cm_client = CMClient(access_token=CONTENTFUL_CMA_KEY, default_locale="en")
cm_env = cm_client.environments(
    CONTENTFUL_SPACE_ID).find(CONTENTFUL_ENVIRONMENT)
cd_client = CDClient(
    space_id=CONTENTFUL_SPACE_ID,
    access_token=CONTENTFUL_CDN_KEY,
    environment=CONTENTFUL_ENVIRONMENT,
    api_url='preview.contentful.com'

)

valid_locales = ['en', 'en-GB', 'en-AU', 'en-US',
                 'de-DE', 'gsw-CH', 'fr-FR', 'nb-NO', 'sv-SE', 'da-DK']


def build_usps(included):
    # included is expected to be of the form { "[locale]": [included-html], ... }
    # accepted locales are keys of [urls], i.e. en, en-GB, ...
    usp_collections = {}
    for locale, included_html in included.items():
        if included_html is None:
            continue

        soup = BeautifulSoup(included_html, 'html.parser')
        usp_collection, _ = soup_to_usp_collections(
            soup, locale)

        usp_collections[locale] = usp_collection
    # print(json.dumps(usp_collections, indent=2))
    return usp_collections

if (len(voyage_ids) == 0):
    voyage_ids = cd_client.entries({
        "content_type": "voyage",
        "select": "sys.id",
        "limit": 800,
    }).items
    voyage_ids = [v.id for v in voyage_ids]
    voyage_ids = list(filter(lambda x: x.isnumeric(), voyage_ids))
    
num_voyages = len(voyage_ids)


def group_usp_collections(usp_collections_by_locale):
    grouped_usp_collections = {}
    unknown_usp_collections = []
    for locale, usp_collections in usp_collections_by_locale.items():
        for usp_collection in usp_collections:
            if usp_collection["id"] == Heading.UNKNOWN:
                print(f'[WARNING]: Unknown heading({locale}): %s' %
                      usp_collection["title"])
                unknown_usp_collections.append(
                    {locale: usp_collection})
                continue

            id = usp_collection["id"]
            grouped_usp_collections.setdefault(id, {})
            grouped_usp_collections[id][locale] = usp_collection

    return (grouped_usp_collections, unknown_usp_collections)


def try_save(e):
    try:
        e.save()
    except:
        print('Failed to save entry, retrying in 5s...', e)
        time.sleep(5)
        try_save(e)


def try_publish(e):
    try:
        e.publish()
    except:
        print('Failed to publish, retrying in 5...', e)
        # time.sleep(5)
        # try_publish(e)


def relink_included_new(cm_env, voyage_id: str, usp_collection_entry_links, update_locales: list[str]):
    voyage = cm_env.entries().find(voyage_id)
    was_published = voyage.is_published

    # print(usp_collection_entry_links, update_locales)
    # Store old USP Collection entry ids, delete last
    # Clear the fields in the voyage
    old_usp_collection_ids = []
    for locale in valid_locales:
        # Store old entry links
        ids = voyage._fields.get(locale, {}).get('included_new', [])
        ids = [i.id for i in ids]
        old_usp_collection_ids.extend(ids)

        if locale in voyage._fields and 'included_new' in voyage._fields[locale]:
            del voyage._fields[locale]['included_new']

    # Find and link entries for this locale
    for locale in update_locales:
        usp_entries_for_locale = list(
            filter(lambda x: locale in x["locales"], usp_collection_entry_links))
        usp_entry_links_for_locale = [
            e["entry_link"] for e in usp_entries_for_locale]

        if (voyage._fields.get(locale) is None):
            voyage._fields[locale] = {}
        voyage._fields[locale]['includedNew'] = usp_entry_links_for_locale

    try_save(voyage)
    if (was_published):
        try_publish(voyage)

    print('Deleting %s old USP collections' % len(old_usp_collection_ids))
    # Delete old entries
    for usp_collection_id in old_usp_collection_ids:
        entry = None
        try:
            entry = cm_env.entries().find(usp_collection_id)
        except cm_errors.NotFoundError:
            pass

        if (entry is None):
            continue
        try:
            entry.unpublish()
        except:
            pass
        try:
            entry.delete()
        except Exception as e:
            print('Failed to delete USP Collection', e)


def get_booking_codes(cm_env, id: str) -> list[str]:
    voyage = cm_env.entries().find(id)
    booking_codes: list[str] = []
    for locale in valid_locales:
        codes = voyage._fields.get(locale, {}).get('booking_code', [])
        booking_codes.extend(codes)

    booking_codes = list(set([b.strip() for b in booking_codes]))
    if (len(booking_codes) == 0):
        return [id]
    return booking_codes


def grouped_usp_collections_to_sorted_list(grouped_usp_collections):
    collections = []

    ids_by_preference = [Heading.FLIGHTS, Heading.HOTEL, Heading.TRANSFERS]
    for id in ids_by_preference:
        collections.append(grouped_usp_collections.get(id, None))

    for id, collection in grouped_usp_collections.items():
        # Already added
        if id in ids_by_preference:
            continue

        collections.append(collection)
    return [x for x in collections if x]


voyage_ids_with_errors = []
for i, id in enumerate(voyage_ids):
    print(f"Updating voyage {i+1}/{num_voyages} ({id})")

    # Get booking codes
    booking_codes = get_booking_codes(cm_env, id)

    # Grab included from EPI, for all valid locales
    print('Fetching included from EPI...')
    included = get_voyage_included(id)

    if included is None:
        print(f'No voyage with id {id} found in EPI. Skipping...')
        continue

    # Convert included HTML into USP collections, one set for each locale
    print('Building USP Collections by locale...')
    usp_collections_by_locale = build_usps(included)

    # Regroup USPs by title
    grouped_usp_collections, unknown_usp_collections = group_usp_collections(
        usp_collections_by_locale)
    # print(json.dumps(grouped_usp_collections, indent=4))

    grouped_usp_collections_list = grouped_usp_collections_to_sorted_list(
        grouped_usp_collections)

    # Create the Contentful entries, and publish them.
    # We get back entry links, and their applicable locales
    print('Creating USP Collection entries...')
    usp_collections_entries = [create_usp_collection_entry(
        cm_env, c, booking_codes) for c in (grouped_usp_collections_list + unknown_usp_collections)]

    if None in usp_collections_entries:
        voyage_ids_with_errors.append(id)
        continue

    # Figure out which locales should be explicitly linked
    update_locales = list(usp_collections_by_locale.keys())
    update_locales = list(set(update_locales))

    print('Relinking voyage...')
    # Relink the USP Collections to the voyage
    relink_included_new(cm_env, id, usp_collections_entries, update_locales)

print('Voyage ids with error: ', voyage_ids_with_errors)
