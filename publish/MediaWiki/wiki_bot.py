import logging
from mwclient import Site


class page_promt:
    # , **kwargs):
    def __init__(self, text, summary='', minor=False, bot=True, section=None):
        self.text = text
        self.summary = summary
        self.bot = bot
        self.section = section
        self.text = text
        # TODO: understand this
        # self.**kwargs = **kwargs


def handle_queries(queries):
    logging.basicConfig(level=logging.WARNING)

    ua = 'playlist2wiki-converter/0.0 (https://github.com/borgnetzwerk/playlist2wiki-converter)'
    site = Site('data.bnwiki.de', path='/', clients_useragent=ua)

    with open("C:\\auth_tokens\\a.txt") as f:
        pw = f.readlines()[0]
    site.login('timborg', pw)
    del pw

    for pagename, tasks in queries.items():
        page = site.pages[pagename]
        for order, promt in tasks.items():
            if order == 'edit':
                if page.text() == promt.text:
                    continue
                """If the page didn’t exist, this operation will create it."""
                page.edit(promt.text, summary=promt.summary,
                          bot=promt.bot, section=promt.section)
            else:
                print('unknown order: ' + str(order))
            # if page.exists:
            # page.exists
            # text = page.text()


def main(queries):
    handle_queries(queries)

    # csv2table(input_path, lookupCSV(input_path))


if __name__ == '__main__':
    main()
