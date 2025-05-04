from openai import OpenAI
import json
from key import api_key
import re
import subprocess
# from sample_code import code2

# Step 1: Read the input file
with open('mycode.txt', 'r', encoding='utf-8') as file:
    code2 = file.read()

client = OpenAI(api_key = api_key)

file = client.files.create(
    file=open("results\dwr_architecture_summary.pdf", "rb"),
    purpose="user_data"
)

response = client.responses.create(
    model="gpt-4o-mini",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "file_id": file.id,
                },
                {
                    "type": "input_text",
                    "text": f"Only Write a complete python code which converts this JSON into DWR. The input JSON will be on path 'results/json1.json'. Also save the output on path 'results\dwr_output.txt'. Here is a sample python code {code2}. And JSON is provided in file given to you",
                },
            ]
        }
    ]
)
response_text=response.output_text
print(response_text)

# Regex to extract the python code
match = re.search(r"```(?:python)?\n(.*?)```", response_text, re.DOTALL)

if match:
    code_only = match.group(1)
    print(code_only)
    # Save it to a new .py file
    with open("extract_code_only.py", "w") as f:
        f.write(code_only)

else:
    print("No code block found.")


# print("\n--- Running extract_code_only.py ---\n")
# Run the newly created file
subprocess.run(["python", "extract_code_only.py"], check=True)


print(f"Only Write a complete python code which converts this JSON into DWR. Here is a sample python code that convert the provided type of JSON to DWR. Here is python sample code")