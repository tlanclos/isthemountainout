import json

with open('mountain-history.classifications.json') as f:
    data = json.load(f)

new_data = {}
for key, values in data.items():
    new_data[key.replace(':', '_')] = values

with open('mountain-history.classifications.json', 'w') as f:
    json.dump(new_data, f)
