'''

This script import excursions from Episerver to Contentful if they already are not added
to Contentful. This is checked by Contentful entry ID. For imported excursions it is the
same as entry id in Epi. To update excursions they first need to be deleted from Contentful
and then imported from Episerver by this script.

'''

import contentful_management, random, config
import helpers as hs

CMS_API_URL = "https://www.hurtigruten.com/rest/excursion/excursions"

excursions = hs.readJsonData(CMS_API_URL)
ctfl_env = hs.createContentfulEnvironment(config.CTFL_SPACE_ID, config.CTFL_ENV_ID, config.CTFL_MGMT_API_KEY)

# this allows running several instances of the script in parallel in order to speed the migration up
random.shuffle(excursions)

print(len(excursions))

for excursion in excursions:

    # if excursion is already added, do not re-import
    if hs.isEntryExists(ctfl_env, excursion['id']):
        print("%s already added, skipping" % excursion['id'])
        continue

    difficulty_dict = {
        '1': 'Level 1 - For everyone',
        '2': 'Level 2 - Easy',
        '3': 'Level 3 - Medium',
        '4': 'Level 4 - Hard'
    }
    hs.addEntry(
        environment=ctfl_env,
        id=str(excursion['id']),
        content_type_id="excursion",
        fields=hs.fieldLocalizer('en-US',
        {
            'name': excursion['title'],
            'description': hs.convertToContentfulRichText(excursion['summary']),
            'categories': [category['text'] for category in excursion['activityCategory'] if category['id'] is not "0"],
            'years': [year['id'] for year in excursion['years']],
            'seasons': [season['text'] for season in excursion['seasons']],
            'location': excursion['details'],
            'directions': [direction['text'].split(' ', 1)[0] for direction in excursion['directions']],
            'duration': excursion['durationText'],
            'difficulty': difficulty_dict[excursion['physicalLevel'][0]['id']],
            'price': excursion['priceValue'],
            'bookingCode': excursion['code'],
            'link': excursion['link'],
            'media': [hs.addAsset(
                environment=ctfl_env,
                asset_uri=excursion['image']['imageUrl'],
                id="excp%s" % excursion['id'],
                title=hs.cleanAssetName(excursion['image']['altText']))] if excursion['image'] is not None else []
        })
    )