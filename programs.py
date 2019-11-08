'''

This script imports pre & post programs from Episerver to Contentful if they already are not added
to Contentful. This is checked by Contentful entry ID. For imported pre & post programs it is the
same as entry id in Epi. To update pre & post programs they first need to be deleted from Contentful
and then imported from Episerver by this script. When adding a pre or post program, entries and assets
that has been previously linked to the old imported pre or post program and thus have the same id are
deleted and re-imported.

'''

import contentful_management, random, config
import helpers as hs

CMS_API_URL = "http://us.staging.hurtigruten.com/rest/b2b/programs"

data = hs.readJsonData(CMS_API_URL)
ctfl_env = hs.createContentfulEnvironment(config.CTFL_SPACE_ID, config.CTFL_ENV_ID, config.CTFL_MGMT_API_KEY)

# this allows running several instances of the script in parallel in order to speed the migration up
random.shuffle(data)

for program in data:

    # if program is already added, do not re-import
    if hs.isEntryExists(ctfl_env, program['id']):
        print("%s already added, skipping" % program['id'])
        continue

    hs.addEntry(
        environment=ctfl_env,
        id=str(program['id']),
        content_type_id="program",
        fields=hs.fieldLocalizer('en-US',
        {
            'name': program['heading'],
            'shortDescription': program['intro'],
            'description': hs.convertToContentfulRichText(program['body']),
            'minNumberOfGuests': program['minimumNumberOfGuests'], # this is not an integer because there are values like "8 (18/19) 4 (19/20)" there
            'maxNumberOfGuests': program['maximumNumberOfGuests'],
            'usps': [hs.addEntry(
                environment=ctfl_env,
                id="usp%d-%d" % (program['id'], i),
                content_type_id="usp",
                fields=hs.fieldLocalizer('en-US', {'text' : usp})) for i, usp in enumerate(program['sellingPoints']) if usp is not None],
            'media': [hs.addAsset(
                environment=ctfl_env,
                asset_uri=media_item['highResolutionUri'],
                id="programPicture%d-%d" % (program['id'], i),
                title=media_item['alternateText']) for i, media_item in enumerate(program['mediaContent'])]
        })
    )
