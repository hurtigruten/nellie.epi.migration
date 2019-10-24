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

    # there is an exception case here
    if voyage_from_list['id'] == 34046:
        continue

    ctfl_voyage = ctfl_env.entries().find(voyage_from_list['id'])
    voyage = hs.readJsonData("%s/%s" % (CMS_API_URL, voyage_from_list['id']))

    ctfl_voyage.fields('en-US')['map'] = hs.addAsset(
        environment=ctfl_env,
        asset_link=voyage['largeMap']['highResolutionUri'],
        id="voyageMap%d" % voyage['id'],
        title=voyage['largeMap']['alternateText'],
        file_name=voyage['largeMap']['alternateText'])

    ctfl_voyage.fields('en-US')['media'] = [hs.addAsset(
        environment=ctfl_env,
        asset_link=media_item['highResolutionUri'],
        id="voyagePicture%d-%d" % (voyage['id'], i),
        title=media_item['alternateText'],
        file_name='%s%s' % (splitext(basename(urlparse(media_item['highResolutionUri']).path)))) for i, media_item in enumerate(voyage['mediaContent'])]

    ctfl_voyage.save()
    ctfl_voyage.publish()
    print("%s updated" % voyage_from_list['id'])

    for i, itinerary_day in enumerate(voyage['itinerary']):
        ctfl_itinerary_day = ctfl_env.entries().find("itday%d-%d" % (voyage['id'], i))
        ctfl_itinerary_day.fields('en-US')['images'] = [hs.addAsset(
            environment=ctfl_env,
            asset_link=media_item['highResolutionUri'],
            id="itdpic%d-%s-%d" % (voyage['id'], hs.camelize(itinerary_day['day']), i),
            title=media_item['alternateText'],
            file_name='%s%s' % (splitext(basename(urlparse(media_item['highResolutionUri']).path)))) for i, media_item in enumerate(itinerary_day['mediaContent'])]
        ctfl_itinerary_day.save()
        ctfl_itinerary_day.publish()
        print("%s updated" % ("itday%d-%d" % (voyage['id'], i)))
