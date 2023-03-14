from util import fallback

accepted_headings = {
    'en': [
        "hotel",
        "hotels",
        "flight",
        "flights",
        "transfer",
        "transfers",
        "expedition cruise",
        "onboard activities",
        "landing activities",
        "notes"
    ],
    'de-DE': [
        "expeditions-seereise",
        "aktivitäten an bord",
        "aktivitäten an land",
        "erkundungstouren",  # landing activities synonym
        "hotel",
        "hotels",
        "flüge",
        "flüges",
        "transfer",
        "transfers",
        "hinweise"
    ]
}


def is_accepted_heading(heading: str, locale: str):
    headings = accepted_headings.get(locale)
    headings = headings or accepted_headings.get(fallback(locale))
    headings = headings or []

    return heading in headings
