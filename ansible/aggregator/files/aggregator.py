import json
import glob
import os
from datetime import datetime

def deep_merge(source, destination):
    """
    Recursively merges source dict into destination dict.
    This ensures that if multiple files have the same top-level node name,
    their internal tests and errors are combined rather than overwritten.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # If the key is a dictionary, grab it from destination (or create an empty one) and recurse
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        elif isinstance(value, list):
            # If it's a list (like your 'failures' array), combine them
            if key in destination and isinstance(destination[key], list):
                destination[key].extend(value)
            else:
                destination[key] = value
        else:
            # Overwrite simple string/int values (like error messages or status codes)
            destination[key] = value
    return destination

def aggregate_jsons():
    # Set up paths
    output_dir = "/var/tmp/aggregator"
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%min")
    output_file = os.path.join(output_dir, f"aggregator-{timestamp}.json")

    # Ensure directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    final_data = {}
    search_pattern = "*/files/logs/*.json" 
    
    found_files = glob.glob(search_pattern)

    print(f"DEBUG: Found {len(found_files)} files matching '{search_pattern}'")

    if not found_files:
        print("WARNING: No JSON files were found. Check your search_pattern.")
        return

    for filename in found_files:
        if "aggregator-" in filename:
            continue
            
        with open(filename, 'r') as f:
            try:
                data = json.load(f)
                # Deep merge the data directly into final_data
                deep_merge(data, final_data)
            except json.JSONDecodeError:
                print(f"WARNING: Could not parse JSON in {filename}. Skipping.")
                continue

    with open(output_file, 'w') as f:
        json.dump(final_data, f, indent=4)

    # Count top-level keys to show how many unique nodes were aggregated
    print(f"Successfully aggregated data for {len(final_data.keys())} unique nodes into {output_file}")

if __name__ == "__main__":
    aggregate_jsons()
