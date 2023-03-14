from enum import Enum


class Heading(str, Enum):
    HOTEL = 'HOTEL',
    FLIGHTS = 'FLIGHTS',
    TRANSFERS = 'TRANSFERS',
    EXPEDITION_CRUISE = 'EXPED_CRUISE',
    ONBOARD_ACTIVITIES = 'ONBRD_ACTIV',
    LANDING_ACTIVITIES = 'LAND_ACTIV',
    NOTES = 'NOTES',
    EXCURSIONS = 'EXCURSIONS',
    ACTIVITIES = 'ACTIVITIES',
    EXTRAS = 'EXTRAS'
    UNKNOWN = 'UNKNOWN'


def heading_en2en(heading: str):
    if (heading == 'extras'):
        return Heading.EXTRAS
    if (heading == 'excursions' or heading == 'excursion'):
        return Heading.EXCURSIONS
    if (heading == 'hotel' or heading == 'hotels'):
        return Heading.HOTEL
    if (heading == 'flight' or heading == 'flights'):
        return Heading.FLIGHTS
    if (heading == 'transfer' or heading == 'transfers'):
        return Heading.TRANSFERS
    if(heading == 'expedition cruise'):
        return Heading.EXPEDITION_CRUISE
    if (heading == 'onboard activities'):
        return Heading.ONBOARD_ACTIVITIES
    if (heading == 'landing activities'):
        return Heading.LANDING_ACTIVITIES
    if (heading == 'notes'):
        return Heading.NOTES
    if (heading == 'activities'):
        return Heading.ACTIVITIES
    return Heading.UNKNOWN


def heading_de2en(heading: str):
    if (heading == 'aktivitäten'):
        return Heading.ACTIVITIES
    if (heading == 'hotel' or heading == 'hotels'):
        return Heading.HOTEL
    if (heading == 'flüge' or heading == 'flug'):
        return Heading.FLIGHTS
    if (heading == 'transfer' or heading == 'transfers'):
        return Heading.TRANSFERS
    if(heading == "expeditions-seereise"):
        return Heading.EXPEDITION_CRUISE
    if (heading == "aktivitäten an bord"):
        return Heading.ONBOARD_ACTIVITIES
    if (heading == "erkundungstouren" or heading == "aktivitäten an land"):
        return Heading.LANDING_ACTIVITIES
    if (heading == 'hinweise'):
        return Heading.NOTES
    if (heading == 'extras'):
        return Heading.EXTRAS
    if (heading == 'ausflug' or heading == 'ausflüge'):
        return Heading.EXCURSIONS
    return Heading.UNKNOWN


def heading_fr2en(heading_: str):
    heading = ''.join([h for h in heading_ if h.isalnum() or h.isspace()])
    if heading == 'croisières dexpédition' or heading == 'croisière dexpédition':
        return Heading.EXPEDITION_CRUISE
    if (heading == 'activités à bord'):
        return Heading.ONBOARD_ACTIVITIES
    if (heading == 'activités à terre'):
        return Heading.LANDING_ACTIVITIES
    if (heading == 'remarques'):
        return Heading.NOTES
    if (heading == 'transferts' or heading == 'transfert'):
        return Heading.TRANSFERS
    if (heading == 'hôtel' or heading == 'hôtels'):
        return Heading.HOTEL
    if (heading == 'vols' or heading == 'vol'):
        return Heading.FLIGHTS
    if (heading == 'activités'):
        return Heading.ACTIVITIES
    if (heading == 'suppléments' or heading == 'autres'):
        return Heading.EXTRAS
    if (heading == 'excursion'):
        return Heading.EXCURSIONS
    return Heading.UNKNOWN


