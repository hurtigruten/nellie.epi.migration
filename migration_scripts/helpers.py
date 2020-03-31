import argparse
import json
import contentful_management
import requests
import logging
import os
import config
from re import split
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from os.path import splitext, basename
from datetime import datetime
from werkzeug.routing import BaseConverter

logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')


def read_json_data(url):
    """Read JSON data from URL"""

    req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
    response = urlopen(req).read()
    return json.loads(response)


def create_contentful_environment(space_id, env_id, cma_key):
    """Create Contentful environment given space, environment and Content Management API key"""
    client = contentful_management.Client(cma_key)
    client.default_locale = config.DEFAULT_LOCALE
    return client.environments(space_id).find(env_id)


def camelize(string):
    pascalized = ''.join(a.capitalize() for a in split('([^a-zA-Z0-9])', string) if (a.isascii()) and a.isalnum())
    return pascalized[0].lower() + pascalized[1:]


def extract_first_letters(string):
    words = string.split()
    letters = [word[0] for word in words]
    return "".join(letters)


def get_entry(environment, entry_id):
    try:
        entry = environment.entries().find(entry_id)
        return entry
    except contentful_management.errors.NotFoundError as e:
        logging.info('Entry not found: %s' % entry_id)
        return e
    except Exception as e:
        logging.error('Exception occurred while finding entry with ID: %s, error: %s ' % (entry_id, e))
        return e


def add_entry_with_code_if_not_exist(environment, content_type_id, entry_id):
    """
    If entry with given entry ID doesn't exist,
    add new one with given content type id and populate field Code with entry id
    """

    if is_entry_exists(environment, entry_id):
        return entry_link(entry_id)

    return add_entry(
        environment = environment,
        id = entry_id,
        content_type_id = content_type_id,
        fields = field_localizer(config.DEFAULT_LOCALE, {
            'code': entry_id
        })
    )


def delete_content_type_and_associated_content(environment, content_type_id):
    """Unpublish and delete content type and all content of that type"""

    delete_content_of_type(environment, content_type_id)

    try:
        content_type = environment.content_types().find(content_type_id)
    except contentful_management.errors.NotFoundError:
        return
    except Exception as e:
        logging.error(e)
        return e

    if content_type.is_published:
        content_type.unpublish()

    environment.content_types().delete(content_type_id)

    logging.info('Content type %s and associated content deleted' % content_type_id)


def delete_content_of_type(environment, content_type_id):
    """Delete all content of particular type"""

    entries = environment.entries().all(query = {
        "content_type": content_type_id
    })
    for entry in entries:
        delete_entry_if_exists(environment, entry.sys['id'])


def delete_entry_if_exists(environment, entry_id):
    """Unpublish and delete entry with given id"""

    try:
        entry = environment.entries().find(entry_id)
        logging.info("Entry exists: %s" % entry_id)
        if entry.is_published:
            entry.unpublish()
        environment.entries().delete(entry_id)
        logging.info("Entry deleted: %s" % entry_id)
    except contentful_management.errors.NotFoundError:
        logging.info("Entry not found: %s, can't be deleted" % entry_id)
        return
    except Exception as e:
        logging.error('Exception occurred while deleting entry with ID: %s, error: %s ' % (entry_id, e))
        return e


def delete_asset_if_exists(environment, asset_id):
    """Unpublish and delete asset with given id"""

    try:
        asset = environment.assets().find(asset_id)
        logging.info('Asset exists: %s' % asset_id)
        if asset.is_published:
            asset.unpublish()
        environment.assets().delete(asset_id)
        logging.info('Asset deleted: %s' % asset_id)
    except contentful_management.errors.NotFoundError:
        logging.info("Asset not found: %s, can't be deleted" % asset_id)
        return
    except Exception as e:
        logging.error('Exception occurred while deleting asset with ID: %s, error: %s ' % (asset_id, e))
        return e


def is_entry_exists(environment, entry_id):
    try:
        environment.entries().find(entry_id)
        return True
    except contentful_management.errors.NotFoundError:
        return False
    except Exception as e:
        logging.error('Exception occurred while finding entry with ID: %s, error: %s ' % (entry_id, e))
        return e


def is_asset_exists(environment, asset_id):
    try:
        environment.assets().find(asset_id)
        return True
    except contentful_management.errors.NotFoundError:
        return False
    except Exception as e:
        logging.error('Exception occurred while finding asset with ID: %s, error: %s ' % (asset_id, e))
        return e


def convert_to_contentful_rich_text(html_content):
    """
    Convert HTML content to Contentful Rich text format by using
    https://bitbucket.org/hurtigruteninternal/html-to-rich-text (need to run locally)
    """

    if html_content is None:
        return None

    html_content = html_content.replace('\n', '').replace('\r', '')

    req = Request("%s/convert" % os.environ['SYNC_RICH_TEXT_CONVERTER_URL'])
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    json_data = json.dumps({'from': 'html', 'to': 'richtext', 'html': html_content})
    json_data_as_bytes = json_data.encode('utf-8')
    req.add_header('Content-Length', str(len(json_data_as_bytes)))
    response = urlopen(req, json_data_as_bytes).read()
    return json.loads(response)


