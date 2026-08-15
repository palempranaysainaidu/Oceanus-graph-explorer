from collections import defaultdict
import csv

input_file = "backend-maps/argo_data.csv"
output_file = "backend-maps/argo_data_sample.csv"

floats = defaultdict(list)
total_before = 0

with open(input_file, newline="", encoding="utf-8") as f:
    # Get headers and units row
    raw_reader = csv.reader(f)
    headers = next(raw_reader)
    units_row = next(raw_reader)

    f.seek(0)
    dict_reader = csv.DictReader(f)
    next(dict_reader) # skip units
    
    for row in dict_reader:
        total_before += 1
        platform = row["platform_number"]
        time_str = row["time"]
        if not time_str or time_str == "UTC":
            continue
        date = time_str[:10]
        
        # Check if we already have this date for this float
        # (This is O(N) per float, but lists are short since we keep 1 per day)
        if not any(r["time"][:10] == date for r in floats[platform]):
            floats[platform].append(row)

total_after = sum(len(v) for v in floats.values())

retained_rows = []
if total_after > 10000:
    # Cap to 10,000 while ensuring every float is retained
    idx = 0
    while len(retained_rows) < 10000:
        added_in_round = False
        for p, rows in floats.items():
            if idx < len(rows):
                retained_rows.append(rows[idx])
                added_in_round = True
                if len(retained_rows) == 10000:
                    break
        if not added_in_round:
            break
        idx += 1
else:
    retained_rows = [r for rows in floats.values() for r in rows]

unique_floats = len(set(r["platform_number"] for r in retained_rows))

print(f"Total floats retained: {unique_floats}")
print(f"Total rows before: {total_before}")
print(f"Total rows after downsampling: {len(retained_rows)}")

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    units_dict = {h: u for h, u in zip(headers, units_row)}
    writer.writerow(units_dict)
    for row in retained_rows:
        writer.writerow(row)
