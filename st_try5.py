import streamlit as st
import re
import json
import os
from urllib.parse import unquote

# Create results folder if it doesn't exist
os.makedirs("results", exist_ok=True)

st.title("DWR File Processor")

uploaded_file = st.file_uploader("Upload your sltemplate.txt file", type="txt")

if uploaded_file is not None:
    try:
        # Step 1: Read the input file
        fetch_code = uploaded_file.read().decode('utf-8')

        # Extract "body"
        match = re.search(r'"body"\s*:\s*"([^"]*)"', fetch_code)

        if match:
            body_value = match.group(1)
            body_value = body_value.replace("\\n", "\n")
            
            with open('newoutput.txt', 'w', encoding='utf-8') as out_file:
                out_file.write(body_value)
        else:
            st.error("No 'body' found in the uploaded file.")
            st.stop()

        with open("newoutput.txt", "r", encoding="utf-8") as f:
            raw_data = f.read()

        all_lines = raw_data.strip().splitlines()

        top_metadata = {}
        bottom_params = {}
        main_body_lines = []

        for line in all_lines:
            if re.match(r'^(callCount|page|httpSessionId|scriptSessionId|c0-scriptName|c0-methodName|c0-id)=', line):
                key, value = line.split("=", 1)
                top_metadata[key] = unquote(value)
            elif re.match(r'^c0-param\d+=', line) or re.match(r'^batchId=', line):
                key, value = line.split("=", 1)
                bottom_params[key] = value
            else:
                main_body_lines.append(line)

        lines = re.findall(r'(c0-e\d+)=([^\n]+)', "\n".join(main_body_lines))

        raw_nodes = {}
        for key, value in lines:
            if value.startswith("string:"):
                raw_nodes[key] = unquote(value[7:])
            elif value.startswith("number:"):
                raw_nodes[key] = float(value[7:]) if '.' in value else int(value[7:])
            elif value.startswith("boolean:"):
                raw_nodes[key] = value[8:] == "true"
            elif value.startswith("null:null"):
                raw_nodes[key] = None
            elif value.startswith("reference:"):
                raw_nodes[key] = {"$ref": value[9:]}
            elif value.startswith("Array:["):
                refs = re.findall(r'reference:(c0-e\d+)', value)
                raw_nodes[key] = [{"$ref": ref} for ref in refs]
            elif value.startswith("Object_Object:{"):
                obj_str = value[len("Object_Object:{"):-1]
                obj_pairs = re.findall(r'(\w+):reference:(c0-e\d+)', obj_str)
                raw_nodes[key] = {k: {"$ref": v} for k, v in obj_pairs}
            else:
                raw_nodes[key] = value

        resolved_nodes = {}
        visited = {}

        def resolve(obj):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref = obj["$ref"]
                    if ref in visited:
                        return visited[ref]
                    if ref in raw_nodes:
                        resolved = resolve(raw_nodes[ref])
                        if isinstance(resolved, dict):
                            resolved["__ref__"] = ref
                        visited[ref] = resolved
                        return resolved
                    else:
                        return {"error": f"Unresolved reference: {ref}", "__ref__": ref}
                else:
                    return {k: resolve(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve(item) for item in obj]
            else:
                return obj

        for node_id in raw_nodes:
            resolved = resolve(raw_nodes[node_id])
            if isinstance(resolved, dict):
                resolved["__ref__"] = node_id
            resolved_nodes[node_id] = resolved

        final_output = {
            "top_metadata": top_metadata,
            "resolved_nodes": resolved_nodes,
            "bottom_params": bottom_params
        }

        # Save full output
        with open("all_nodes_resolved_with_meta.json", "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        with open("results/json1.json", "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        # Create a preview summary
        preview_nodes = {k: resolved_nodes[k] for k in list(resolved_nodes.keys())[:5]}
        preview_nodes["..."] = "..."

        summary_json = {
            "top_metadata": top_metadata,
            "resolved_nodes": preview_nodes,
            "bottom_params": bottom_params
        }

        with open("results/dwr_architecture_summary.pdf", "w", encoding="utf-8") as f:
            json.dump(summary_json, f, indent=2, ensure_ascii=False)

        st.success("✅ Files saved successfully!")

    except Exception as e:
        st.error(f"Error occurred: {e}")
