
from headings import Heading


def map_usp_heading_id_to_type(id: Heading):
    if id == Heading.FLIGHTS:
        return "Flight"
    if id == Heading.HOTEL:
        return "Hotel"
    if id == Heading.TRANSFERS:
        return 'Transfer'
    if id == Heading.ONBOARD_ACTIVITIES:
        return 'OnboardActivities'
    if id == Heading.LANDING_ACTIVITIES:
        return 'LandingActivities'
    if id == Heading.EXPEDITION_CRUISE:
        return 'ExpeditionCruise'
    if id == Heading.EXCURSIONS:
        return 'Excursions'
    if id == Heading.ACTIVITIES:
        return 'Activities'
    if id == Heading.NOTES:
        return 'Notes'
    if id == Heading.EXTRAS:
        return 'Extras'
    return 'Other'
