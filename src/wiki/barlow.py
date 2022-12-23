import re

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



    text = ''
    if 'description' in episode_info:
        text += episode_info['description'] + '\n'
        text += '\n'
    hashtag = '#'
    text += '{| class="wikitable"' + '\n'
    text += '! ' + hashtag + ' !! date !! runtime !! url' + '\n'
    text += '|-' + '\n'
    text += '| ' + str(ID) + ' || ' + date + ' || ' + \
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
