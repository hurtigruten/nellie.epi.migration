import json
import contentful_management
import contentful
import os
from urllib.request import urlopen, Request
from dotenv import load_dotenv
import argparse


def entry_link(entry_id):
    if entry_id is None:
        return None
    return {"sys": {"type": "Link", "linkType": "Entry", "id": str(entry_id)}}


parser = argparse.ArgumentParser(description='Find unmigrated entries')
parser.add_argument('--entry_type', dest='entry_type',
                    help='Valid values: [excursion, program]')
parser.add_argument('--ids', dest='activity_ids',
                    help='List of comma-separated entry ids')

args = parser.parse_args()
entry_type = args.entry_type
activity_ids = [str(id) for id in args.activity_ids.split(',')]

env_vars = load_dotenv()

CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
CONTENTFUL_CDN_KEY = os.getenv('CONTENTFUL_CDN_KEY_GLOBAL_PREVIEW')
CONTENTFUL_CMA_KEY = os.getenv('CONTENTFUL_CMA_KEY')
CONTENTFUL_ENVIRONMENT = os.getenv('CONTENTFUL_ENVIRONMENT')


def get_excursion_ids_for_voyage(voyage_id: float):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Magic ZBrowser'
    }

    base_urls = ['https://www.hurtigruten.com.au/rest/',
                 'https://www.hurtigruten.de/rest/']

    eids = []
    for base in base_urls:
        url = base + entry_type + '/voyages/' + voyage_id + '/' + entry_type + 's'

        req = Request(url, headers=headers)
        res = urlopen(req).read()
        eids.extend([str(id) for id in json.loads(res.decode('utf-8'))])

    return list(set(eids))


print('Relinking activities in env: %s' % CONTENTFUL_ENVIRONMENT)

cma = contentful_management.Client(CONTENTFUL_CMA_KEY)
cma_env = cma.environments(CONTENTFUL_SPACE_ID).find(CONTENTFUL_ENVIRONMENT)
voyageType = cma_env.content_types().find('voyage')

client = contentful.Client(
    CONTENTFUL_SPACE_ID, CONTENTFUL_CDN_KEY, 'preview.contentful.com', environment=CONTENTFUL_ENVIRONMENT)
cf_voyages = client.entries({
    'content_type': 'voyage',
    'select': 'sys.id',
    'limit': 500
}).items

cf_voyage_ids = [voyage.id for voyage in cf_voyages]
voyages_for_activity = {}
for activity_id in activity_ids:
    voyages_for_activity[activity_id] = []

for i, vid in enumerate(cf_voyage_ids):
    try:
        float(vid)
    except ValueError:
        continue

    eids = get_excursion_ids_for_voyage(vid)
    for activity_id in activity_ids:
        if (activity_id in eids):
            voyages_for_activity[activity_id].append(vid)

    print('Retrieved voyage info %s/%s' %
          (i, len(cf_voyage_ids)), end='\r')

# This is marvelously stupid, should turn dict around and map voyage_id -> [activity_ids]
print('Updating activities')
for activity_id, voyage_ids in voyages_for_activity.items():
    for voyage_id in voyage_ids:
        voyage = voyageType.entries().find(voyage_id)
        was_published = voyage.is_published
        activities = voyage.fields('en').get(entry_type + 's')
        if activities is not None and activity_id in [str(activity.id) for activity in activities]:
            continue

        new_activities = ([entry_link(
            activity.id) for activity in activities] if activities is not None else []) + [entry_link(activity_id)]
        voyage._fields['en'][entry_type + 's'] = new_activities
        voyage.save()

        if (was_published):
            try:
                voyage.publish()
            except:
                print('Unable to publish voyage %s' % voyage_id)

    print('Updated activity %s. Affected voyages: %s' %
          (activity_id, ', '.join(voyage_ids)))
