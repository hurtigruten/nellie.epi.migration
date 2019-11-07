'''

This script imports ship data from Epi that are not yet added to Contentful.
Only ships that are already in Contentful are updated. The script:
- imports ship picture from Epi server if the picture is not existing already
- migrates all cabin class and grade data if not existing already
- migrates all deck plans if not existing already

Distinction between what is existing and what is not is made by Contentful entry ID. 
Contentful entry ID is the same as entry ID in Epi for imported items.
To re-import entries and assets from Episerver, first delete the particular ship picture,
cabin class container or deck plan form Contentful; then run this script.
Please note that deleting the link between a ship and associated item
e.g. cabin class container will not trigger update.
The class container entry needs to be deleted.

'''

import contentful_management
import helpers as hs
import config as cf
import random
from urllib.parse import urlparse
from os.path import splitext, basename

CMS_API_URL = "http://api.development.hurtigruten.com:80/api/CmsShips"

ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)
ctfl_ships = ctfl_env.entries().all(query={"content_type": "ship"})

# convert to regular array format in order to shuffle
ships = [ctfl_ship for ctfl_ship in ctfl_ships]

# this allows running several instances of the script in parallel in order to speed the migration up
random.shuffle(ships)

for ship in ships:

    print("Migrating data for ship %s" % ship.name)

    ship_data = hs.readJsonData("%s/%s" % ("https://www.hurtigruten.com/rest/b2b/ships", ship.code))

    # add ship image if not already added
    image_id = "shippic-%s" % ship.code
    if hs.isAssetExists(ctfl_env, image_id):
        print("Ship image already added, skipping")
    else:
        full_image_url = "https://www.hurtigruten.com%s" % ship_data['imageUrl']
        ship.images = [hs.addAsset(
            environment=ctfl_env,
            asset_uri=full_image_url,
            id=image_id,
            title=ship.name)]
        ship.save()
        ship.publish()
        print("Ship %s image updated" % ship.name)

    # add cabin categories if not added already
    for cabinCategory in ship_data['cabinCategories']:
        cabinCategoryCode = hs.extractFirstLetters(cabinCategory['title'])
        if not hs.isEntryExists(ctfl_env, cabinCategoryCode):
            hs.addEntry(
                environment=ctfl_env,
                id=cabinCategoryCode,
                content_type_id="cabinCategory",
                fields=hs.fieldLocalizer('en-US',
                {
                    'code': cabinCategoryCode,
                    'name': cabinCategory['title'],
                    'description': hs.convertToContentfulRichText(cabinCategory['description'])
                })
            )
        else:
            print("Skip adding %s cabin category because it is already added" % cabinCategory['title'])
    
    # add cabin category containers with media and cabin grades if not added already
    cabin_category_container_links = []
    is_links_updated = False
    for cabinCategory in ship_data['cabinCategories']:

        cabin_container_id = "cabcatcont-%s-%s" % (ship.code, hs.extractFirstLetters(cabinCategory['title']))
        cabin_category_container_link = {}

        if hs.isEntryExists(ctfl_env, cabin_container_id):
            print("Cabin container %s already added, skipping" % cabin_container_id)
            cabin_category_container_link = hs.entryLink(cabin_container_id)

        else:
            is_links_updated = True
            cabin_category_container_link = hs.addEntry(
                environment=ctfl_env,
                id="cabcatcont-%s-%s" % (ship.code, hs.extractFirstLetters(cabinCategory['title'])),
                content_type_id="cabinCategoryContainer",
                fields=hs.fieldLocalizer('en-US',
                {
                    'category': hs.entryLink(hs.extractFirstLetters(cabinCategory['title'])),
                    'media': [hs.addAsset(
                        environment=ctfl_env,
                        asset_uri=media_item['highResolutionUri'],
                        id="shCabCatPic-%s-%s-%d" % (ship.code, hs.extractFirstLetters(cabinCategory['title']), i),
                        title=media_item['alternateText']
                    ) for i, media_item in enumerate(cabinCategory['media'])],
                    'cabinGrades': [
                        hs.addEntry(
                            environment=ctfl_env,
                            id="cg-%s-%s-%s" % (ship.code, hs.extractFirstLetters(cabinCategory['title']), cabinGrade['code']),
                            content_type_id="cabinGrade",
                            fields = hs.fieldLocalizer('en-US',
                            {
                                'code': cabinGrade['code'],
                                'name': cabinGrade['title'],
                                'shortDescription': hs.convertToContentfulRichText(cabinGrade['shortDescription']),
                                'longDescription': hs.convertToContentfulRichText(cabinGrade['longDescription']),
                                'extraInformation': hs.convertToContentfulRichText(cabinGrade['extraInformation']),
                                'sizeFrom': cabinGrade['sizeFrom'],
                                'sizeTo': cabinGrade['sizeTo'],
                                'features': [x for x in
                                [
                                    'bathroom' if cabinGrade['hasBathroom'] else None,
                                    'balcony' if cabinGrade['hasBalcony'] else None,
                                    'sofa' if cabinGrade['hasSofa'] else None,
                                    'tv' if cabinGrade['hasTv'] else None,
                                    'dinnerTable' if cabinGrade['hasDinnerTable'] else None
                                ] if x is not None],
                                'bed': hs.addEntryWithCodeIfNotExist(ctfl_env, "bed", cabinGrade['bed']),
                                'window': hs.addEntryWithCodeIfNotExist(ctfl_env, "window", cabinGrade['window']),
                                'isSpecial': cabinGrade['isSpecial'],
                                'media': [
                                    hs.addAsset(
                                        environment=ctfl_env,
                                        asset_uri=image_url,
                                        id="shCabGr-%s-%s-%i" % (ship.code, cabinGrade['code'], i),
                                        title=hs.cleanAssetName(splitext(basename(urlparse(image_url).path))[0])
                                    )
                                    for i, image_url in enumerate(cabinGrade['cabinGradeImages'])]                        
                            })
                        )
                        for cabinGrade in cabinCategory['cabinGrades']
                    ]
                })
            )

        cabin_category_container_links.append(cabin_category_container_link)

    if is_links_updated:
        ship.cabinCategories = cabin_category_container_links
        ship.save()
        ship.publish()
        print("Ship %s cabin categories updated" % ship.name)

    # add deckplans if not added already
    deck_plan_links = []
    is_deckplans_updated = False
    for deck in ship_data['decks']:
        deck_number = int(deck['number'])
        deck_plan_id = "dplan-%s-%d" % (ship.code, deck_number)
        if hs.isEntryExists(ctfl_env, deck_plan_id):
            print("Deckplan %s already added, skipping" % deck_plan_id)
            deck_plan_link = hs.entryLink(deck_plan_id)
        else:
            is_deckplans_updated = True
            deck_plan_link = hs.addEntry(
                environment=ctfl_env,
                id=deck_plan_id,
                content_type_id="deckPlan",
                fields = hs.fieldLocalizer('en-US',
                {
                    "deck": deck_number,
                    "plan": hs.addAsset(
                        environment=ctfl_env,
                        asset_uri=deck['deck']['highResolutionUri'],
                        id="deckPic-%s-%d" % (ship.code, deck_number),
                        title=hs.cleanAssetName(deck['deck']['alternateText']))
                })
            )

        deck_plan_links.append(deck_plan_link)


    if is_deckplans_updated:
        ship.deckPlans = deck_plan_links
        ship.save()
        ship.publish()
        print("Ship %s deckplans updated" % ship.name)
