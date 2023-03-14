
from headings import Heading


def map_usp_heading_id_to_icon(id: Heading):
    if id == Heading.FLIGHTS:
        return "ri-plane-line"
    if id == Heading.HOTEL:
        return "ri-hotel-line"
    if id == Heading.TRANSFERS:
        return 'ri-bus-fill'
    if id == Heading.ONBOARD_ACTIVITIES:
        return "ri-anchor-line"
    if id == Heading.LANDING_ACTIVITIES:
        return "ri-landscape-line"
