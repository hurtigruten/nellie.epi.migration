import json, contentful_management
from urllib.request import Request, urlopen
from re import split


from urllib.request import Request, urlopen
import json

def readJsonData(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    return json.loads(webpage)

def createContentfulEnvironment(space_id, env_id, cma_key):
    ctfl_client = contentful_management.Client(cma_key)
    return ctfl_client.environments(space_id).find(env_id)

def camelize(string):
    pascalized = ''.join(a.capitalize() for a in split('([^a-zA-Z0-9])', string)
       if a.isalnum())
    return pascalized[0].lower() + pascalized[1:]

def fieldFactory(name, type_name, required=False, localized=True):
    return {
        'disabled': False,
        'id': camelize(name),
        'localized': localized,
        'name': name,
        'omitted': False,
        'required': required,
        'type': type_name,
    }

def deleteContentTypeAndAssociatedContent(environment, content_type_id):
    deleteContentOfType(environment, content_type_id)

    try:
        content_type = environment.content_types().find(content_type_id)
    except contentful_management.errors.NotFoundError:
        return
    
    if content_type.is_published:
        content_type.unpublish()
    environment.content_types().delete(content_type_id)
    print("Content type %s deleted" % content_type_id)

def deleteContentOfType(environment, content_type_id):
    entries = environment.entries().all(query={
        "sys.contentType": content_type_id
    })
    for entry in entries:
        deleteEntryIfExists(environment, entry.sys['id'])

def deleteEntryIfExists(environment, entry_id):
    try:
        entry = environment.entries().find(entry_id)
        if entry.is_published:
            entry.unpublish()
        environment.entries().delete(entry.sys['id'])
        print("Entry %s deleted" % entry.sys['id'])
    except contentful_management.errors.NotFoundError:
        return

def deleteAssetIfExists(environment, asset_id):
    try:
        asset = environment.assets().find(asset_id)
        if asset.is_published:
            asset.unpublish()
        environment.assets().delete(asset_id)
        print("Asset %s deleted" % asset_id)
    except contentful_management.errors.NotFoundError:
        return

def convertToContentfulRichText(markdown_content):

    if markdown_content is None:
        return None

    return {
        "data": {},
        "content": [
            {
            "data": {},
            "content": [
                {
                "data": {},
                "marks": [],
                "value": markdown_content,
                "nodeType": "text"
                }
            ],
            "nodeType": "paragraph"
            }
        ],
        "nodeType": "document"
    }

def cleanAssetName(name):
    return name.replace('.jpeg', ' ').replace('.jpg', ' ').replace('.png', ' ').replace('_', ' ').replace('-', ' ').replace('.JPG', ' ').replace('.JPEG', ' ').replace('.PNG', ' ').strip()

def addAsset(**kwargs):
    deleteAssetIfExists(kwargs['environment'], kwargs['id'])

    assets = kwargs['environment'].assets().all(query={
        'fields.title': cleanAssetName(kwargs['title'])
    })

    for asset in assets:
        if asset.fields()['file']['fileName'] == kwargs['file_name']:
            print("Linking to existing asset %s" % asset.sys['id'])
            return assetLink(asset.sys['id'])

    asset_attributes = {
        'fields': {
            "title": {
                'en-US': cleanAssetName(kwargs['title'])
            },
            'file': {
                'en-US': {
                    'fileName': kwargs['file_name'],
                    'contentType': kwargs['content_type'],
                    'upload': kwargs['asset_link']
                }
            }
        }
    }

    kwargs['environment'].assets().create(
        kwargs['id'],
        asset_attributes
    )
    p = kwargs['environment'].assets().find(kwargs['id'])
    p.process()
    print("Asset %s added" % kwargs['id'])

    return assetLink(kwargs['id'])

def addEntry(**kwargs):
    deleteEntryIfExists(kwargs['environment'], kwargs['id'])

    entry_attributes = {
        'content_type_id': kwargs['content_type_id'],
        'fields': kwargs['fields']
    }
    kwargs['environment'].entries().create(
        kwargs['id'],
        entry_attributes
    )
    kwargs['environment'].entries().find(kwargs['id']).publish()
    print("Entry %s added" % kwargs['id'])
    return entryLink(kwargs['id'])

def fieldLocalizer(locale, field_dict):
    d = {}
    for key, value in field_dict.items():
        d[key] = {
            locale: value
        }
    return d

def entryLink(entry_id):

    if entry_id is None:
        return None

    return {
        "sys": {
            "type": "Link",
            "linkType": "Entry",
            "id": str(entry_id)
        }
    }

def assetLink(asset_id):

    if asset_id is None:
        return None

    return {
        "sys": {
            "type": "Link",
            "linkType": "Asset",
            "id": asset_id,
        }
    }
