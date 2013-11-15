#! /usr/bin/env python

import httplib
from xml.dom.minidom import parseString
from urlparse import urlparse
import sys
import os
import json

from utils import load_json_file


#------------- ENUMERATIONS --------------------------

RAID_DIFFICULTIES = {
    3: 'normal 10',
    4: 'normal 25',
    5: 'heroic 10',
    6: 'heroic 25',
    7: 'lfr',
    14: 'flex',
}



#------------- FUNCTIONS --------------------------

def retrieve_url(url):
    o = urlparse(url)

    connection = httplib.HTTPConnection(o.netloc, 80)

    try:
        connection.connect()
    except:
        print "Failed to connect to the server '%s'" % o.netloc
        return None

    try:
        connection.request('GET', o.path)
        response = connection.getresponse()
    except:
        print "Failed to retrieve the page at 'http://%s/%s'" % (o.netloc, o.path)
        connection.close()
        return None

    content = response.read()

    connection.close()

    return content



# Process the command-line arguments
if (len(sys.argv) > 3) or (len(sys.argv) < 2):
    print "Usage: %s [<output_folder>] URL" % sys.argv[0]
    print
    print "URL must be of the form: http://eu.battle.net/wow/en/zone/siege-of-orgrimmar/"
    print
    sys.exit(-1)


if len(sys.argv) == 3:
    dest = sys.argv[1]
    url = sys.argv[2]
elif len(sys.argv) == 2:
    dest = '.'
    url = sys.argv[1]

dest = os.path.abspath(dest)

if url[-1] != '/':
    url += '/'


# Download the HTML page
content = retrieve_url(url)


# Parse it to retrieve the raid name
document = parseString(content)

title = document.getElementsByTagName('title')[0]
raid_name = title.firstChild.data.split('-')[0].strip()


# If needed, retrieve the slots of each item from the english loot HTML page
item_slots = None

if url.find('/en/') == -1:
    english_content = retrieve_url('http://us.battle.net/wow/en/' + '/'.join(url.split('/')[5:]) + 'loot')

    document = parseString(english_content)

    table_rows = document.getElementsByTagName('tr')

    item_slots = {}

    for row in table_rows:
        links = row.getElementsByTagName('a')

        try:
            item_link = filter(lambda x: x.hasAttribute('class') and \
                                         (x.getAttribute('class').find('item-link') >= 0), links)[0]
        except:
            # Not an item
            continue

        item_id = int(item_link.getAttribute('href').split('/')[-1])
        slot = row.getElementsByTagName('td')[3].firstChild.data.strip()

        item_slots[item_id] = slot


# Download the localized loot HTML page and parse it
content = retrieve_url(url + 'loot')

document = parseString(content)


# Extract the loot tables
boss_list = {}
table_rows = document.getElementsByTagName('tr')

for row in table_rows:
    links = row.getElementsByTagName('a')

    try:
        item_link = filter(lambda x: x.hasAttribute('class') and \
                                     (x.getAttribute('class').find('item-link') >= 0), links)[0]
        boss_link = filter(lambda x: x.hasAttribute('data-npc'), links)[0]
    except:
        # Not an item
        continue

    item_name = row.getElementsByTagName('td')[0].getAttribute('data-raw')
    if not(item_name.startswith('-3 ')):
        # Not an equipment
        continue

    item_name = item_name[3:]
    item_id = int(item_link.getAttribute('href').split('/')[-1])
    boss_id = int(boss_link.getAttribute('data-npc'))
    boss_name = boss_link.firstChild.data.strip()

    cells = row.getElementsByTagName('td')

    item_level = int(cells[1].firstChild.data.strip())
    difficulties = map(lambda x: RAID_DIFFICULTIES[int(x)], cells[4].getAttribute('data-raw').split(' '))

    if item_slots is not None:
        slot = item_slots[item_id]
    else:
        slot = cells[3].firstChild.data.strip()

    item_specs = []
    for class_name in row.getAttribute('class').split(' '):
        if class_name.startswith('spec-'):
            (character_class, spec) = class_name[5:].split('-')
            item_specs.append({
                'class': int(character_class),
                'spec': int(spec) - 1,
            })

    if not(boss_list.has_key(str(boss_id))):
        boss_list[str(boss_id)] = {
            'name': boss_name,
            'loot_table': [],
        }

    boss_list[str(boss_id)]['loot_table'].append({
        'id': item_id,
        'name': item_name,
        'slot': slot.lower(),
        'level': item_level,
        'difficulties': difficulties,
        'specs': item_specs,
    })


# Save the raid informations in a JSON file
json_raids = load_json_file(os.path.join(dest, 'raids.json'), [])

found = False
for raid_entry in json_raids:
    if raid_entry['name'] == raid_name:
        raid_entry['boss'] = boss_list
        found = True
        break

if not(found):
    json_raids.append({
        'name': raid_name,
        'boss': boss_list,
    })

output_file = open(os.path.join(dest, 'raids.json'), 'w')
output_file.write(json.dumps(json_raids, indent=4))
output_file.close()