def clean_asset_name(name, asset_id):
    """Replace image extension with spaces and strip in order to create asset name"""

    logging.info('Asset name: %s, ID: %s' % (name, asset_id))

    return name \
        .replace('.jpeg', ' ') \
        .replace('.jpg', ' ') \
        .replace('.png', ' ') \
        .replace('_', ' ') \
        .replace('-', ' ') \
        .replace('.JPG', ' ') \
        .replace('.JPEG', ' ') \
        .replace('.PNG', ' ') \
        .replace('.svg', ' ') \
        .replace('.SVG', ' ') \
        .strip() if name is not None else name


def add_asset(**kwargs):
    """
    Add or override asset with given id, then initialize processing

    environment :
        Contentful environment

    id :
        Asset id

    asset_uri :
        Asset URI

    title :
        Asset title

    Returns :
        Link to asset
    """

    # get asset base URI
    image_url = kwargs['asset_uri'].split('?')[0]
    if not image_url.startswith("http"):
        if image_url.startswith("/globalassets"):
            image_url = "https://www.hurtigruten.com" + image_url
        if image_url.startswith("//www.hurtigruten.com"):
            image_url = "https:" + image_url

    id = kwargs['id'].replace("/", "")

    # check if asset exists
    # 1. checking if the asset ID is the same

    svgAsset = image_url.endswith(".svg")

    if svgAsset:
        delete_asset_if_exists(kwargs['environment'], id)

    if is_asset_exists(kwargs['environment'], id) and not svgAsset:
        # logging.info('Asset exists, skip asset ID: %s' % id)
        logging.info('Asset exists ID: %s, checking file size' % id)

        image_bytes = 0
        try:
            image_bytes = get_asset_size(image_url)
        except Exception as e:
            logging.error('Could not retrieve image with url: %s, error: %s' % (image_url, e))

        logging.info('Epi image size: %s' % image_bytes)

        asset_fields = kwargs['environment'].assets().find(id).fields()

        asset_file = None
        try:
            asset_file = asset_fields['file']
        except Exception as e:
            logging.error('Asset file is not available: %s' % e)

        asset_url = None
        try:
            asset_url = asset_file['url']
        except Exception as e:
            logging.error('Asset url is not available: %s' % e)

        contentful_image_bytes = 0

        if asset_file is not None and asset_url is not None:
            resp = requests.get("http:" + asset_url, stream = True)
            contentful_image_bytes = resp.headers['Content-length']
            resp.close()
        else:
            logging.error('Could not determine asset url')

        logging.info('Contentful image size: %s' % contentful_image_bytes)

        # 2. has the same asset ID -> check the file size as well
        if image_bytes == contentful_image_bytes:
            logging.info('Asset id and size are the same')
            return asset_link(id)
        else:
            logging.info('Asset size is different')
            id = id + datetime.now().strftime('%Y%m%d.%H%M%S.%f')

    # 3. the image with a different file size might be already in contentful, so we have to reuse that one

    # search for assets with the same exact size and link to existing image if byte content is exactly the same
    image_fetch_success = False
    while not image_fetch_success:
        try:
            asset_type, asset_size = get_asset_type_and_size(image_url)
            image_fetch_success = True
        except requests.exceptions.MissingSchema:
            # sometimes Epi provides corrupt URLs that can be fixed manually
            if input(
                    "Cannot retrieve asset. Would you like to manually override the URL: %s (y/n) " % image_url) == 'y':
                image_url = input("Image URL: ")
            else:
                return None
        except Exception as e:
            logging.error('Exception occurred while fetching image for asset with ID: %s, error: %s ' % (id, e))
            return e

    assets = kwargs['environment'].assets().all(query = {'fields.file.details.size': asset_size})

    for asset in assets:
        resp = requests.get(image_url, stream = True)
        image_bytes = resp.content
        resp.close()

        asset_file = None
        try:
            asset_file = asset.fields()['file']
        except Exception as e:
            logging.error('Asset file is not available: %s' % e)

        asset_url = None
        try:
            asset_url = asset_file['url']
        except Exception as e:
            logging.error('Asset url is not available: %s' % e)

        contentful_image_bytes = 0
        if asset_file is not None and asset_url is not None:
            resp = requests.get("http:" + asset_url, stream = True)
            contentful_image_bytes = resp.content
            resp.close()
        else:
            logging.error('Could not determine asset url')

        if image_bytes == contentful_image_bytes:
            logging.info('%s matches size to existing asset: %s' % (id, asset.sys['id']))
            if is_asset_exists(kwargs['environment'], asset.sys['id']):
                logging.info('Linking %s to existing asset: %s' % (id, asset.sys['id']))
                return asset_link(asset.sys['id'])

    name = '%s%s' % splitext(basename(urlparse(image_url).path))
    asset_attributes = {
        'fields': {
            "title": {
                config.DEFAULT_LOCALE: clean_asset_name(name, id)
            },
            'file': {
                config.DEFAULT_LOCALE: {
                    'fileName': '%s%s' % splitext(basename(urlparse(image_url).path)),
                    'upload': image_url,
                    'contentType': asset_type
                }
            }
        }
    }

    try:
        kwargs['environment'].assets().create(id, asset_attributes)
    except Exception as e:
        logging.error('Exception occurred while creating asset with ID: %s, error: %s' % (id, e))
        return e

    try:
        asset = kwargs['environment'].assets().find(id)
    except Exception as e:
        logging.error('Exception occurred while finding asset with ID: %s, error: %s' % (id, e))
        return e

    try:
        asset.process()
    except Exception as e:
        logging.error('Exception occurred while processing asset with ID: %s, error: %s' % (id, e))
        return e

    logging.info('Asset added: %s' % id)

    return asset_link(id)


