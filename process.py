#! /usr/bin/env python

import sys
import os
import json
from tools.utils import load_json_file


def item2json(item):
    if item is None:
        return None

    return {
        'id': item.id,
        'name': item.name,
        'quality': item.get_quality_name(),
        'level': item.itemLevel,
        'upgrade': item.upgrade if item.upgradable else {},
        'icon': item.get_icon_url(size='small'),
        'random_enchant': item.random_enchant,
        'enchant': item.enchant,
        'extra_socket': item.extra_socket,
        'gems': item.gems.values(),
        'set': item.set,
    }



def validate_json_file(json_data, default):
    if len(json_data['characters']) > 0:
        json_character = json_data['characters'][0]
        if not(json_character.has_key('specs')):
            return False

    if json_data['locale'] != default['locale']:
        return False

    json_data['minimum_ilevel_for_upgrades'] = default['minimum_ilevel_for_upgrades']

    return True



def item_level(item):
    if item.has_key('upgrade') and item['upgrade'].has_key('itemLevelIncrement'):
        return item['level'] - item['upgrade']['itemLevelIncrement']

    return item['level']



def decode_amr_data(data):
    data = data.split('$')

    parts = data[1].split(';')

    items = {}

    prevItemId = 0
    prevGemId = 0
    prevEnchantId = 0
    prevUpgradeId = 0
    prevBonusId = 0

    for i in xrange(14, len(parts)):
        item_string = parts[i]
        if item_string in ['', '_']:
            continue

        item_info = {
            'id': None,
            'suffix': None,
            'duplicate': None,
            'slot': i - 14,
            'upgrade': None,
            'enchant': None,
            'gems': [0, 0, 0],
            'socket_colors': [None, None, None],
            'bonus': [],
        }

        token = ''
        prop = 'i'

        j = 0
        while j <= len(item_string):
            if j < len(item_string):
                c = item_string[j]
                if c in ['-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    token += c
                    j += 1
                    continue

            val = int(token)
            if prop == 'i':
                val += prevItemId
                prevItemId = val
                item_info['id'] = val
            elif prop == 'u':
                val += prevUpgradeId
                prevUpgradeId = val
                item_info['upgrade'] = val
            elif prop == 'd':
                item_info['duplicate'] = val
            elif prop == 'f':
                item_info['suffix'] = val
            elif prop == 'b':
                val += prevBonusId
                prevBonusId = val
                item_info['bonus'].append(val)
            elif prop == 'x':
                val += prevGemId
                prevGemId = val
                item_info['gems'][0] = val
            elif prop == 'y':
                val += prevGemId
                prevGemId = val
                item_info['gems'][1] = val
            elif prop == 'z':
                val += prevGemId
                prevGemId = val
                item_info['gems'][2] = val
            elif prop == 'e':
                val += prevEnchantId
                prevEnchantId = val
                item_info['enchant'] = val
            elif prop == 'c':
                for k in xrange(len(token)):
                    item_info['socket_colors'][k] = int(token[k])

            token = ''

            if j < len(item_string):
                prop = c

            j += 1

        items[item_info['id']] = item_info

    parts = data[2].split('@')

    gems = {}
    enchants = {}

    for i in xrange(len(parts)):
        info_parts = parts[i].split('\\\\')

        if info_parts[0] == 'g':
            gem_infos = {
                'id': int(info_parts[2]),
                'enchant_id': int(info_parts[1]),
                'identical_gems': ( map(lambda x: int(x), info_parts[3].split(',')) if info_parts[3] != '' else None ),
                'text': info_parts[4].replace('_', ''),
                'identical_ids': ( map(lambda x: int(x), info_parts[5].split(',')) if info_parts[5] != '' else None ),
            }

            gems[gem_infos['enchant_id']] = gem_infos

        elif info_parts[0] == 'e':
            enchant_infos = {
                'id': int(info_parts[1]),
                'item_id': int(info_parts[2]),
                'spell_id': int(info_parts[3]),
                'text': info_parts[4].replace('_', ''),
                'materials': dict(map(lambda x: (int(x[0]), int(x[1])), map(lambda x: x.split('='), info_parts[5].split(',')))),
            }

            enchants[enchant_infos['id']] = enchant_infos

    return (items, gems, enchants)



AMR_SLOTS_ID = [
    'main_hand',
    'off_hand',
    'head',
    'neck',
    'shoulder',
    'back',
    'chest',
    'wrist',
    'hands',
    'waist',
    'legs',
    'feet',
    'finger1',
    'finger2',
    'trinket1',
    'trinket2',
]


RAID_SLOTS_NAMES = {
    'head': 'head',
    'neck': 'neck',
    'shoulder': 'shoulder',
    'chest': 'chest',
    'waist': 'waist',
    'legs': 'legs',
    'feet': 'feet',
    'wrists': 'wrist',
    'hands': 'hands',
    'back': 'back',
    'one-hand': 'main_hand',
    'two-hand': 'main_hand',
    'ranged': 'main_hand',
    'held in off-hand': 'off_hand',
    'off-hand': 'off_hand',
}


ENCHANTS = {}
REFORGES = {}



# Modify the path to be able to import the 'battlenet' library
script_path = os.path.dirname(sys.argv[0])
if os.path.exists(os.path.join(script_path, 'battlenet/battlenet/__init__.py')):
    sys.path.insert(0, os.path.join(script_path, 'battlenet'))


# battlenet importations
import battlenet
from battlenet import Connection
from battlenet import Character


# Process the command-line arguments
if (len(sys.argv) > 4) or ((len(sys.argv) > 2) and (sys.argv[1] != '--data')):
    print "Usage: %s [--data <path>] [<output_folder>]" % sys.argv[0]
    print
    sys.exit(-1)


if len(sys.argv) == 4:
    wtf_path = sys.argv[2]
    dest = sys.argv[3]
elif len(sys.argv) == 3:
    wtf_path = sys.argv[2]
    dest = './html'
elif len(sys.argv) == 2:
    wtf_path = None
    dest = sys.argv[1]
else:
    wtf_path = None
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

    if not(hasattr(settings, 'MINIMUM_ILEVEL_FOR_UPGRADES')):
        print 'No MINIMUM_ILEVEL_FOR_UPGRADES option found in the settings file'
        sys.exit(-1)
except:
    import traceback
    print 'Failed to load the settings file, reason:\n' + traceback.format_exc()
    sys.exit(-1)



# Import the data file (if one exist)
json_data = load_json_file(os.path.join(dest, 'data.json'),
                           {
                               'characters': [],
                               'items': {},
                               'locale': settings.LOCALE,
                               'minimum_ilevel_for_upgrades': settings.MINIMUM_ILEVEL_FOR_UPGRADES,
                               'raids': None,
                               'amr': False,
                           },
                           validation=validate_json_file
                    )


# Import the list of raids (if available)
json_raids = load_json_file(os.path.join(script_path, 'data/raids.json'), None)

if json_raids is not None:
    json_data['raids'] = map(lambda x: {
                                'name': x['name'],
                                'wings': x['wings']
                             }, json_raids)


# Setup the connection
Connection.setup(locale=settings.LOCALE)


# Complete the data
for (region, server, name, specs) in settings.CHARACTER_NAMES:
    try:
        print "Retrieving '%s (%s - %s)'..." % (name, server, region)
        character = Character(region, server, name,
                              fields=[Character.ITEMS, Character.TALENTS])
    except:
        print "    FAILED"
        continue


    # Known character or new one?
    json_character = filter(lambda x: x['name'] == name, json_data['characters'])
    if len(json_character) == 1:
        json_character = json_character[0]
        json_character['level'] = character.level
        json_character['max_ilvl'] = character.equipment.average_item_level

        known_specs = map(lambda x: x['name'], json_character['specs'])
        specs_to_add = filter(lambda x: x not in known_specs, specs)
        for spec in specs_to_add:
            json_spec = {
                'name': spec,
                'ilvl': None,
                'role': None,
                'icon': None,
                'items': {},
                'modifications': {},
                'valid_modifications': True,
                'amr_import_string': None,
            }

            json_character['specs'].append(json_spec)

        specs_to_remove = filter(lambda x: x['name'] not in specs, json_character['specs'])
        for spec in specs_to_remove:
            json_character['specs'].remove(spec)

    else:
        json_character = {
            'name': character.name,
            'level': character.level,
            'class': character.get_class_name(),
            'max_ilvl': character.equipment.average_item_level,
            'armory_url': 'http://%s.battle.net/wow/%s/character/%s/%s/advanced' % (region, settings.LOCALE, character.get_realm_name(), character.name),
            'specs': [],
            'raid_upgrades': None,
        }

        for spec in specs:
            json_spec = {
                'name': spec,
                'ilvl': None,
                'role': None,
                'icon': None,
                'items': {},
                'modifications': {},
                'valid_modifications': True,
                'amr_import_string': None,
            }

            json_character['specs'].append(json_spec)


        json_data['characters'].append(json_character)


    # Process the active spec
    active_talents = filter(lambda x: x.selected, character.talents)[0]
    if active_talents.name not in specs:
        print "    Active spec must not be displayed: '%s'" % active_talents.name
        continue

    json_spec = filter(lambda x: x['name'] == active_talents.name, json_character['specs'])[0]

    json_spec['role'] = active_talents.role
    json_spec['ilvl'] = character.equipment.average_item_level_equipped
    json_spec['icon'] = active_talents.get_icon_url(size='small')

    json_spec['modifications']       = {}
    json_spec['valid_modifications'] = True

    json_spec['items']['main_hand'] = item2json(character.equipment.main_hand)
    json_spec['items']['off_hand']  = item2json(character.equipment.off_hand)
    json_spec['items']['head']      = item2json(character.equipment.head)
    json_spec['items']['neck']      = item2json(character.equipment.neck)
    json_spec['items']['shoulder']  = item2json(character.equipment.shoulder)
    json_spec['items']['back']      = item2json(character.equipment.back)
    json_spec['items']['chest']     = item2json(character.equipment.chest)
    json_spec['items']['wrist']     = item2json(character.equipment.wrist)
    json_spec['items']['hands']     = item2json(character.equipment.hands)
    json_spec['items']['waist']     = item2json(character.equipment.waist)
    json_spec['items']['legs']      = item2json(character.equipment.legs)
    json_spec['items']['feet']      = item2json(character.equipment.feet)
    json_spec['items']['finger1']   = item2json(character.equipment.finger1)
    json_spec['items']['finger2']   = item2json(character.equipment.finger2)
    json_spec['items']['trinket1']  = item2json(character.equipment.trinket1)
    json_spec['items']['trinket2']  = item2json(character.equipment.trinket2)


    # Process the raid loot tables (if available)
    if json_raids is not None:
        json_upgrades = []

        spec1 = character.talents[0]._data['spec']['order']

        try:
            spec2 = character.talents[1]._data['spec']['order']
        except:
            spec2 = -1

        for json_raid_infos in json_raids:
            json_upgrade = {
                'raid': json_raid_infos['name'],
                'boss': [],
            }

            for boss_id, json_boss_infos in json_raid_infos['boss'].items():
                json_boss = {
                    'id': int(boss_id),
                    'name': json_boss_infos['name'],
                    'loot_tables': {
                        'lfr': [],
                        'flex': [],
                        'normal': [],
                        'heroic': [],
                    }
                }

                for json_item_infos in json_boss_infos['loot_table']:
                    for json_spec_infos in json_item_infos['specs']:
                        if (json_spec_infos['class'] != character.class_) or \
                           ((json_spec_infos['spec'] != spec1) and (json_spec_infos['spec'] != spec2)):
                            continue

                        spec_name = character.talents[0].name if json_spec_infos['spec'] == spec1 else character.talents[1].name

                        try:
                            json_spec_ref = filter(lambda x: x['name'] == spec_name, json_character['specs'])[0]
                        except:
                            continue

                        if json_spec_ref['ilvl'] is None:
                            continue

                        slots = []
                        if json_item_infos['slot'] == 'trinket':
                            item1 = json_spec_ref['items']['trinket1']
                            item2 = json_spec_ref['items']['trinket2']

                            if item1 is None:
                                if item2 is None:
                                    slots.append('trinket1')
                                elif item2['id'] != json_item_infos['id']:
                                    slots.append('trinket1')

                            else:
                                if item2 is None:
                                    if item2['id'] != json_item_infos['id']:
                                        slots.append('trinket2')
                                elif (item1['id'] != json_item_infos['id']) and (item2['id'] != json_item_infos['id']):
                                    if item_level(item2) > item_level(item1):
                                        if json_item_infos['level'] > item_level(item1):
                                            slots.append('trinket1')
                                    else:
                                        if json_item_infos['level'] > item_level(item2):
                                            slots.append('trinket2')

                        elif json_item_infos['slot'] == 'finger':
                            item1 = json_spec_ref['items']['finger1']
                            item2 = json_spec_ref['items']['finger2']

                            if item1 is None:
                                if item2 is None:
                                    slots.append('finger1')
                                elif item2['id'] != json_item_infos['id']:
                                    slots.append('finger1')

                            else:
                                if item2 is None:
                                    if item2['id'] != json_item_infos['id']:
                                        slots.append('finger2')
                                elif (item1['id'] != json_item_infos['id']) and (item2['id'] != json_item_infos['id']):
                                    if item_level(item2) > item_level(item1):
                                        if json_item_infos['level'] > item_level(item1):
                                            slots.append('finger1')
                                    else:
                                        if json_item_infos['level'] > item_level(item2):
                                            slots.append('finger2')

                        elif json_item_infos['slot'] == 'consumable':
                            slots.append('consumable')

                        else:
                            item = json_spec_ref['items'][RAID_SLOTS_NAMES[json_item_infos['slot']]]
                            if (item is None) or (json_item_infos['level'] > item_level(item)):
                                slots.append(RAID_SLOTS_NAMES[json_item_infos['slot']])

                        for slot in slots:
                            json_item = {
                                'id': json_item_infos['id'],
                                'name': json_item_infos['name'],
                                'level': json_item_infos['level'],
                                'spec': spec_name,
                                'slot': slot,
                            }

                            if 'lfr' in json_item_infos['difficulties']:
                                json_boss['loot_tables']['lfr'].append(json_item)
                            elif 'flex' in json_item_infos['difficulties']:
                                json_boss['loot_tables']['flex'].append(json_item)
                            elif 'normal 10' in json_item_infos['difficulties']:
                                json_boss['loot_tables']['normal'].append(json_item)
                            elif 'heroic 10' in json_item_infos['difficulties']:
                                json_boss['loot_tables']['heroic'].append(json_item)

                json_upgrade['boss'].append(json_boss)

            json_upgrades.append(json_upgrade)

        json_character['raid_upgrades'] = json_upgrades


    # Process AskMrRobot's data
    if wtf_path is not None:
        path = os.path.join(wtf_path, server, name, 'SavedVariables', 'AskMrRobot.lua')
        if os.path.exists(path):
            file = open(path, 'r')
            lines = file.readlines()
            file.close()

            json_data['amr'] = True

            import_data = filter(lambda x: x.startswith('\t["LastCharacterImport"] = '), lines)
            if (len(import_data) == 1) and (len(import_data[0].strip()[27:-2]) > 0):
                import_data = import_data[0].strip()[27:-2]

                json_spec['amr_import_string'] = import_data

                (amr_items, amr_gems, amr_enchants) = decode_amr_data(import_data)

                for (item_id, item_infos) in amr_items.items():

                    item = None
                    for slot_name in AMR_SLOTS_ID:
                        item = getattr(character.equipment, slot_name)
                        if (item is not None) and (item_id == item.id):
                            break
                        else:
                            item = None

                    if item is not None:
                        if item_id != item.id:
                            print item_id, item.id
                            json_spec['valid_modifications'] = False
                            break

                        modifs = {
                            'gems': [None] * len(item_infos['gems']),
                            'enchant': None,
                        }

                        for index, gem in enumerate(item_infos['gems']):
                            if gem == 0:
                                continue

                            gem_id = amr_gems[gem]['id']

                            if gem_id != item.gems[index]:
                                if not(json_data['items']).has_key(str(gem_id)):
                                    print "    Retrieving gem #%d..." % gem_id
                                    connection = Connection()
                                    json_gem = connection.get_item(region, gem_id)
                                    if json_gem is not None:
                                        json_data['items'][str(gem_id)] = json_gem
                                        print "        %s" % json_gem['name'].encode('utf-8')
                                    else:
                                        json_data['items'][str(gem_id)] = None
                                        print "        FAILED"

                                modifs['gems'][index] = gem_id

                        if (item_infos['enchant'] is not None) and (item_infos['enchant'] != item.enchant):
                            enchant_id = amr_enchants[item_infos['enchant']]['item_id']

                            if not(json_data['items']).has_key(str(enchant_id)):
                                print "    Retrieving enchant #%d..." % enchant_id
                                connection = Connection()
                                json_enchant = connection.get_item(region, enchant_id)
                                if json_enchant is not None:
                                    json_data['items'][str(enchant_id)] = json_enchant
                                    print "        %s" % json_enchant['name'].encode('utf-8')
                                else:
                                    json_data['items'][str(enchant_id)] = None
                                    print "        FAILED"

                            modifs['enchant'] = enchant_id

                        json_spec['modifications'][slot_name] = modifs
            else:
                json_spec['valid_modifications'] = False


# Generate the JSON file
output_file = open(os.path.join(dest, 'data.json'), 'w')
output_file.write(json.dumps(json_data, indent=4))
output_file.close()
