import wiki.barlow as barlow

def write_individual_wiki_page(p_n, ID, episode_info):
    if p_n == 'BMZ':
        return barlow.write_individual_wiki_page_BMZ(ID, episode_info)

def write_episodes(p_n, episodes_info):
    if p_n == 'BMZ':
        return barlow.write_mainpage(episodes_info)

# acro = barlow.acro