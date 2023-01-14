import re

hashtag = '#'

def write_individual_wiki_page_BMZ(ID, episode_info):
    date = ''
    if 'date' in episode_info:
        date = episode_info['date']
    runtime = ''
    if 'runtime' in episode_info:
        runtime = episode_info['runtime']
    url = ''
    if 'url' in episode_info:
        url = episode_info['url']
    title_full = ''
    if 'title_full' in episode_info:
        title_full = episode_info['title_full']
    title = ''
    if 'title' in episode_info:
        title = episode_info['title']
    category = ''
    if len(title_full) > len (title):
        category = title_full[:-(len(title)+1)]
    transcript = ''
    if 'transcript' in episode_info:
        transcript = episode_info['transcript']
    leading_zeros = ''
    if ID < 9:
        leading_zeros = '00'
    elif ID < 99:
        leading_zeros = '0'

    description = ""
    if 'description' in episode_info:
        description += episode_info['description'] + '\n\n'
    text = f"""{description}"""
    #todo : continue putting all of this into the """string
    text += '{| class="wikitable"' + '\n'
    text += '! ' + hashtag + ' !! date !! runtime !! url' + '\n'
    text += '|-' + '\n'
    text += '| ' + str(ID+1) + ' || ' + date + ' || ' + \
        runtime + ' || ' + url + '\n'
    text += '|}' + '\n'
    text += '\n'
    text += '= Zusammenfassung =' + '\n'
    text += '<Zusammenfassung>' + '\n'
    text += '\n'
    text += '= Lessons Learned =' + '\n'
    text += '== <Lesson Learned 1> ==' + '\n'
    text += '\n'
    text += '= Transkript =' + '\n'
    text += transcript + '\n'
    text += '\n'
    # nickname = row[elements['title']].split("|", 1)[1]
    # nickname = nickname.replace("]]", "")
    # text += '[[Kategorie:Hagrids Hütte:Hörspiel|' + nickname + ']]' + '\n'
    text += '[[Kategorie:' +  category + '|' + leading_zeros + title + ']]'# + '\n'
    return text
    # filename = helper.fill_digits(id, 4)
    # with open(input_path + filename + '_wiki.txt', 'w') as f:
    #     f.write(text)

def write_mainpage(episodes_info):
    text = 'https://www.youtube.com/c/OnkelBarlow\n'
    text += '\n'
    text += '= Podcast =\n'
    text += '*[[OnkelBarlow/BMZ]]\n'
    text += '**[[:Category:OnkelBarlow/BMZ|BMZ Kategorie]]\n'
    text += '*[[:Category:Onkel Barlow:Guide|Guide]]\n'
    text += '\n'
    text += '= Übersicht =\n'
    text += '== Podcast ==\n'
    text += '{| class="wikitable sortable"\n'
    text += '|+ playlist\n'
    text += '|-\n'
    text += '! title !! description !! author_type !! author_name !! publisher !! language !! @type !! accessMode !! url !! image\n'
    text += '|-\n'
    text += '| [[OnkelBarlow/BMZ|BMZ]] || Listen to BMZ on Spotify.  || Person || [https://www.youtube.com/@OnkelBarlow OnkelBarlow] || George Zaal || de || PodcastSeries || auditory || [https://www.youtube.com/playlist?list=PLv3Aqr0YYT6S_8mdaKCBu0pskPLNEPSlJ YouTube][https://open.spotify.com/show/55UqBIZCSXoBZB5jVXEzHq Spotify] || [https://i.scdn.co/image/13d386beb25f08329057330ebe053172e6f7a506 image]\n'
    text += '|}\n'
    text += '\n'
    text += '\n'
    text += '\n'
    text += '=== Episoden ===\n'
    text += '{| class="wikitable sortable"\n'
    text += '|+ episodes\n'
    text += '|-\n'
    text += f'! {hashtag} !! date !! runtime !! title !! url\n'
    text += '|-\n'
    
    for ID, episode_info in episodes_info.items():
        date = ''
        if 'date' in episode_info:
            date = episode_info['date']
        runtime = ''
        if 'runtime' in episode_info:
            runtime = episode_info['runtime']
        url = ''
        if 'url' in episode_info:
            url = episode_info['url']
        link_to_title = ''
        if 'link_to_title' in episode_info:
            link_to_title = episode_info['link_to_title']

        text += '|-' + '\n'
        text += '| ' + str(ID+1) + ' || ' + date + ' || ' + \
            runtime + ' || ' + link_to_title +  ' || ' + url + '\n'


    text += '|}\n'
    text += '\n'
    text += '= Tags =\n'
    text += '[[Category:Podcast]]\n'
    text += '[[Category:German]]\n'
    text += '[[Category:Unterhaltung]]\n'
    text += '[[Category:Bildung]]\n'
    return text
