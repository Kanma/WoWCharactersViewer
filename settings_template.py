# List of all the characters to retrieve
# Format: (region, server, character, specs)
CHARACTER_NAMES = [
    ('eu', 'Khaz Modan', 'SomeCharacter', ['spec1', 'spec2']),
    ('eu', 'Khaz Modan', 'AnotherCharacter', ['spec1']),
]


LOCALE = 'fr'


# Optional function called by the script to generate some text displayed at the bottom
# of the HTML page.
#
# Comment the function to display nothing.
#
# This example returns the date and hour of the data generation.
def UPDATE_NOTICE_GENERATOR():
    import datetime

    now = datetime.datetime.now()

    return 'Generated the %s, at %s' % (now.strftime('%d %b %Y'), now.strftime('%H:%M:%S'))