def heading_no2en(heading: str):
    if (heading == 'utflukter' or heading == 'utflukt'):
        return Heading.EXCURSIONS
    if (heading == 'tillegg'):
        return Heading.EXTRAS
    if (heading == 'aktiviteter'):
        return Heading.ACTIVITIES
    if (heading == 'merknader'):
        return Heading.NOTES
    if (heading == 'ekspedisjonscruise'):
        return Heading.EXPEDITION_CRUISE
    if (heading == 'hotell' or heading == 'hoteller' or heading == 'hotel'):
        return Heading.HOTEL
    if (heading == 'landingsaktiviteter' or heading == 'aktiviteter på land' or heading == 'aktiviteter i land'):
        return Heading.LANDING_ACTIVITIES
    if (heading == 'aktiviteter om bord'):
        return Heading.ONBOARD_ACTIVITIES
    if (heading == 'transport' or heading == 'transporter'):
        return Heading.TRANSFERS
    if (heading == 'flyvninger' or heading == 'flygninger' or heading == 'flygning' or heading == 'fly' or heading == 'flyreiser'):
        return Heading.FLIGHTS
    return Heading.UNKNOWN


def heading_dk2en(heading: str):
    if (heading == 'supplementer'):
        return Heading.EXTRAS
    if (heading == 'aktiviteter'):
        return Heading.ACTIVITIES
    if (heading == 'flyrejser' or heading == 'flyafgange' or heading == 'flyrejse' or heading == 'flyvrejser'):
        return Heading.FLIGHTS
    if (heading == 'bemærkninger'):
        return Heading.NOTES
    if (heading == 'ekspeditionskrydstogt' or heading == 'expeditionsrejse' or heading == 'ekspeditionsrejse'):
        return Heading.EXPEDITION_CRUISE
    if (heading == 'aktiviteter ombord' or heading == 'aktiviteter om bord'):
        return Heading.ONBOARD_ACTIVITIES
    if (heading == 'aktiviteter ved landgang' or heading == 'aktiviteter i land' or heading == 'landgangs-aktiviteter' or heading == 'aktiviteter på land'):
        return Heading.LANDING_ACTIVITIES
    if (heading == 'hotel' or heading == 'hoteller'):
        return Heading.HOTEL
    if (heading == 'transport'):
        return Heading.TRANSFERS
    if (heading == 'udflugter' or heading == 'udflugt'):
        return Heading.EXCURSIONS
    return Heading.UNKNOWN


def heading_se2en(heading: str):
    if (heading == 'tillägg'):
        return Heading.EXTRAS
    if (heading == 'aktiviteter'):
        return Heading.ACTIVITIES
    if (heading == 'utflykter' or heading == 'utflykt'):
        return Heading.EXCURSIONS
    if (heading == 'flyg' or heading == 'flygresa' or heading == 'flygresor'):
        return Heading.FLIGHTS
    if (heading == 'hotell'):
        return Heading.HOTEL
    if (heading == 'transfer' or heading == 'transfers' or heading == 'transferresor' or heading == 'transport'):
        return Heading.TRANSFERS
    if (heading == 'aktiviteter ombord'):
        return Heading.ONBOARD_ACTIVITIES
    if (heading == 'aktiviteter med landstigning' or heading == 'aktiviteter i land'):
        return Heading.LANDING_ACTIVITIES
    if (heading == 'expeditionskryssning' or heading == 'expeditionsresa'):
        return Heading.EXPEDITION_CRUISE
    if (heading == 'observera:' or heading == 'observera'):
        return Heading.NOTES
    return Heading.UNKNOWN


heading_translators = {
    'en': heading_en2en,
    'de-DE':  heading_de2en,
    'gsw-CH':  heading_de2en,
    'fr-FR': heading_fr2en,
    'nb-NO': heading_no2en,
    'da-DK': heading_dk2en,
    'sv-SE': heading_se2en
}

english_locales = ['en', 'en-AU', 'en-GB', 'en-US']


def get_heading_id(heading: str, from_locale: str):
    if (from_locale in english_locales):
        from_locale = 'en'

    translator = heading_translators.get(from_locale)

    if translator is None:
        raise Exception(
            f'No heading translator defined from locale {from_locale}')

    return translator(heading)
