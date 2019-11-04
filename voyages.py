import contentful_management, random, config
import helpers as hs
from urllib.parse import urlparse
from os.path import splitext, basename

CMS_API_URL = "https://www.hurtigruten.com/rest/b2b/voyages"

data = hs.readJsonData(CMS_API_URL)
ctfl_env = hs.createContentfulEnvironment(config.CTFL_SPACE_ID, config.CTFL_ENV_ID, config.CTFL_MGMT_API_KEY)

# this allows running several instances of the script in parallel in order to speed the migration up
random.shuffle(data)

for voyage_from_list in data:

    # these voyages are not migrated because they are being rewritten for B2B
    if voyage_from_list['id'] in [35896, 48549, 48953, 48152, 49082, 48826, 47889,
        47608, 49010, 48797, 48127, 48896, 48395, 36914, 36818, 36957, 36009,
        35950, 50739, 50705, 50671, 50619, 50595, 50526, 58353, 50458, 58330,
        50574, 50548, 50417]:
        print("%s needs to be rewritten, skipping" % voyage_from_list['id'])
        continue

    # if voyage is already added, do not re-import
    try:
        ctfl_env.entries().find(voyage_from_list['id'])
        print("%s already added, skipping" % voyage_from_list['id'])
        continue
    except contentful_management.errors.NotFoundError:
        pass

    # load all fields for the particular voyage by calling GET voyages/{id} 
    voyage = hs.readJsonData("%s/%s" % (CMS_API_URL, voyage_from_list['id']))  

    hs.addEntry(
        environment=ctfl_env,
        id=str(voyage['id']),
        content_type_id="voyage",
        fields=hs.fieldLocalizer('en-US',
        {
            'name': voyage['heading'],
            'id': voyage['id'],
            'description': voyage['intro'],
            'included': hs.convertToContentfulRichText(voyage['includedInfo']),
            'notIncluded': hs.convertToContentfulRichText(voyage['notIncludedInfo']),
            'travelSuggestionCodes': voyage['travelSuggestionCodes'],
            'duration': voyage['durationText'],
            'destinations': [hs.entryLink(voyage['destinationId'])],
            'fromPort': hs.entryLink(voyage['fromPort']),
            'toPort': hs.entryLink(voyage['toPort']),
            'usps': [hs.addEntry(
                environment=ctfl_env,
                id="usp%d-%d" % (voyage['id'], i),
                content_type_id="usp",
                fields=hs.fieldLocalizer('en-US', {'text' : usp})) for i, usp in enumerate(voyage['sellingPoints'])],
            'map': hs.addAsset(
                environment=ctfl_env,
                asset_link=voyage['largeMap']['highResolutionUri'],
                id="voyageMap%d" % voyage['id'],
                title=voyage['largeMap']['alternateText'],
                file_name=voyage['largeMap']['alternateText']),
            'media': [hs.addAsset(
                environment=ctfl_env,
                asset_link=media_item['highResolutionUri'],
                id="voyagePicture%d-%d" % (voyage['id'], i),
                title=media_item['alternateText'],
                file_name='%s%s' % (splitext(basename(urlparse(media_item['highResolutionUri']).path)))) for i, media_item in enumerate(voyage['mediaContent'])],
            'itinerary': [hs.addEntry(
                environment=ctfl_env,
                id="itday%d-%d" % (voyage['id'], i),
                content_type_id="itineraryDay",
                fields=hs.fieldLocalizer('en-US',
                {
                    'day': itinerary_day['day'],
                    'location': itinerary_day['location'],
                    'name': itinerary_day['heading'],
                    'description': hs.convertToContentfulRichText(itinerary_day['body']),
                    'images': [hs.addAsset(
                        environment=ctfl_env,
                        asset_link=media_item['highResolutionUri'],
                        id="itdpic%d-%s-%d" % (voyage['id'], hs.camelize(itinerary_day['day']), i),
                        title=media_item['alternateText'],
                        file_name='%s%s' % (splitext(basename(urlparse(media_item['highResolutionUri']).path))),) for i, media_item in enumerate(itinerary_day['mediaContent'])]
                })) for i, itinerary_day in enumerate(voyage['itinerary'])]
        })
    )
