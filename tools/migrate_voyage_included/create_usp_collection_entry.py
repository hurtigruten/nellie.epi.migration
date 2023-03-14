from util import entry_link, map_usp_heading_id_to_icon, map_usp_heading_id_to_type


def create_usp_collection_entry(cm_env, usp_collection, booking_codes: list[str]):
    if (usp_collection == {}):
        print('[WARNING]: Empty USP collection')
        return
    first_collection = usp_collection.get(
        'en') or list(usp_collection.values())[0]
    icon = map_usp_heading_id_to_icon(first_collection["id"])
    type = map_usp_heading_id_to_type(first_collection["id"])

    locale_fields = {
        "internalName": {"en": ",".join(booking_codes) + ' - ' + first_collection["title"]},
        "title": {"en": ""},
        "type": {"en": type},
        "icon": {"en": icon or ""},
        'usPs': {"en": []}
    }

    locales = list(usp_collection.keys())
    for locale, collection in usp_collection.items():
        locale_fields['title'][locale] = collection["title"]
        locale_fields["usPs"][locale] = collection["usps"]

    entry_attributes = {
        "content_type_id": "uspCollection",
        "fields": locale_fields
    }

    try:
        entry = cm_env.entries().create(None, entry_attributes)
        entry.publish()
        return {"entry_link": entry_link(entry.id), "locales": locales}
    except Exception as e:
        print(f'Unable to create/publish usp collection: {e}')
        print(entry_attributes)
