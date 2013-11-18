import json
import sys
import os


def load_json_file(path, default={}, validation=None):
    json_data = None
    if os.path.exists(path):
        file = open(path, 'r')
        json_data = json.load(file)
        file.close()

        if (validation is not None) and not(validation(json_data, default)):
            json_data = None

    if json_data is None:
        json_data = default

    return json_data
