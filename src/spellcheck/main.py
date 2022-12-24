import spellcheck.barlow as barlow

main_dict = {
    'regular':   {
        r'Nr\.*(?= \d)': 'Nummer',
        r'(?<=\d)%ig': '-prozentig',
        r'(?<=\d)%': ' Prozent',
        # '......' : ' ', # Gedankenpause
        # '...' : ' ', # auslaufende Gedanken
        r'\bmanchemal\b': 'manchmal',
        r'곳' : '',
        r'수' : '',
        r'가' : '',
        r'물' : '',
        r'т' : '',
        r'а' : '',
    }
} | barlow.main

acro = barlow.acro