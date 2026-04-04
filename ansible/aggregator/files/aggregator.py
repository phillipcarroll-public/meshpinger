import json
import glob
import os
from datetime import datetime

def aggregate_jsons():
    # Set up paths
    output_dir = "/var/tmp/aggregator"
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%min")
    output_file = os.path.join(output_dir, f"aggregator-{timestamp}.json")

    # Ensure directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # We will use a dictionary, but key the data by filename to prevent overwrites
    final_data = {}
    
    # Updated pattern: Looks in all immediate subdirectories (e.g., aggregator, node1)
    # If your folders are actually inside a 'roles' folder, change this back to "roles/*/files/logs/*.json"
    search_pattern = "*/files/logs/*.json" 
    
    found_files = glob.glob(search_pattern)

    # Debug print to verify files are actually being found
    print(f"DEBUG: Found {len(found_files)} files matching '{search_pattern}'")

    if not found_files:
        print("WARNING: No JSON files were found. Check your search_pattern and current directory.")
        return

    for filename in found_files:
        # Skip the output file if it accidentally gets caught in the glob
        if "aggregator-" in filename:
            continue
            
        with open(filename, 'r') as f:
            try:
                data = json.load(f)
                # Store the data under its filename so nodes don't overwrite each other's keys
                # e.g. final_data["node1/files/logs/ping.json"] = { ... }
                final_data[filename] = data
            except json.JSONDecodeError:
                print(f"WARNING: Could not parse JSON in {filename}. Skipping.")
                continue

    with open(output_file, 'w') as f:
        json.dump(final_data, f, indent=4)

    print(f"Successfully aggregated {len(final_data)} files into {output_file}")

if __name__ == "__main__":
    aggregate_jsons()
