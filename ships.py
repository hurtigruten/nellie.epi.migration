import contentful_management
import helpers as hs
import config as cf
from urllib.parse import urlparse
from os.path import splitext, basename

CMS_API_URL = "http://api.development.hurtigruten.com:80/api/CmsShips"

ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)
ships = ctfl_env.entries().all(query={"content_type": "ship"})

for ship in ships:

    ## TODO check if ship already exists

    print("Migrating data for ship %s" % ship.code)

    ship_data = hs.readJsonData("%s/%s" % ("https://www.hurtigruten.com/rest/b2b/ships", ship.code))

    full_image_url = "https://www.hurtigruten.com%s" % ship_data['imageUrl']
    ship.images = [hs.addAsset(
        environment=ctfl_env,
        asset_uri=full_image_url,
        id="shippic-%s" % ship.code,
        title=ship.name,
        file_name='%s%s' % (splitext(basename(urlparse(full_image_url).path))))]

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
    
    # add cabin category containers with media and cabin grades
    ship.cabinCategories = [
        hs.addEntry(
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
                    title=media_item['alternateText'],
                    file_name='%s%s' % (splitext(basename(urlparse(media_item['highResolutionUri']).path)))
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
                            'features': [
                                'bathroom' if cabinGrade['hasBathroom'] else None,
                                'balcony' if cabinGrade['hasBalcony'] else None,
                                'sofa' if cabinGrade['hasSofa'] else None,
                                'tv' if cabinGrade['hasTv'] else None,
                                'dinnerTable' if cabinGrade['hasDinnerTable'] else None
                            ],
                            'bed': hs.addEntryWithCodeIfNotExist(ctfl_env, "bed", cabinGrade['bed']),
                            'window': hs.addEntryWithCodeIfNotExist(ctfl_env, "window", cabinGrade['window']),
                            'isSpecial': cabinGrade['isSpecial'],
                            'media': [
                                hs.addAsset(
                                    environment=ctfl_env,
                                    asset_uri=image_url,
                                    id="shCabGr-%s-%s-%i" % (ship.code, cabinGrade['code'], i),
                                    title=ship.name,
                                    file_name='%s%s' % (splitext(basename(urlparse(full_image_url).path)))
                                )
                                for i, image_url in enumerate(cabinGrade['cabinGradeImages'])]                        
                        })
                    )
                    for cabinGrade in cabinCategory['cabinGrades']
                ]
            })
        )
        for cabinCategory in ship_data['cabinCategories']]

    ship.save()
    ship.publish()

    break