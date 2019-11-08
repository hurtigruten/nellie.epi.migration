import json, contentful_management, requests
from re import split
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from os.path import splitext, basename

def readJsonData(url):
    '''Read JSON data from URL'''
    
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    return json.loads(webpage)

def createContentfulEnvironment(space_id, env_id, cma_key):
    '''Create Contentful environment given space, environment and Content Management API key'''

    ctfl_client = contentful_management.Client(cma_key)
    return ctfl_client.environments(space_id).find(env_id)

def camelize(string):
    pascalized = ''.join(a.capitalize() for a in split('([^a-zA-Z0-9])', string)
       if a.isalnum())
    return pascalized[0].lower() + pascalized[1:]

def extractFirstLetters(string):
    words = string.split()
    letters = [word[0] for word in words]
    return "".join(letters)

def addEntryWithCodeIfNotExist(environment, content_type_id, entry_id):
    '''
    If entry with given entry ID doesn't exist,
    add new one with given content type id and populate field Code with entry id
    '''

    if isEntryExists(environment, entry_id):
        return entryLink(entry_id)
    
    return addEntry(
        environment=environment,
        id=entry_id,
        content_type_id=content_type_id,
        fields=fieldLocalizer('en-US', {
            'code': entry_id
        })
    )

def deleteContentTypeAndAssociatedContent(environment, content_type_id):
    '''Unpublish and delete content type and all content of that type'''

    deleteContentOfType(environment, content_type_id)

    try:
        content_type = environment.content_types().find(content_type_id)
    except contentful_management.errors.NotFoundError:
        return
    
    if content_type.is_published:
        content_type.unpublish()
    environment.content_types().delete(content_type_id)
    print("Content type %s and assocated content deleted" % content_type_id)

def deleteContentOfType(environment, content_type_id):
    '''Delete all content of particular type'''

    entries = environment.entries().all(query={
        "content_type": content_type_id
    })
    for entry in entries:
        deleteEntryIfExists(environment, entry.sys['id'])

def deleteEntryIfExists(environment, entry_id):
    '''Unpublish and delete entry with given id'''

    try:
        entry = environment.entries().find(entry_id)
        if entry.is_published:
            entry.unpublish()
        environment.entries().delete(entry.sys['id'])
        print("Entry %s deleted" % entry.sys['id'])
    except contentful_management.errors.NotFoundError:
        return

def deleteAssetIfExists(environment, asset_id):
    '''Unpublish and delete asset with given id'''

    try:
        asset = environment.assets().find(asset_id)
        if asset.is_published:
            asset.unpublish()
        environment.assets().delete(asset_id)
        print("Asset %s deleted" % asset_id)
    except contentful_management.errors.NotFoundError:
        return

def isEntryExists(environment, entry_id):
    try:
        environment.entries().find(entry_id)
        return True
    except contentful_management.errors.NotFoundError:
        return False

def isAssetExists(environment, asset_id):
    try:
        environment.assets().find(asset_id)
        return True
    except contentful_management.errors.NotFoundError:
        return False

def convertToContentfulRichText(html_content):
    '''Convert HTML content to Contentful Rich text format by using https://bitbucket.org/hurtigruteninternal/html-to-rich-text (need to run locally)'''

    if html_content is None:
        return None

    html_content = html_content.replace('\n', '').replace('\r', '')

    req = Request("http://localhost:3000/convert")
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps({'from': 'html', 'to': 'richtext', 'html': html_content})
    jsondataasbytes = jsondata.encode('utf-8')
    req.add_header('Content-Length', len(jsondataasbytes))
    response = urlopen(req, jsondataasbytes).read()
    return json.loads(response)

def cleanAssetName(name):
    '''Replace image extension with spaces and strip in order to create asset name'''

    return name.replace('.jpeg', ' ').replace('.jpg', ' ').replace('.png', ' ').replace('_', ' ').replace('-', ' ').replace('.JPG', ' ').replace('.JPEG', ' ').replace('.PNG', ' ').strip()

