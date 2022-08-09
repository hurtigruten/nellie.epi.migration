import json
import contentful_management
import contentful
import os
import sys
import requests
from urllib.request import urlopen, Request
from dotenv import load_dotenv
from PIL import Image
import pathlib
from urllib.parse import urlparse
from os.path import splitext, basename
import pickle

IMAGE_DIR = str(pathlib.Path(__file__).parent.resolve()) + \
    '/imgs/'


def clean_asset_name(name, asset_id):
    return (
        name.replace(".jpeg", " ")
        .replace(".jpg", " ")
        .replace(".png", " ")
        .replace("_", " ")
        .replace("-", " ")
        .replace(".JPG", " ")
        .replace(".JPEG", " ")
        .replace(".PNG", " ")
        .replace(".svg", " ")
        .replace(".SVG", " ")
        .strip()
        if name is not None
        else name
    )


def add_protocol(url):
    if (url.startswith('//')):
        return 'https:' + url
    return url


def get_asset_url(asset):
    url = asset.fields('en').get('file').get('url').split('?')[0]
    return add_protocol(url)


def get_asset_type(asset):
    url = get_asset_url(asset)
    return requests.get(url, stream=True).headers['Content-type']


def is_resizable(asset):
    types_to_skip = ['video/quicktime', 'video/mp4']
    asset_type = get_asset_type(asset)
    if (asset_type.lower() in types_to_skip):
        return False
    return True


def save_asset_to_disk(asset_url):
    response = requests.get(asset_url)
    img_path = IMAGE_DIR + asset_url.split('/')[-1]
    with open(img_path, 'wb') as outfile:
        outfile.write(response.content)

    return img_path


def create_asset(asset_name, uploaded_img_id, asset_id, asset_type):
    asset_attributes = {
        "fields": {
            "title": {'en': clean_asset_name(asset_name, asset_id)},
            "file": {
                'en': {
                    "fileName": asset_name,
                    "uploadFrom": {
                        "sys": {
                            "type": "Link",
                            "linkType": "Upload",
                            "id": uploaded_img_id
                        }
                    },
                    "contentType": asset_type,
                }
            },
        }
    }

    cma_env.assets().create(asset.id, asset_attributes)
    new_asset = cma_env.assets().find(asset.id)
    new_asset.process()

    return new_asset


def resize(asset):
    url = get_asset_url(asset)
    asset_type = get_asset_type(asset)

    if (not is_resizable(url)):
        print('Skipping type: ', asset_type)
        return

    raw_img_path = save_asset_to_disk(url)

    optimized_img_path = IMAGE_DIR + 'optimized' + url.split('/')[-1]
    img = Image.open(raw_img_path)
    max_dims = (4000, 4000)
    img.thumbnail(max_dims)
    img.save(optimized_img_path)

    new_size = os.path.getsize(
        optimized_img_path)
    print('New size: %s' % new_size)
    if (new_size > SIZE_LIMIT):
        print('ERROR: Unable to get filesize below limit', url)

    asset_name = "%s%s" % splitext(basename(urlparse(url).path))
    uploaded_img = cma.uploads(CONTENTFUL_SPACE_ID).create(
        optimized_img_path)

    old_asset = cma_env.assets().find(asset.id)
    old_asset.unpublish()
    old_asset.delete()

    new_asset = create_asset(asset_name, uploaded_img.id, asset.id, asset_type)
    new_asset.publish()


env_vars = load_dotenv()

CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
CONTENTFUL_CDN_KEY = os.getenv('CONTENTFUL_CDN_KEY_GLOBAL')
CONTENTFUL_CMA_KEY = os.getenv('CONTENTFUL_CMA_KEY_GLOBAL')

client = contentful.Client(
    CONTENTFUL_SPACE_ID, CONTENTFUL_CDN_KEY, environment="master")

cma = contentful_management.Client(CONTENTFUL_CMA_KEY)
cma_env = cma.environments(CONTENTFUL_SPACE_ID).find('master')

total = client.assets({"limit": 1}).total
i = 0
j = 0
limit = 1000
SIZE_LIMIT = 20000000

large_asset_ids = []

while(i < total):
    assetCollection = client.assets({"skip": i, "limit": limit})
    i += len(assetCollection.items)

    for asset in assetCollection.items:
        size = asset.fields('en').get('file').get('details').get('size')
        if (size > SIZE_LIMIT):
            j += 1
            print('Asset exceeded size')
            print('Image with size: %s' % size)
            large_asset_ids.append(asset.id)
            resize(asset)
            print('Resized asset %s' % j)

with open('large-asset-ids.txt', 'wb') as file:
    pickle.dump(large_asset_ids, file)
