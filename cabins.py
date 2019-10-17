import contentful_management
import helpers as hs
import config as cf

## TODO rewrite and connect to ships

def addCabinGradeContentType():
    cabin_grade_type_attributes = {
        'name': 'Cabin Grade',
        #'displayField': 'title',
        'fields': [
            hs.fieldFactory('Code', 'Symbol', True, False),
            hs.fieldFactory('Title', 'Symbol', True),
            hs.fieldFactory('Short Description', 'Text'),
            hs.fieldFactory('Long Description', 'Text'),
            hs.fieldFactory('Extra Information', 'Text'),
            hs.fieldFactory('Size From', 'Integer', True, False),
            hs.fieldFactory('Size To', 'Integer', True, False),
            hs.fieldFactory('Has Bathroom', 'Boolean', False, False),
            hs.fieldFactory('Has Balcony', 'Boolean', False, False),
            hs.fieldFactory('Has Sofa', 'Boolean', False, False),
            hs.fieldFactory('Has TV', 'Boolean', False, False),
            hs.fieldFactory('Has Dinner Table', 'Boolean', False, False),
            hs.fieldFactory('Is Special', 'Boolean', False, False),
            hs.fieldFactory('Bed Code', 'Symbol', False, False),
            hs.fieldFactory('Bed', 'Symbol', False, False),
            hs.fieldFactory('Window Code', 'Symbol', False, False),
            hs.fieldFactory('Window', 'Symbol', False, False),
        ]
    }

    ctfl_env.content_types().create(
        CABIN_GRADE_FIELD_TYPE_ID,
        cabin_grade_type_attributes
    )
    ctfl_env.content_types().find(CABIN_GRADE_FIELD_TYPE_ID).publish()
    print("Content type %s created and published" % CABIN_GRADE_FIELD_TYPE_ID)

def addCabinCategoryContentType():
    facilities_field = hs.fieldFactory('Facilities', 'Array')
    facilities_field['items'] = {
        'type': 'Symbol'
    }

    cabin_grades_field = hs.fieldFactory('Cabin Grades', 'Array', False, False)
    cabin_grades_field['items'] = {
        'type': 'Link',
        'linkType': 'Entry',
        'validations': [
            {
                'linkContentType': ['cabinGrade']
            }
        ]
    }

    media_field = hs.fieldFactory('Media', 'Array', False, False)
    media_field['items'] = {
        'type': 'Link',
        'linkType': 'Asset'
    }

    cabin_category_type_attributes = {
        'name': 'Cabin Category',
        'fields': [
            hs.fieldFactory('Code', 'Symbol', True, False),
            hs.fieldFactory('Title', 'Symbol', True),
            hs.fieldFactory('Description', 'Text'),
            facilities_field,
            cabin_grades_field,
            media_field
        ]
    }

    ctfl_env.content_types().create(
        CABIN_CATEGORY_FIELD_TYPE_ID,
        cabin_category_type_attributes
    )
    ctfl_env.content_types().find(CABIN_CATEGORY_FIELD_TYPE_ID).publish()
    print("Content type %s created and published" % CABIN_CATEGORY_FIELD_TYPE_ID)

def addCabinContent():
    i = 0
    for cabin_category in data:

        cabin_grade_ids = []
        for cabin_grade in cabin_category['cabinGrades']:

            # add cabin grades
            cabin_grade_attributes = {
                'content_type_id': CABIN_GRADE_FIELD_TYPE_ID,
                'fields': { }
            }
            field_list = ['code', 'title', 'shortDescription', 'longDescription', 'extraInformation', 'sizeFrom', 'sizeTo', 'hasBathroom', 'bedCode', 'bed', 'windowCode', 'window', 'hasBalcony', 'hasSofa', 'hasTv', 'hasDinnerTable', 'isSpecial']
            for field in field_list:
                cabin_grade_attributes['fields'][field] = {
                    'en-US': cabin_grade[field],
                }
            
            id = "cg%d" % i
            ctfl_env.entries().create(
                id,
                cabin_grade_attributes
            )
            ctfl_env.entries().find(id).publish()
            cabin_grade_ids.append(id)
            print("Cabin grade %d added" % i)
            i = i + 1

        # add cabin category
        cabin_grade_links = []
        for cabin_grade_id in cabin_grade_ids:
            cabin_grade_links.append({
                "sys": {
                    "type": "Link",
                    "linkType": "Entry",
                    "id": cabin_grade_id,
                }
            })

        # Add category assets
        media_links = []
        for media_item in cabin_category['media']:
            file_attributes = {
                'fields': {
                    "title": {
                        'en-US': media_item['title']
                    },
                    'file': {
                        'en-US': {
                            'fileName': '%s.jpg' % hs.camelize(media_item['title']),
                            'contentType': 'image/jpg',
                            'upload': media_item['retinaUri']
                        }
                    }
                }
            }
            pic_id = "ccp%d" % i
            ctfl_env.assets().create(
                pic_id,
                file_attributes
            )
            p = ctfl_env.assets().find(pic_id)
            p.process()
            media_links.append({
                "sys": {
                    "type": "Link",
                    "linkType": "Asset",
                    "id": pic_id,
                }
            })

            print("Picture %s added" % pic_id)
            i = i + 1

        cabin_category_attributes = {
            'content_type_id': CABIN_CATEGORY_FIELD_TYPE_ID,
            'fields': {
                'cabinGrades': {
                    'en-US': cabin_grade_links
                },
                'media': {
                    'en-US': media_links
                }
            }
        }
        field_list = ['code', 'title', 'description', 'facilities']
        for field in field_list:
            cabin_category_attributes['fields'][field] = {
                'en-US': cabin_category[field],
            }
        id = "cc%d" % i
        ctfl_env.entries().create(
            id,
            cabin_category_attributes
        )
        ctfl_env.entries().find(id).publish()
        print("Cabin class %d added" % i)
        i = i + 1

########################

CMS_API_URL = "http://api.development.hurtigruten.com:80/api/CmsCabins"
CABIN_GRADE_FIELD_TYPE_ID = "cabinGrade"
CABIN_CATEGORY_FIELD_TYPE_ID = "cabinCategory"

data = hs.readJsonData(CMS_API_URL)
ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)

hs.deleteContentTypeAndAssociatedContent(ctfl_env, CABIN_GRADE_FIELD_TYPE_ID)
addCabinGradeContentType()

hs.deleteContentTypeAndAssociatedContent(ctfl_env, CABIN_CATEGORY_FIELD_TYPE_ID)        
addCabinCategoryContentType()

addCabinContent()