def addAsset(**kwargs):
    '''Add or override asset with given id, then initialize processing

    environment :
        Contentful environment

    id :
        Asset id

    asset_uri :
        Asset URI

    title :
        Asset title
        
    Returns :
        Link to asset'''

    id = kwargs['id'].replace("/","")

    print("Adding %a" % id)

    # if asset with the same id already added, delete it
    deleteAssetIfExists(kwargs['environment'], id)

    # get asset base URI
    image_url = kwargs['asset_uri'].split('?')[0]
    if not image_url.startswith("http"):
        if image_url.startswith("/globalassets"):
            image_url = "https://www.hurtigruten.com" + image_url
        if image_url.startswith("//www.hurtigruten.com"):
            image_url = "https:" + image_url


    # search for assets with the same exact size and link to existing image if byte content is exactly the same
    image_fetch_succ = False
    while not image_fetch_succ:
        try:
            asset_type, asset_size = getAssetTypeAndSize(image_url)
            image_fetch_succ = True
        except requests.exceptions.MissingSchema:
            # sometimes Epi provides corrupt URLs that can be fixed manually
            if input("Cannot retrieve asset. Would you like to manually override the URL: %s (y/n) " % image_url) == 'y':
                image_url = input("Image URL: ")
            else:
                return None
    
    assets = kwargs['environment'].assets().all(query={
        'fields.file.details.size': asset_size
    })
    for asset in assets:
        resp = requests.get(image_url, stream=True)
        image_bytes = resp.content
        resp.close()

        resp = requests.get("http:" + asset.fields()['file']['url'], stream=True)
        ctfl_image_bytes = resp.content
        resp.close()

        if image_bytes == ctfl_image_bytes:
            print("Linking to existing asset %s" % asset.sys['id'])
            return assetLink(asset.sys['id'])

    asset_attributes = {
        'fields': {
            "title": {
                'en-US': cleanAssetName(kwargs['title'])
            },
            'file': {
                'en-US': {
                    'fileName': '%s%s' % splitext(basename(urlparse(image_url).path)),
                    'upload': image_url,
                    'contentType': asset_type
                }
            }
        }
    }

    kwargs['environment'].assets().create(id, asset_attributes)
    p = kwargs['environment'].assets().find(id)

    p.process()
    print("Asset %s added" % id)

    return assetLink(id)

def getAssetTypeAndSize(uri):
    '''Return asset type and size if possible to read by image URI, otherwise return 0'''

    resp = requests.get(uri, stream=True)

    img_to_add_content_type = resp.headers['Content-type']
    if 'content-length' in resp.headers:
        return (img_to_add_content_type, resp.headers['Content-length'])
    else:
        return (img_to_add_content_type, 0)
    resp.close()

def addEntry(**kwargs):
    '''Add or override entry with given id

    environment :
        Contentful environment

    id :
        Entry id

    content_type_id :
        Content type id in Contentful

    fields :
        Entry fields

    Returns :
        Link to entry'''

    id = kwargs['id'].replace("/","")

    # if entry with the same id already added, delete it
    deleteEntryIfExists(kwargs['environment'], id)

    entry_attributes = {
        'content_type_id': kwargs['content_type_id'],
        'fields': kwargs['fields']
    }
    kwargs['environment'].entries().create(id, entry_attributes)
    kwargs['environment'].entries().find(id).publish()
    print("Entry %s added" % id)
    return entryLink(id)

def fieldLocalizer(locale, field_dict):
    '''Localize field dictionary for a given locale'''

    d = {}
    for key, value in field_dict.items():
        d[key] = {
            locale: value
        }
    return d

def entryLink(entry_id):
    '''Return link to entry by given entry id'''

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
    '''Return link to asset with given asset id'''

    if asset_id is None:
        return None

    return {
        "sys": {
            "type": "Link",
            "linkType": "Asset",
            "id": asset_id,
        }
    }

def intfromStringOrNoneifNone(string):
    '''Returns int from string if string value is not None; otherwise returns None'''
    
    if string:
        return int(string)

    return None
