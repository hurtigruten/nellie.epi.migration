import json
from urllib.request import Request, urlopen

from util import html_to_rt


headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'User-Agent': 'Magic ZBrowser'
}

urls = {
    "en": "https://global.hurtigruten.com/rest/b2b/voyages/",
    "en-AU": "https://www.hurtigruten.com.au/rest/b2b/voyages/",
    "en-GB": "https://www.hurtigruten.co.uk/rest/b2b/voyages/",
    "en-US": "https://www.hurtigruten.com/rest/b2b/voyages/",
    "de-DE": "https://www.hurtigruten.de/rest/b2b/voyages/",
    "gsw-CH": "https://www.hurtigruten.ch/rest/b2b/voyages/",
    "sv-SE": "https://www.hurtigrutenresan.se/rest/b2b/voyages/",
    "nb-NO": "https://www.hurtigruten.no/rest/b2b/voyages/",
    "da-DK": "https://www.hurtigruten.dk/rest/b2b/voyages/",
    "fr-FR": "https://www.hurtigruten.fr/rest/b2b/voyages/",
}



def get_voyage_field(voyage_id, field_name):
    field = {}
    for locale, url in urls.items():
        try:
            req = Request(url + voyage_id, headers=headers)
            res = urlopen(req).read()
            epi_voyage = json.loads(res.decode('utf-8'))

            is_fallback = epi_voyage["isFallbackContent"]
            if (is_fallback):
                continue
            field[locale] = epi_voyage[field_name]
        except:
            print(f'[WARNING]: Failed to fetch {locale}:{voyage_id} from EPI')
    if (field == {}):
        return None
    return field

def get_voyage_included(voyage_id):
    return get_voyage_field(voyage_id, "includedInfo")

def get_voyage_not_included(voyage_id):
    not_included_html = get_voyage_field(voyage_id, "notIncludedInfo")
    not_included_rt = {}

    for locale, value in not_included_html.items():
        not_included_rt[locale] = html_to_rt(value)

    return not_included_rt
