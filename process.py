#! /usr/bin/env python

import sys
import os
import json


def item2json(item):
    if item is None:
        return None

    return {
        'id': item.id,
        'name': item.name,
        'quality': item.get_quality_name(),
        'level': item.itemLevel,
        'icon': item.get_icon_url(size='small'),
    }


# Modify the path to be able to import the 'battlenet' library
script_path = os.path.dirname(sys.argv[0])
if os.path.exists(os.path.join(script_path, 'battlenet/battlenet/__init__.py')):
    sys.path.insert(0, os.path.join(script_path, 'battlenet'))


# battlenet importations
import battlenet
from battlenet import Connection
from battlenet import Character


# Process the command-line arguments
if (len(sys.argv) != 1) and (len(sys.argv) != 2):
    print "Usage: %s [<output_folder>]" % sys.argv[0]
    print
    sys.exit(-1)


if len(sys.argv) == 2:
    dest = sys.argv[1]
else:
    dest = './html'

dest = os.path.abspath(dest)


# Try to import the user's custom settings
try:
    settings = __import__('settings')

    if not(hasattr(settings, 'CHARACTER_NAMES')):
        print 'No CHARACTER_NAMES option found in the settings file'
        sys.exit(-1)

    if not(hasattr(settings, 'LOCALE')):
        print 'No LOCALE option found in the settings file'
        sys.exit(-1)
except:
    import traceback
    print 'Failed to load the settings file, reason:\n' + traceback.format_exc()
    sys.exit(-1)


# Setup the connection
Connection.setup(locale=settings.LOCALE)


# Retrieve the data
json_data = {
    'characters': [],
    'locale': settings.LOCALE,
}

for (region, server, name) in settings.CHARACTER_NAMES:
    try:
        character = Character(region, server, name,
                              fields=[Character.ITEMS, Character.TALENTS])
    except:
        print "Failed to retrieve the character '%s' on server '%s (%s)'" % (name, server, region)
        continue

    json_character = {
        'name': character.name,
        'class': character.get_class_name(),
        'current_ilvl': character.equipment.average_item_level_equipped,
        'max_ilvl': character.equipment.average_item_level,
        'armory_url': 'http://%s.battle.net/wow/%s/character/%s/%s/advanced' % (region, settings.LOCALE, character.get_realm_name(), character.name),
        'role': None,
        'spec_icon': None,
        'items': {},
    }

    active_talents = filter(lambda x: x.selected, character.talents)[0]

    json_character['role'] = active_talents.role
    json_character['spec_icon'] = active_talents.get_icon_url(size='small')

    json_character['items']['main_hand'] = item2json(character.equipment.main_hand)
    json_character['items']['off_hand']  = item2json(character.equipment.off_hand)
    json_character['items']['head']      = item2json(character.equipment.head)
    json_character['items']['neck']      = item2json(character.equipment.neck)
    json_character['items']['shoulder']  = item2json(character.equipment.shoulder)
    json_character['items']['back']      = item2json(character.equipment.back)
    json_character['items']['chest']     = item2json(character.equipment.chest)
    json_character['items']['wrist']     = item2json(character.equipment.wrist)
    json_character['items']['hands']     = item2json(character.equipment.hands)
    json_character['items']['waist']     = item2json(character.equipment.waist)
    json_character['items']['legs']      = item2json(character.equipment.legs)
    json_character['items']['feet']      = item2json(character.equipment.feet)
    json_character['items']['finger1']   = item2json(character.equipment.finger1)
    json_character['items']['finger2']   = item2json(character.equipment.finger2)
    json_character['items']['trinket1']  = item2json(character.equipment.trinket1)
    json_character['items']['trinket2']  = item2json(character.equipment.trinket2)

    json_data['characters'].append(json_character)


# Generate the HTML page
output_file = open(os.path.join(dest, 'data.json'), 'w')
output_file.write(json.dumps(json_data, indent=4))
output_file.close()
