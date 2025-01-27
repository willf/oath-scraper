import json
import sys
import csv


def convert_to_csv(data, csv_file_path):
    if not data:
        return

    # Extract headers from the first dictionary
    headers = data[0].keys()

    with open(csv_file_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def unique_dicts_by_key(dicts, key):
    seen = set()
    unique_dicts = []
    for d in dicts:
        value = d[key]
        if value not in seen:
            seen.add(value)
            unique_dicts.append(d)
    return unique_dicts


agents = []
for line in sys.stdin:
    # read the line as JSON
    oath = json.loads(line)
    oath_id = oath.get("oath_id", None)
    if not oath_id:
        continue
    swearers = oath.get("swearer", [])
    swearees = oath.get("swearee", [])
    if not swearers:
        sys.stderr.write(f"No swearers in {oath_id}\n")
    if not swearees:
        sys.stderr.write(f"No swearees in {oath_id}\n")
    agents.extend(swearers)
    agents.extend(swearees)

uniq_agents = unique_dicts_by_key(agents, "agent")
convert_to_csv(uniq_agents, "agents.csv")
