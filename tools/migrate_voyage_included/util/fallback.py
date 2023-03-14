def fallback(locale):
    en_fallbacks = ['en', 'en-AU', 'en-GB', 'en-US',
                    'de-DE', 'fr-FR', 'nb-NO', 'sv-SE', 'da-DK']
    de_fallbacks = ['gsw-CH']
    if locale in en_fallbacks:
        return 'en'
    if locale in de_fallbacks:
        return 'de-DE'
    return None
