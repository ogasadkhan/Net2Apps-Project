import streamlit as st
from openai import OpenAI
import json
import os
import re
import subprocess
from key import api_key

st.title("DWR Code Generator")

uploaded_file = st.file_uploader("Upload your mycode.txt file", type="json")

if uploaded_file is not None:
    try:
        # Save uploaded mycode.txt temporarily
        # with open('mycode.txt', 'w', encoding='utf-8') as f:
        #     f.write(uploaded_file.read().decode('utf-8'))

        # Read the uploaded mycode.txt
        with open('mycode.txt', 'r', encoding='utf-8') as file:
            code2 = file.read()

        client = OpenAI(api_key=api_key)

        # Upload static PDF
        file_upload = client.files.create(
            file=open("results/dwr_architecture_summary.pdf", "rb"),
            purpose="user_data"
        )

        # Send request to OpenAI
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "file_id": file_upload.id,
                        },
                        {
                            "type": "input_text",
                            "text": f"Only Write a complete python code which converts this JSON into DWR. The input JSON will be on path 'results/json1.json'. Also save the output on path 'results/dwr_output.txt'. Here is a sample python code {code2}. And JSON is provided in file given to you",
                        },
                    ]
                }
            ]
        )

        response_text = response.output_text

        # Extract python code from markdown block
        match = re.search(r"```(?:python)?\n(.*?)```", response_text, re.DOTALL)

        if match:
            code_only = match.group(1)

            # Save extracted code
            with open("extract_code_only.py", "w", encoding='utf-8') as f:
                f.write(code_only)

            # Run the newly created Python file
            subprocess.run(["python", "extract_code_only.py"], check=True)

            st.success("✅ DWR file created successfully!")
        else:
            st.error("No Python code block found in the OpenAI response.")

    except Exception as e:
        st.error(f"Error occurred: {e}")
