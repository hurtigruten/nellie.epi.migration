
def entry_link(entry_id):
    if entry_id is None:
        return None
    return {"sys": {"type": "Link", "linkType": "Entry", "id": str(entry_id)}}
