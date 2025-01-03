import openai
import pandas as pd
import json
import streamlit as st

# Load API key securely
api_key = st.secrets["openai"]["api_key"]

# Set OpenAI API key
openai.api_key = api_key

# Load extracted data
DATA_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/combined_aortic_stenosis.csv"
OUTPUT_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/pre_summarized_findings.json"

data = pd.read_csv(DATA_PATH)

# Define the summarization function
def summarize_entry(entry):
    # Retrieve the OpenAI API key from Streamlit secrets
    api_key = st.secrets["openai"]["api_key"]

    # Set the OpenAI API key
    openai.api_key = api_key

    # Build the prompt for the LLM
    prompt = (
        f"Summarize the following physical exam finding with diagnostic values and instructions:\n\n"
        f"Finding: {entry['content']}\n\n"
        "Provide:\n"
        "1. Maneuver name\n"
        "2. Diagnostic value (sensitivity, specificity, likelihood ratios)\n"
        "3. How to perform the maneuver."
    )

    try:
        # Query the LLM
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a physician summarizing physical exam maneuvers for educational purposes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        # Extract and return the response content
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error summarizing entry: {e}")
        return None


summarized_findings = []
for _, row in data.iterrows():
    if pd.notna(row['content']):
        summary = summarize_entry(row)
        if summary:
            summarized_findings.append({"type": row["type"], "content": row["content"], "summary": summary})

# Save summarized findings
with open(OUTPUT_PATH, "w") as f:
    json.dump(summarized_findings, f, indent=4)

print(f"Summarized findings saved to {OUTPUT_PATH}")