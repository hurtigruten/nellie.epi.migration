def get_text(e):
    try:
        p = next(e.find_all("p"))
        return p.text
    except:
        if (hasattr(e, "text")):
            return e.text


def next_element(elem):
    while elem is not None:
        # Find next element, skip NavigableString objects
        elem = elem.next_sibling
        if hasattr(elem, 'name'):
            return elem
