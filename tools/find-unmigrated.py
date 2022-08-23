import json
import contentful_management
import contentful
import os
from urllib.request import urlopen, Request
from dotenv import load_dotenv
import argparse


def entry_conditions(entry_, entry_type_):
    if (entry_type_ == 'voyage'):
        # and entry_['isBookable'] == True
        return entry_['brandingType'] == 'expedition'
    return True


env_vars = load_dotenv()

CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
CONTENTFUL_CDN_KEY = os.getenv('CONTENTFUL_CDN_KEY_GLOBAL_PREVIEW')

CONTENTFUL_CMA_KEY = os.getenv('CONTENTFUL_CMA_KEY_GLOBAL')
CONTENTFUL_ENVIRONMENT = os.getenv('CONTENTFUL_ENVIRONMENT')

parser = argparse.ArgumentParser(description='Find unmigrated entries')
parser.add_argument('--entry_type', dest='entry_type',
                    help='Valid values: [voyage, excursion, program]')

args = parser.parse_args()
entry_type = args.entry_type

valid_entry_types = ['voyage', 'excursion', 'program']
if (not entry_type in valid_entry_types):
    print('Invalid entry type: %s' % entry_type)
    quit()

epi_ids = []

base_urls_by_locale = ["https://global.hurtigruten.com/rest/b2b/",
                       "https://www.hurtigruten.com.au/rest/b2b/",
                       "https://www.hurtigruten.co.uk/rest/b2b/",
                       "https://www.hurtigruten.com/rest/b2b/",
                       "https://www.hurtigruten.de/rest/b2b/",
                       "https://www.hurtigruten.ch/rest/b2b/"
                       ]

for url in base_urls_by_locale:
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Magic ZBrowser'
    }

    req = Request(url + entry_type + 's', headers=headers)

    res = urlopen(req).read()
    epi_entries = json.loads(res.decode('utf-8'))

    epi_ids.extend(
        [str(entry['id']) for entry in epi_entries if entry_conditions(entry, entry_type)])

client = contentful.Client(
    CONTENTFUL_SPACE_ID, CONTENTFUL_CDN_KEY, 'preview.contentful.com', environment=CONTENTFUL_ENVIRONMENT)
cf_entries = client.entries({
    'content_type': entry_type,
    'select': 'sys.id',
    'sys.archivedAt[exists]': 'true',
    'limit': 1000
}).items

cf_entry_ids = [entry.id for entry in cf_entries]

epi_ids = set(epi_ids)
cf_entry_ids = set(cf_entry_ids)

unmigrated_ids = epi_ids.difference(cf_entry_ids)

# Check with CMA if any of these are archived
cma = contentful_management.Client(CONTENTFUL_CMA_KEY)
cma_env = cma.environments(CONTENTFUL_SPACE_ID).find(CONTENTFUL_ENVIRONMENT)
cma_entry_type = cma_env.content_types().find(entry_type)
archived_ids = []
for unmigrated_id in unmigrated_ids:
    try:
        entry = cma_entry_type.entries().find(
            unmigrated_id, {"sys.archivedAt[exists]": True})
        archived_ids.append(unmigrated_id)
    except Exception as e:
        pass
unmigrated_ids = unmigrated_ids.difference(archived_ids)
unmigrated_ids = sorted(list(unmigrated_ids))


print('---- %s unmigrated %ss -----' % (len(unmigrated_ids), entry_type))
print(unmigrated_ids)
print('---- %s archived %ss -------' % (len(archived_ids), entry_type))
print(archived_ids)
print('----------------------------------')