# Wichtig:
# Groß- und Kleinschreibung beachten
# -> handled by "case insensitive"


name = {
    # Barlow:
    r'(?<!\w)[PBVW]a{1,2}r{0,1}[ndl]{0,2}o{1,2}u{0,1}w{0,1}(?!\w)':   'Barlow',
    r'(?<!\w)[PB]a{1,2}r{0,1}[ndl]{0,2}o{1,2}u{0,1}w{0,1}r{0,1}(?!\w)':   'Barlow',
    r'(?<!\w)[vVwWmM][aA]{1,2}[nNdDlL]{1,2}[oOuU]{1,2}[mMwW]{0,1}(?!\w)':   'Barlow',
    r'(?<!\w)[vVwWbB][aAhH]{1,2}[nNdDlL]{1,2}[oOuU]{1,2}[mMwW]{0,1}(ng){0,1}(?!\w)':   'Barlow',
    r'(?<!\w)[vVwWbB][aAhH]{1,2}[nNdDlL]{1,2}[oOuU]{1,2}[mMwW]{0,1}(ng){0,1}(?!\w)':   'Barlow',
    r'\bBalot*g*(ch)*(?!(mer))': 'Barlow',
    r'\bpal[ou]\b': 'Barlow',
    r'\bBalos\b': 'Barlows',

    # Onkel Barlow:
    r'(?<!\w)unkel{0,1}(?!\w)':   'Onkel',
    'onkel Campus': 'Onkel Barlow',
    'Onkel Manu': 'Onkel Barlow',
    'onkel war lo': 'Onkel Barlow',
    'onkel war': 'Onkel Barlow',
    'UnclipAllo': "Onkel Barlow",
    r'(?<!\w)[oO]nkel{0,1} (pENNIS)*(Wadl)*(pa am)*(?!\w)':   'Onkel Barlow',
    # pENNIS? WTF Whisper? WTF Trainingssatz...
    # onkel anime # nope, das war intentional

    'Balomer,': "Barlow, mal",
    r'\bBalomarc*k*t*\W': 'Barlow mag ',

    'Uli Sebalo': "Hallo Barlow",
    r'\bH[ae]lobar*low*\b': 'Hallo Barlow',
    r'\b[nh]e[iy]*ba[dr]*low*\b': 'Hey Barlow',
    # r'\bhei{0,1}ba[dr]ow{0,1}': 'Hey Barlow',
    # r'\bhai{0,1}ba[dr]ow{0,1}': 'Hi Barlow',
    r'\b[PH][ae]ibar*low*\b': 'Hi Barlow',
    r'\bJoBalo\b': 'Jo Barlow',
    r'\bHu*bar*low*\b': 'Huhu Barlow',
    r'\bHu*[ou]nkel*bar*low*\b': 'Huhu Onkel Barlow',
    # herzlich willkommen hier ist Barlow
    'herzlich willkommen hier ist war noch': 'herzlich willkommen hier ist Barlow',
    # r'willkommen,* hier ist [^(Barlow)] mit '   :   'willkommen, hier ist Barlow mit ', # nicht mehr notwendig
}

abrev = {
    r'\[kc]atar*\b': "Cata",
    r'\bBF\.*[- ][RA]\b': "BfA",
    r'\bPvE\b': "PvE",
    r'\bPvP\b': "PvP",
    r'\bSW.Tou*r\b': "SWTOR",
    r'\btl[ ;\.]dr\b': "TLDR",
    r'\bbow\b': "WoW",
    r'\b[vw]\.*o*\.*[vw]\.*\b': "WoW",
    r'\bwod\b': "WoD",
    r'\b[mdwpb][mn]z\b': 'BMZ',
    r'\b[aA][hH][aA]*\b': "AH",
    'AH-Effekt': "Aha-Effekt",
    r'\bnfr\b': "LFR",
    r'\bDDS\b': "DDs",
    r'\beds\b': "Adds",
    r"(?<![-'])\bED\b": "Add",
    r'\b[vV][oO][tT][lL][kK]\b': "WotLK",
    'D.O.T.L.K.': 'WotLK',
    r'\b[cC]{2}S\b': 'CCs',
    r'Radar\.io': 'raider.io',
    r'Rai*d[ea]r[\. (,)]i\.*o\.*': 'raider.io',
}

