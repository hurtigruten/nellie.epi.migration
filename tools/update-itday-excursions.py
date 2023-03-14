import json
import contentful_management
import contentful
import os
from urllib.request import urlopen, Request
from dotenv import load_dotenv
import time

env_vars = load_dotenv()

CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
CONTENTFUL_CDN_KEY = os.getenv('CONTENTFUL_CDN_KEY_GLOBAL_PREVIEW')
CONTENTFUL_ENVIRONMENT = "master" # os.getenv('CONTENTFUL_ENVIRONMENT')
CONTENTFUL_CMA_KEY = os.getenv('CONTENTFUL_CMA_KEY')


print(f"Updating itday excursions in {CONTENTFUL_ENVIRONMENT}")

# Check if any of the included excursions in EPI have not been migrated to Contentful
def show_unmigrated_excursions(epi_voyages):
    epi_exc_ids = []
    for v in epi_voyages:
        for i in v["itinerary"]:
            epi_exc_ids.extend([str(vv) for vv in i["includedExcursions"]])
            
    epi_exc_ids = set(epi_exc_ids)

    client = contentful.Client(
        CONTENTFUL_SPACE_ID, CONTENTFUL_CDN_KEY, 'preview.contentful.com')
    cf_entries = client.entries({
        'content_type': 'excursion',
        'select': 'sys.id',
        'limit': 1000,
    }).items

    cf_exc_ids = set([cfe.id for cfe in cf_entries])

    epi_only_excs = epi_exc_ids.difference(cf_exc_ids)
    
    print(len(epi_exc_ids))
    print(len(cf_exc_ids))
    print(epi_only_excs)

epi_ids = []

base_urls_by_locale = ["https://global.hurtigruten.com/rest/b2b/voyages",
                       "https://www.hurtigruten.com.au/rest/b2b/voyages",
                       "https://www.hurtigruten.co.uk/rest/b2b/voyages",
                       "https://www.hurtigruten.com/rest/b2b/voyages",
                       "https://www.hurtigruten.de/rest/b2b/voyages"
                       ]

epi_voyages = []
for url in base_urls_by_locale:
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Magic ZBrowser'
    }

    req = Request(url, headers = headers)

    res = urlopen(req).read()
    epi_entries = json.loads(res.decode('utf-8'))

    epi_voyages.extend(epi_entries)
    
evmap = {}
for v in epi_voyages:
    if (v["id"] in evmap):
        continue
    evmap[v["id"]] = v
    
epi_voyages = evmap.values()


client = contentful.Client(
    CONTENTFUL_SPACE_ID, CONTENTFUL_CDN_KEY, 'preview.contentful.com', environment=CONTENTFUL_ENVIRONMENT)

total = client.entries({
    'content_type': 'voyage',
    'limit': 1,
    'select': 'sys.id',
}).total

cf_entries = []
while(len(cf_entries) < total):
    new_cf_entries = client.entries({
        'content_type': 'voyage',
        'select': 'sys.id,fields.itinerary',
        'limit': 50,
        'skip': len(cf_entries),
        'include': 1,
    }).items

    cf_entries.extend(new_cf_entries)
    
print('Retrieved %s voyages from CF' % len(cf_entries))

cma = contentful_management.Client(CONTENTFUL_CMA_KEY)
cma_env = cma.environments(CONTENTFUL_SPACE_ID).find(CONTENTFUL_ENVIRONMENT)
itineraryType = cma_env.content_types().find('itinerary')

def entry_link(entry_id):
    if entry_id is None:
        return None
    return {"sys": {"type": "Link", "linkType": "Entry", "id": str(entry_id)}}

def get_epi_voyage(id):
    # print(f'Attempting to find individual voyage {id}')
    for url in base_urls_by_locale:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Magic ZBrowser'
        }

        req = Request(url + '/' + id, headers = headers)

        res = urlopen(req).read()
        epi_voyage = json.loads(res.decode('utf-8'))

        if (epi_voyage):
            return epi_voyage
        print('Voyage %s not found in EPI' % id)

def update_itinerary(itinerary_id, excursion_ids, wait = 5):
    try:
        exc_links = [entry_link(excursion_id) for excursion_id in excursion_ids]
            
        cma_itinerary = itineraryType.entries().find(itinerary_id)
        cma_itinerary._fields['en']['available_excursions'] = exc_links
        cma_itinerary.save()
        cma_itinerary.publish()
    except:
        print(f'Request timed out, retrying in {wait}s...')
        time.sleep(wait)
        update_itinerary(itinerary_id, excursion_ids, wait + 5)

# Go through all voyages in Contentful
num_voyages = len(cf_entries)
for voyage_idx, cfv in enumerate(cf_entries):
    print('Updating: %s/%s' % (voyage_idx, num_voyages), end="\r")
    # If a corresponding voyage in EPI can't be found, move on
    if (not cfv.id.isdigit()):
        continue
    
    # If voyage misses itinerary
    if (not cfv.fields('en').get('itinerary')):
        print('Voyage missing itinerary: %s' % cfv.id)
        continue
    
    epiv = [v for v in epi_voyages if str(v["id"]) == str(cfv.id)]
    if (len(epiv) == 0):
        epiv = [get_epi_voyage(cfv.id)]
        if not epiv:
            print('WARNING: Could not find voyage in EPI for id ', cfv.id)
            continue
    epiv = epiv[0]
    
    # If the itineraries have different length, they have been manually edited, move on
    if (len(cfv.fields('en').get('itinerary')) != len(epiv["itinerary"])):
        print('WARNING: Itinerary length mismatch for id ', cfv.id)
        continue
    
    # Get excursions per itinerary from EPI
    epi_it_excs = [ei["includedExcursions"] for ei in epiv["itinerary"]]
    
    # Get excursions per itinerary from Contentful
    updated_itinerary = 0
    for it_index, it in enumerate(cfv.fields('en').get('itinerary')):
        
        cf_excursions = [int(e.id) for e in (it.fields('en').get('available_excursions') or [])]
        epi_excursions = epiv["itinerary"][it_index]["includedExcursions"]

        # CF and EPI have same excursions, all good. move on
        if sorted(cf_excursions) == sorted(epi_excursions):
            continue
        
                
        # Update CF with correct excursions
        update_itinerary(it.id, epi_excursions)
        updated_itinerary += 1
        
    voyage_id = cfv.id
    
        

