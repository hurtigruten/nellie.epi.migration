import os
from dotenv import load_dotenv
from contentful_management import Client as CMClient
from contentful import Client as CDClient
import time
from typing import Union

from get_voyage_included import get_voyage_not_included

load_dotenv()

CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
CONTENTFUL_CDN_KEY = os.getenv('CONTENTFUL_CDN_KEY_GLOBAL_PREVIEW')
CONTENTFUL_CMA_KEY = os.getenv('CONTENTFUL_CMA_KEY')
CONTENTFUL_ENVIRONMENT = os.getenv('CONTENTFUL_ENVIRONMENT')

print(CONTENTFUL_ENVIRONMENT)

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

def get_voyage_ids():
    try:
        return cd_client.entries({
            "content_type": "voyage",
            "select": "sys.id",
            "limit": 600,
        }).items
    except:
        print('Retrying in 5..')
        time.sleep(5)
        return get_voyage_ids()
    
voyage_ids = get_voyage_ids()

voyage_ids = [v.id for v in voyage_ids]

voyage_ids = list(filter(lambda x: x.isnumeric(), voyage_ids))
num_voyages = len(voyage_ids)

voyage_ids_with_errors = []
for i, id in enumerate(voyage_ids):
    print(f"Updating voyage {i+1}/{num_voyages} ({id})")
    
    # Grab not_included from EPI, for all valid locales
    print('Fetching not_included from EPI...')
    not_included = get_voyage_not_included(id)

    if not_included is None:
        print(f'No voyage with id {id} found in EPI. Skipping...')
        continue

    voyage = cm_env.entries().find(id)
    was_published = voyage.is_published

    changed = False
    for locale, field_value in not_included.items():
        if not locale in voyage._fields:
            voyage._fields[locale] = {}
        voyage._fields[locale]["not_included"] = field_value
        changed = True
    if not changed:
        continue

    voyage.save()
    if (was_published):
        try:
            voyage.publish()
        except:
            voyage_ids_with_errors.append(id)
    