words = {
    r'\bheel(?=\w)': "heal-",
    r'\bheel': "heal",
    r'\bheel': "heal",
    r'\bhelse\b': "heal",
    r'\bhefen\b': "helfen",
    r'\bguilde(?=[n\b])': "Gilde",
    r'\b(?<!Sammel)gilder\b': "Gilde",
    r'(?<=[e ])radet': "geraided",
    r'\b[pP]al+adin*\b': "Paladin",
    # leaving rate -> Rate in there, but is not always right:
    r'\brate\b': "Raid",
    r'\bgerated\b': "geraided",
    r'\b\w*Wa\w* of Draenor': "Warlords of Draenor",
    r'\b\w*Wa\w* of Draenor': "gecue",
    r'\b\w*Wa\w* of Draenor': "-ed un 'ed",
    # testing

    # testing end
    r'\bFierigkeiten\b': "Schwierigkeiten",
    'Formists of Pandaria': "vor Mists of Pandaria",

    # Cue (Hinweis) und Queue (Warteschlange)
    r"gecue.ed": "gequeued",
    r"Solo.cue": "Solo Queue",
    r"Dungeon.cue": "Dungeon Queue",
    r"cue.window": "Queue Window",

    r"Lordhawk": "Lore Talk",
    r"Lore-Talk": "Queue Window",
    "Poiseken": 'Päuseken',

    # Latein
    "Cumhawk ergopropterhawk": 'cum hoc ergo propter hoc',
    "posthawk ergopropterhawk": 'post hoc ergo propter hoc',

    r"\bKil[' ]jae*den\b": "Kil'jaeden",
    r"\bDeb\b": "Depp",
    r'\bini\b': "Ini",
    'Mythik': "Mythic",
    r'[hH]ailer': "Heiler",
    'Edron': 'Add-on',
    'Addon': 'Add-on',
    r'\b[iI]ngenie-(?=\w)': 'ingame-',
    r'\b[iI]ngenie(?!-)\b': 'Ini',
    'Amount': 'Mount',
    r'[dD]ungen': 'Dungeon',
    'älter Scrolls': 'Elder Scrolls',
    'Cell-Run': 'Sellrun',
    r'[pP]arlor': 'Pala',
    r'\b[pP][rRoO]{0,2}t[ -][pP][aA][rR]{0,1}[lA]+[aAoP][rR]{0,1}': 'Prot Pala',
    # 'gemopper' : 'gemopper', # dafuq?
    # 'baff' : 'Buff', # nicht immer
    # heel, self hier : 'heal', 'self heal
    'Olof Goldcap': 'Null auf Goldcap',
    r'\bingame[^-]':  'ingame-'
}

acro = {
    'BMZ': {
        'Cata': ['Cataclysm'],
        'Afd': ['Alternative für Deutschland'],
        'SWTOR': ['Star Wars: The Old Republic'],
        'BMI': ['body mass index'],
        'DMB': ['Deadly Boss Mods'],
        'TBC': ['The Burning Crusade'],
        'WoW': ['World of Warcraft'],
        'LFR': ['looking for raid'],
        'LFG': ['looking for group'],
        'BG': ['battleground'],
        'RBG': ['random battleground'],
        'IO': ['Raider.IO'],
        'MC': ['Molten Core'],
        'HC': ['heroic'],
        'MVP': ['at the moment'],
        'MVP': ['most valuable player'],
        'Dev': ['Developer'],
        'aka': ['also known as'],
        'DK': ['death knights'],
        'MMO': ['massively multiplayer online'],
        'MMOG': ['massively multiplayer online game'],
        'MMORPG': ['massively multiplayer online role-playing game'],
        'DD': ['damage dealer'],
        'nHC ': ['non heroic'],
        'PvP': ['Player versus Player'],
        'PvP': ['Player versus Environment'],
        'Mob': ['mobile object'],
        # TODO: fix mistake with "Adds" -> most likely rework acro detection
        # 'Add': ['additional enemy', 'Adds', 'additional enemies'],
        'DPS': ['damage per second'],
        'CC': ['crowd control'],
        'Pot': ['potion'],
        'DoT': ['damage over time'],
        'RP': ['role-play'],
        'ERP': ['erotic role-play'],
        'RPG': ['role-playing game'],
        'HPS': ['healing per second'],
        'HoT': ['healing over time'],
        'LKW': ['Lastkraftwagen', 'LKWs', 'Lastkraftwagen'],
        'AH': ['Auktionshaus'],
        'BMAH': ['Black Market Auction House'],
        'TSM': ['TradeSkillMaster'],
        'OG': ['Orgrimmar'],
        'TLDR': ["too long; didn't read"],
        'Ini': ['Instanz'],
        'M+': ['Mythic+'],
        'BfA': ['Battle for Azeroth'],
        'WotLK': ['Wrath of the Lich King'],
        'WoD': ['Warlords of Draenor'],
        'DKP': ['dragon kill points'],
        'NFL': ['National Football League'],
        'Abo': ['Abonnement'],
        'MoP': ['Mists of Pandaria'],
        'USA': ['United States of America'],
        'DDR': ['Deutsche Demokratische Republik'],
        'GCD': ['global cooldown'],
        'AE': ['Area of Effect'],
        'AoE': ['Area of Effect'],
        'CD': ['cooldown'],
        'ARD': ['Arbeitsgemeinschaft der öffentlich-rechtlichen Rundfunkanstalten der Bundesrepublik Deutschland'],
        'ZDF': ['Zweites Deutsches Fernsehen'],
        'API': ['application programming interface'],
        'oom': ['out of mana'],
        'BRD': ['Bundesrepublik Deutschland'],
        'ToS': ['terms of service'],
        'RNG': ['random number generator'],
        'Int': ['intelligence'],
        'Def': ['defense'],
        'App': ['application'],
    }
}

