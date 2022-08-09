import json
import contentful_management
import contentful
import os
from urllib.request import urlopen, Request
from dotenv import load_dotenv
import time
import pickle
from htmldocx import HtmlToDocx
from rich_text_renderer import RichTextRenderer

renderer = RichTextRenderer()
env_vars = load_dotenv()

CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
CONTENTFUL_CDN_KEY = os.getenv('CONTENTFUL_CDN_KEY_GLOBAL_PREVIEW')
CONTENTFUL_ENVIRONMENT = os.getenv('CONTENTFUL_ENVIRONMENT')

API_URLS = {
    # "en-US": "https://www.hurtigruten.com/rest/b2b/voyages"
    "en": "https://global.hurtigruten.com/rest/b2b/programs",
    "en-US": "https://www.hurtigruten.com/rest/b2b/programs",
    "en-GB": "https://www.hurtigruten.co.uk/rest/b2b/programs",
    "en-AU": "https://www.hurtigruten.com.au/rest/b2b/programs",
    # "de": "https://www.hurtigruten.de/rest/excursion/excursions",
    # "fr-FR": "https://www.hurtigruten.fr/rest/excursion/excursions"
}

locales = ['en']  # , 'en-US', 'en-GB', 'en-AU']

client = contentful.Client(
    CONTENTFUL_SPACE_ID, CONTENTFUL_CDN_KEY, environment=CONTENTFUL_ENVIRONMENT, api_url='preview.contentful.com')
voyage_ids = client.entries({
    'content_type': 'voyage',
    'select': 'sys.id',
    'limit': 1
}).items

voyage_ids = [v.id for v in voyage_ids]

print('Fetched voyage ids')

voyage_ids = ['74362']


def rt2html(fields, field_name):
    return renderer.render(fields.get(field_name)) if fields.get(field_name) else ''


def imgwrapper_url(wrapper):
    try:
        return 'https:' + wrapper.fields('en').get('image').fields('en').get('file').get('url') + '?w=1000'
    except Exception as e:
        print(e)
        return None


voyage_fields = ['internalName', 'shortDescription', 'longDescriptionTitle',
                 'longDescription', 'slug', 'itinerary',  'included', 'notIncluded', 'usPs', 'images', 'map', 'highlightedImage']

for voyage_id in voyage_ids:
    print('Fetching voyage')
    voyage = client.entry(voyage_id,  {"include": 2, "content_type": "voyage", "select": ",".join(
        ['fields.' + v for v in voyage_fields])})
    print('Fetched voyage')

    for locale in locales:
        document = '<!DOCTYPE html><html lang="en"><meta charset="UTF-8"><style>*{ font-weight: normal }</style><body>'

        if (not voyage.fields(locale)):
            continue

        fields = voyage.fields(locale)

        internal_name = fields.get('internal_name') or ''
        short_description = rt2html(fields, 'short_description')
        long_desc_title = fields.get('long_description_title') or ''
        long_desc = rt2html(fields, 'long_description')
        included = rt2html(fields, 'included')
        not_included = rt2html(fields, 'not_included')
        usps = fields.get('us_ps') or ''
        imgs_title = fields.get('images').fields(locale).get('title')
        map_img = imgwrapper_url(fields.get('map'))
        images = fields.get('images').fields('en').get('images')
        highlighted_image = imgwrapper_url(fields.get('highlighted_image'))

        document += '<h1>' + internal_name + '</h1>'

        document += '<img src="' + highlighted_image + '"/>' if highlighted_image else ''

        document += '<h2>Slug</h2>'
        document += '<p>' + fields.get('slug') + '</p>'

        document += '<h2>Short description</h2>'
        document += '<p>' + short_description + '</p>'

        document += '<h2>' + long_desc_title + '</h2>'
        document += '<p>' + long_desc + '</p>'

        document += '<img src="' + map_img + '"/>' if map_img else ''

        document += '<h2>Itinerary</h2>'
        for itd in fields.get('itinerary'):
            itd_img = imgwrapper_url(itd.fields(
                'en').get('highlighted_image')[0])
            document += '<h3>' + \
                itd.fields('en').get('day') + ' - ' + \
                itd.fields('en').get('title') + '</h3>'
            try:
                document += '<p>' + \
                    rt2html(itd.fields('en'), 'long_description') + '</p>'
            except:
                pass
            document += '<img src="' + itd_img + '"/>' if itd_img else ''

        document += '<h2>Included</h2>'
        document += '<p>' + included + '</p>'

        document += '<h2>Not included</h2>'
        document += '<p>' + not_included + '</p>'

        document += '<h2>USPs</h2>'
        document += '<ul>'
        for usp in usps:
            document += '<li>' + usp + '</li>'
        document += '</ul>'

        document += '<h2>' + imgs_title + '</h2>'
        for image in images:
            img_src = imgwrapper_url(image)
            document += '<img src="' + img_src + '"/>' if img_src else ''

        document += '</body></html>'

        html_file_name = "word/" + voyage_id + '_' + locale + ".html"
        print('Built HTML')
        with open(html_file_name, 'w', encoding='utf-8') as f:
            f.write(document)
        print('Saved HTML')

        # new_parser = HtmlToDocx()
        # new_parser.parse_html_file(html_file_name, "word/" + voyage_id + '_' + locale)
