from accepted_headings import is_accepted_heading
from headings import get_heading_id
from util.beautifulsoup import next_element, get_text


def soup_to_usp_collections(soup, locale):
    # soup: BeautifulSoup()
    # locale: en, en-AU, en-GB, ...
    # Returns: tuple( list[{ english_titles: list[str], title: str, usps: list[str] }], list[str] )

    usp_collections = []
    h3tags = soup.find_all('h3')
    unaccepted_headings = []

    for h3tag in h3tags:
        heading_text = h3tag.text.lower().strip()
        if (heading_text == ""):
            continue

        if (not is_accepted_heading(heading_text, locale)):
            unaccepted_headings.append(heading_text)

        title = h3tag.text.strip()
        id = get_heading_id(title.lower().strip(), locale)
        usp_collection = {"title": title,
                          "id": id, "usps": []}
        elem = next_element(h3tag)
        while elem and elem.name != 'h3':
            if (elem.name == "ul"):
                usp_collection["usps"] = [get_text(e)[:255]
                                          for e in elem.find_all("li")]
            elem = next_element(elem)
        usp_collections.append(usp_collection)
    return (usp_collections, unaccepted_headings)
