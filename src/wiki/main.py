import wiki.barlow as barlow

def write_individual_wiki_page(p_n, ID, episode_info):
    if p_n == 'BMZ':
        return barlow.write_individual_wiki_page_BMZ(ID, episode_info)

# acro = barlow.acro