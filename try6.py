import json
from urllib.parse import quote

# Load full structured JSON with top, resolved, and bottom data
with open("all_nodes_resolved_with_meta.json", "r", encoding="utf-8") as f:
    full_data = json.load(f)

top_metadata = full_data["top_metadata"]
all_nodes = full_data["resolved_nodes"]
bottom_params = full_data["bottom_params"]

node_map = {}  # Holds serialized lines
temp_counter = 10000  # For assigning temp IDs to new values

def assign_temp_id(val):
    global temp_counter
    temp_counter += 1
    return f"c0-e{temp_counter}"

def serialize(value, node_id):
    if node_id in node_map:
        return node_id

    if isinstance(value, str):
        node_map[node_id] = f"string:{quote(value)}"
    elif isinstance(value, bool):
        node_map[node_id] = f"boolean:{str(value).lower()}"
    elif isinstance(value, int) or isinstance(value, float):
        node_map[node_id] = f"number:{value}"
    elif value is None:
        node_map[node_id] = "null:null"
    elif isinstance(value, list):
        refs = []
        for item in value:
            if isinstance(item, dict) and "__ref__" in item:
                ref_id = item["__ref__"]
            else:
                ref_id = assign_temp_id(item)
            serialize(item, ref_id)
            refs.append(f"reference:{ref_id}")
        node_map[node_id] = f"Array:[{','.join(refs)}]"
    elif isinstance(value, dict):
        refs = []
        for k, v in value.items():
            if k == "__ref__":
                continue
            if isinstance(v, dict) and "__ref__" in v:
                ref_id = v["__ref__"]
            else:
                ref_id = assign_temp_id(v)
            serialize(v, ref_id)
            refs.append(f"{k}:reference:{ref_id}")
        node_map[node_id] = f"Object_Object:{{{','.join(refs)}}}"
    else:
        raise TypeError(f"Unsupported type: {type(value)}")

    return node_id

# Step 1: Serialize all resolved nodes
for node_id, content in all_nodes.items():
    serialize(content, node_id)

# Step 2: Write back to DWR format
with open("full_reconstructed_with_meta.dwr.txt", "w", encoding="utf-8") as f:
    # Write top metadata
    for key in top_metadata:
        f.write(f"{key}={top_metadata[key]}\\n")

    # Write all DWR content nodes
    def sort_key(k): return int(k.split("-e")[-1])
    for key in sorted(node_map, key=sort_key):
        f.write(f"{key}={node_map[key]}\\n")

    # Write bottom params
    for key, value in bottom_params.items():
        f.write(f"{key}={value}\\n")

# Step 2: Write back to DWR format
with open("full_reconstructed_with_meta.dwr.pdf", "w", encoding="utf-8") as f:
    # Write top metadata
    for key in top_metadata:
        f.write(f"{key}={top_metadata[key]}\\n")

    # Write only the first 5 DWR content nodes
    def sort_key(k): return int(k.split("-e")[-1])
    sorted_keys = sorted(node_map, key=sort_key)
    for key in sorted_keys[:5]:
        f.write(f"{key}={node_map[key]}\\n")

    # Write bottom params
    for key, value in bottom_params.items():
        f.write(f"{key}={value}\\n")


print("Full DWR with metadata and parameters saved to full_reconstructed_with_meta.dwr.txt")
