import csv
import sys

import os
from os import listdir
from os.path import isfile, join

csv_delimiter = ';'

individual_wiki_pages_per_episode = False

def fill_digits(var_s, num = 2):
    var_s = str(var_s)
    while len(var_s) < num:
        var_s = "0" + var_s
    return var_s

def write_individual_wiki_page(input_path, id, row, elements):
    filename = fill_digits(id, 4)
    with open(input_path + filename + '_wiki.txt', 'w') as f:
        f.write(row[elements['description']] + '\n')
        f.write('\n')
        hashtag = '#'
        f.write('{| class="wikitable"' + '\n')
        f.write('! ' + hashtag + ' !! date !! runtime !! url' + '\n')
        f.write('|-' + '\n')
        f.write('| ' + str(id) + ' || ' + row[elements['date']] + ' || ' + row[elements['runtime']] + ' || ' + row[elements['url']] + '\n')
        f.write('|}' + '\n')
        f.write('\n')
        f.write('= Zusammenfassung =' + '\n')
        f.write('<Zusammenfassung>' + '\n')
        f.write('\n')
        f.write('= Hörspiele =' + '\n')
        f.write('== <Titel Hörspiel 1> ==' + '\n')
        f.write('\n')
        f.write('= Transkript =' + '\n')
        f.write('\n')
        nickname = row[elements['title']].split("|", 1)[1]
        nickname = nickname.replace("]]", "")
        f.write('[[Kategorie:Hagrids Hütte:Hörspiel|' + nickname +  ']]' + '\n')
        f.write('[[Kategorie:Hagrids Hütte:Episode|' + nickname +  ']]' + '\n')

def csv2table(input_path, filenames):
    for filename in filenames:
        cols = 1
        with open(input_path + filename, newline='') as rf, open(input_path + filename.replace(".csv", "") + '_wiki.txt', 'w') as f:
            freader = csv.reader(rf, delimiter=csv_delimiter)
            lines = []
            elements = {
                "runtime"   : -1,
                "date"  : -1,
                "description" : -1,
                "title"  : -1,
                "url"  : -1
            }
            f.write('{| class="wikitable sortable"' + '\n')
            f.write('|+ ' + filename.replace(".csv", "") + '\n')
            for idx, row in enumerate(freader):
                f.write('|-' + '\n')
                if len(row) > cols:
                    cols = len(row)
                if idx == 0:
                    for idy, element in enumerate(row):
                        if element in elements:
                            elements[element] = idy
                    f.write('! ' + ' !! '.join(row) + '\n')
                else:
                    f.write('| ' + ' || '.join(row) + '\n')
                    if individual_wiki_pages_per_episode and filename == "episodes.csv":
                        write_individual_wiki_page(input_path, idx, row, elements)
            f.write('|}' + '\n')
        # outfile.write('{| class = class="wikitable sortable"\n')

def lookupCSV(input_path):
    input_path
    onlyfiles = [f for f in listdir(input_path) if isfile(join(input_path, f))]
    return [f for f in onlyfiles if ".csv" in f]

def main(input_path = os.getcwd()):

    csv2table(input_path, lookupCSV(input_path))

if __name__ == '__main__':
    main()