for key, value in acro.items():
    acro[key] = dict(sorted(value.items(), key=lambda i: i[0].lower()))


"""
376
Steht BMZ für barlos Meinungs-Streit, Meinungs-Austauschzimmer? 
Ich sage gar nichts dazu. Also weder ein Ja 
noch ein Nein. Wenn ich jedes Mal Nein sage 
und ihr irgendwann das Richtige sagt, dann würde 
ich nicht Nein sagen und ihr wüsstet, AH, da du 
nicht Nein gesagt hast, sind wir wohl auf dem richtigen Weg. 
Eines Tages werde ich verkünden, was BMZ heißt. 
Ich muss mir noch überlegen, wann genau ich das mache. 
Vielleicht im 1000. BMZ oder so? Keine Ahnung. 
Ich habe das schon mal, glaube ich, erklärt, dass es 
für mich so ein Seriengeheimnis ist wie bei den Fernsehserien 
in den 70er, 80er, teilweise auch noch 90er Jahren,
wo es immer in jeder Serie so eine Kleinigkeit gab, 
die man irgendwie nicht wusste und die so das Geheimnis war.
"""

"""
findall(r'\bB\w* M\w* Z\w*')
Folge 488
Fünfte Frage steht BMZ für 
Barlow Mecker zurück 
oder 
Balos 
Meinungszeit. Ich weiß, dass ich darauf keine Antwort
 bekomme, aber es macht mich fuchsig. 
 Irgendwann werde ich eine Antwort geben. 
 Ich überlege gerade, wann ich die Antwort 
 gebe. Gebe ich die Antwort in einem bestimmten 
 BMZ, im 1000. zum Beispiel? Vielleicht kündige 
 ich es nicht vorher an, sodass ihr euch denkt, 
 Mensch, jetzt muss ich aber mal das 1000. BMZ 
 gucken. Oder mache ich das, wenn wir irgendeinen
 anderen Meilenstein erreichen? Zuschauerzahlen 
 oder so, oder Subs oder Abos oder so? Keine Ahnung. 
 Irgendwann werde ich es bestimmt mal verraten, 
 aber im Moment noch nicht. Vielleicht passiert es 
 auch einfach im 1142. BMZ oder so. So was, 
 was überhaupt keiner rechnet und sich dann nur 
 im Nachhinein die Leute denken, verdammt, 
 damals dieser Barlow im 488. BMZ, der ist 
 schon gesagt, im 1241. BMZ könnte er verraten, 
 wofür BMZ steht. Ich habe es gewusst und es 
 mir gebuckmarkt und es muss genau, jetzt könnt 
 ihr irgendjemand ausrechnen, welches Datum das 
 ist in dem das 1000. BMZ kommt. Irgendwann 
 verrate ich es euch. Vielleicht mal, wenn 
 ihr mal lieb seid. Und ja gut, das ist dann 
 lange nicht, bis zum 1241. BMZ. Das soll es 
 gewesen sein für heute. Macht es gut und tschüss, 
 sagt euer Onkel Barlow.

"""

"""
851

Balomarck Züge
"""

main = {
    'BMZ':   name | abrev | words
}
