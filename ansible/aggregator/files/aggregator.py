import json
import glob
import os
import re
from datetime import datetime

def deep_merge(source, destination):
    """Recursively merges source dict into destination dict."""
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value
    return destination

def is_valid_modern_format(data, test_key):
    """Checks if the JSON contains the 'status' key for the specific test."""
    try:
        for hostname in data:
            tests = data[hostname].get("tests", {})
            test_entry = tests.get(test_key, {})
            for timestamp in test_entry:
                if "status" in test_entry[timestamp]:
                    return True
    except:
        return False
    return False

def get_latest_files(found_files):
    """Groups files by Node and Type, returning only the newest valid ones."""
    latest_map = {}

    # Map the middle-part of the filename to the actual key inside the JSON
    json_key_map = {
        "pingtest": "backendpingtest",
        "eterrors": "ethtool_errors",
        "pciedegraded": "pciedegraded"
    }

    for filepath in found_files:
        filename = os.path.basename(filepath)
        if "aggregator-" in filename or not filename.endswith(".json"):
            continue

        # Regex explanation:
        # (.+?) -> Match hostname (non-greedy)
        # -(pingtest|eterrors|pciedegraded)- -> Match one of our known types
        # (\d{8}-\d{4}) -> Match the timestamp
        match = re.match(r"(.+?)-(pingtest|eterrors|pciedegraded)-(\d{8}-\d{4})\.json", filename)

        if not match:
            continue

        node_name = match.group(1)
        category = match.group(2)
        test_key = json_key_map.get(category, category)

        # Validate the JSON content before adding to the list
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if not is_valid_modern_format(data, test_key):
                    continue
        except:
            continue

        mtime = os.path.getmtime(filepath)
        group_key = (node_name, category)

        if group_key not in latest_map or mtime > latest_map[group_key]['mtime']:
            latest_map[group_key] = {'path': filepath, 'mtime': mtime}

    return [info['path'] for info in latest_map.values()]

def aggregate_jsons():
    # Keep your original portable output and search paths
    output_dir = "/var/tmp/aggregator"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp_str = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_file = os.path.join(output_dir, f"aggregator-{timestamp_str}.json")

    # Portable search pattern
    search_pattern = "*/files/logs/*.json"
    all_files = glob.glob(search_pattern)

    print(f"DEBUG: Found {len(all_files)} total files using pattern '{search_pattern}'")

    files_to_process = get_latest_files(all_files)
    print(f"DEBUG: Processing {len(files_to_process)} latest unique test files.")

    final_data = {}
    for filename in files_to_process:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                deep_merge(data, final_data)
        except:
            continue

    with open(output_file, 'w') as f:
        json.dump(final_data, f, indent=4)

    print(f"Successfully aggregated {len(final_data)} unique nodes into {output_file}")

if __name__ == "__main__":
    aggregate_jsons()
