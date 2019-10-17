import contentful_management, random
import helpers as hs
import config as cf
from urllib.parse import urlparse
from os.path import splitext, basename


CMS_API_URL = "https://www.hurtigruten.com/rest/b2b/voyages"

data = hs.readJsonData(CMS_API_URL)
ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)

voyages_to_rewrite = [35896, 48549, 48953, 48152, 49082, 48826, 47889,
    47608, 49010, 48797, 48127, 48896, 48395, 36914, 36818, 36957, 36009,
    35950, 50739, 50705, 50671, 50619, 50595, 50526, 58353, 50458, 58330,
    50574, 50548, 50417]

# to allow more efficient multitasking with parallel workers
random.shuffle(data)

for voyage_from_list in data:
    
    notFound = False
    try:
        ctfl_env.entries().find(voyage_from_list['id'])
    except contentful_management.errors.NotFoundError:
        notFound = True

    if notFound == False:
        print("%s already added, skipping update" % voyage_from_list['id'])
        continue

    voyage = hs.readJsonData("%s/%s" % (CMS_API_URL, voyage_from_list['id']))
    needs_rewriting = voyage['id'] in voyages_to_rewrite

    hs.addEntry(
        environment=ctfl_env,
        id=str(voyage['id']),
        content_type_id="voyage",
        fields=hs.fieldLocalizer('en-US',
        {
            'name': "[TODO rewrite] " + voyage['heading'] if needs_rewriting else voyage['heading'],
            'id': voyage['id'],
            'description': "TODO" if needs_rewriting else voyage['intro'],
            'included': hs.convertToContentfulRichText("TODO" if needs_rewriting else voyage['includedInfo']),
            'notIncluded': hs.convertToContentfulRichText("TODO" if needs_rewriting else voyage['notIncludedInfo']),
            'travelSuggestionCodes': voyage['travelSuggestionCodes'],
            'duration': voyage['durationText'],
            'destinations': [hs.entryLink(voyage['destinationId'])],
            'fromPort': hs.entryLink(voyage['fromPort']),
            'toPort': hs.entryLink(voyage['toPort']),
            'usps': None if needs_rewriting else [hs.addEntry(
                environment=ctfl_env,
                id="usp%d-%d" % (voyage['id'], i),
                content_type_id="usp",
                fields=hs.fieldLocalizer('en-US', {'text' : usp})) for i, usp in enumerate(voyage['sellingPoints'])],
            'map': hs.addAsset(
                environment=ctfl_env,
                asset_link=voyage['largeMap']['highResolutionUri'],
                id="voyageMap%d" % voyage['id'],
                title=voyage['largeMap']['alternateText'],
                file_name=voyage['largeMap']['alternateText'],
                content_type='image/svg+xml',
                check_duplicates=False),
            'media': [hs.addAsset(
                environment=ctfl_env,
                asset_link=media_item['highResolutionUri'],
                id="voyagePicture%d-%d" % (voyage['id'], i),
                title=media_item['alternateText'],
                file_name='%s.%s' % (splitext(basename(urlparse(media_item['highResolutionUri']).path))),
                content_type='image/jpg') for i, media_item in enumerate(voyage['mediaContent'])],
            'itinerary': [hs.addEntry(
                environment=ctfl_env,
                id="itday%d-%d" % (voyage['id'], i),
                content_type_id="itineraryDay",
                fields=hs.fieldLocalizer('en-US',
                {
                    'day': "[TODO rewrite] " + itinerary_day['day'] if needs_rewriting else itinerary_day['day'],
                    'location': itinerary_day['location'],
                    'name': "TODO" if needs_rewriting else itinerary_day['heading'],
                    'description': hs.convertToContentfulRichText("TODO" if needs_rewriting else itinerary_day['body']),
                    'images': [hs.addAsset(
                        environment=ctfl_env,
                        asset_link=media_item['highResolutionUri'],
                        id="itdpic%d-%s-%d" % (voyage['id'], hs.camelize(itinerary_day['day']), i),
                        title=media_item['alternateText'],
                        file_name='%s%s' % (splitext(basename(urlparse(media_item['highResolutionUri']).path))),
                        content_type='image/jpg') for i, media_item in enumerate(itinerary_day['mediaContent'])]
                })) for i, itinerary_day in enumerate(voyage['itinerary'])]
        })
    )
