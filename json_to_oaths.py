import json
import sys
import csv


def normalize_dict(d):
    result = {}
    for k, v in d.items():
        # if k is swearer, swearee, gods_invoked, or proposed_by,
        # gather the results
        # build a case statement to handle the different keys
        if k == "swearer":
            result["swearer"] = "; ".join([d["agent"] for d in v])
        elif k == "swearee":
            result["swearee"] = "; ".join([d["agent"] for d in v])
        elif k == "gods_invoked":
            result["gods_invoked"] = "; ".join(v)
        elif k == "proposed_by":
            result["proposed_by"] = "; ".join(v)
        else:
            result[k] = v

    return result


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


# read stdin one by one
oaths = []
for line in sys.stdin:
    # read the line as JSON
    oath = json.loads(line)
    # normalize the dictionary
    normalized_oath = normalize_dict(oath)
    oaths.append(normalized_oath)

# write the normalized oaths to stdout
convert_to_csv(oaths, "oaths.csv")