def get_asset_size(uri):
    """Return asset size if possible to read by image URI, otherwise return 0"""

    resp = requests.get(uri, stream = True)

    img_to_add_content_type = resp.headers['Content-type']
    if 'content-length' in resp.headers:
        return resp.headers['Content-length']
    else:
        return 0
    resp.close()


def get_asset_type_and_size(uri):
    """Return asset type and size if possible to read by image URI, otherwise return 0"""

    resp = requests.get(uri, stream = True)

    img_to_add_content_type = resp.headers['Content-type']
    if 'content-length' in resp.headers:
        return img_to_add_content_type, resp.headers['Content-length']
    else:
        return img_to_add_content_type, 0
    resp.close()


def add_entry(**kwargs):
    """
    Add or override entry with given id

    environment :
        Contentful environment

    id :
        Entry id

    content_type_id :
        Content type id in Contentful

    fields :
        Entry fields

    Returns :
        Link to entry
    """

    id = kwargs['id'].replace("/", "")

    # old_entry = kwargs['environment'].entries().find(id)

    # if old_entry:
    #     logging.info('Comparing entries with id: %s' % id)
    #     if compare_entry(kwargs['fields'], old_entry._fields):
    #         logging.info('Entries are the same')
    #         return entry_link(id)

    # if entry with the same id already added, delete it
    delete_entry_if_exists(kwargs['environment'], id)

    entry_attributes = {
        'content_type_id': kwargs['content_type_id'],
        'fields': kwargs['fields']
    }

    try:
        kwargs['environment'].entries().create(id, entry_attributes)
    except Exception as e:
        logging.error('Exception occurred while creating entry with ID: %s, error: %s' % (id, e))
        return e

    try:
        kwargs['environment'].entries().find(id).publish()
    except Exception as e:
        logging.error('Exception occurred while publishing entry with ID: %s, error: %s' % (id, e))
        return e

    logging.info('Entry added: %s' % id)
    return entry_link(id)


def field_localizer(locale, field_dict):
    """Localize field dictionary for a given locale"""

    d = {}
    for key, value in field_dict.items():
        d[key] = {
            locale: value
        }
    return d


def merge_localized_dictionaries(*args):
    merged = {}
    for localized_dicts in args:
        for field_name, locale_pair in localized_dicts.items():
            if field_name in merged:
                existing_locale_dict = merged[field_name].copy()
                new_locale_dict = {**locale_pair, **existing_locale_dict}
                merged[field_name] = new_locale_dict
            else:
                merged[field_name] = locale_pair
    return merged


def entry_link(entry_id):
    """Return link to entry by given entry id"""

    if entry_id is None:
        return None

    return {
        "sys": {
            "type": "Link",
            "linkType": "Entry",
            "id": str(entry_id)
        }
    }


def asset_link(asset_id):
    """Return link to asset with given asset id"""

    if asset_id is None:
        return None

    return {
        "sys": {
            "type": "Link",
            "linkType": "Asset",
            "id": asset_id,
        }
    }


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join(BaseConverter.to_url(value)
                        for value in values)


class IntListConverter(BaseConverter):
    regex = r'\d+(?:,\d+)*,?'

    def to_python(self, value):
        return [int(x) for x in value.split(',')]

    def to_url(self, value):
        return ','.join(str(x) for x in value)

# def compare_entry(new_fields, old_fields):
#     """Compares the old and new fields in contentful"""

#     result = True
#     for key in old_fields:
#         newKeys = key.split('_')
#         newKey = '%s%s' % (newKeys[0], newKeys[1].title())
#         if new_fields[newKey]["en-US"] is None:
#             continue
#         if isinstance(new_fields[newKey]["en-US"], dict):
#             if "nodeType" in new_fields[newKey]["en-US"]:
#                 continue
#         if new_fields[newKey]["en-US"] != old_fields['en-US'][key]:
#             result = False

#     return result
