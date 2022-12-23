import spellcheck.barlow as barlow

main_dict = {
    'regular':   {
        r'Nr\.*(?= \d)': 'Nummer',
        r'(?<=\d)%ig': '-prozentig',
        r'(?<=\d)%': ' Prozent',
        # '......' : ' ', # Gedankenpause
        # '...' : ' ', # auslaufende Gedanken
        r'\bmanchemal\b': 'manchmal'
    }
} | barlow.main

acro = barlow.acro
