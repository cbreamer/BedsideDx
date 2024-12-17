import os  # Used for accessing environment variables like our secret OpenAI API key.
from openai import OpenAI
import openai  # Import the OpenAI library to interact with the API
import streamlit as st  # Streamlit library for creating web apps

api_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = api_key

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=api_key)

def recommend_exam_maneuvers(clinical_note):
    prompt = f"""
    Based on the following clinical note, recommend relevant physical exam maneuvers. 
    Include:
    1. The name of the maneuver.
    2. A brief description of how to perform it.
    3. The purpose of the maneuver.

    Clinical note: "{clinical_note}"
    """
    
    # Call OpenAI API (GPT-4)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a medical assistant specialized in recommending physical exam maneuvers."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.5
    )
    
    return response['choices'][0]['message']['content']

# Title of the app
st.title("Enhancing Bedside Diagnosis")

st.title("Physical Exam Maneuver Recommender")
st.write("Enter a clinical note to get recommended physical exam maneuvers.")

# Text input for clinical note
clinical_note = st.text_area("Clinical Note", placeholder="Enter clinical note here...")

# Submit button
if st.button("Recommend Maneuvers"):
    if clinical_note:
        with st.spinner("Analyzing..."):
            # Get recommendation from GPT-4
            exam_maneuvers = recommend_exam_maneuvers(clinical_note)
            st.success("Here are the recommended physical exam maneuvers:")
            st.markdown(exam_maneuvers)
    else:
        st.warning("Please enter a clinical note.")

# Footer
st.write("---")
st.caption("Powered by OpenAI GPT-4 and Streamlit.")
