import streamlit as st
from openai import OpenAI
import pandas as pd

# Load the API key from Streamlit secrets
api_key = st.secrets["openai"]["api_key"]

# Create OpenAI client
client = OpenAI(api_key=api_key)

# Path to physical exam CSV file
EXAM_TABLE_PATH = "Extracted_phys_exam.csv"

# Function to get relevant conditions
def get_relevant_conditions(clinical_note, conditions_list):
     
    prompt = f"""
You are a physician. Your task is to extract relevant conditions from the provided clinical note.

**Instructions:**
1. Return only a comma-separated list of conditions from the list provided below. Do not include any commentary or additional text.
2. Ensure the conditions are directly relevant to the clinical note.

**Clinical Note:**
{clinical_note}

**Conditions List:**
{', '.join(conditions_list)}

**Output Format:**
Condition1, Condition2, Condition3
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a physician extracting relevant conditions from a clinical note."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        message_content = response.choices[0].message.content
        relevant_conditions = [condition.strip() for condition in message_content.split(",") if condition.strip()]
        return relevant_conditions
    except Exception as e:
        st.error(f"Error extracting conditions from GPT: {e}")
        return []

# Function to generate a sample clinical note
def generate_sample_note(selected_conditions):
    if not selected_conditions:
        return "No conditions selected."

    conditions_str = ", ".join(selected_conditions)
    prompt = f"""
Generate a sample clinical note for a patient with the following symptoms and/or condition(s) in the differential diagnosis: {conditions_str}.
The note should include:
1. Chief complaint
2. History of present illness (HPI)
3. Relevant past medical history (PMH)
4. Review of systems (ROS)
5. Physical exam findings, including vital signs
6. Lab and imaging findings
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a physician creating sample clinical notes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating sample note: {e}"

# Function to load the exam table
def load_exam_table():
    try:
        return pd.read_csv(EXAM_TABLE_PATH)
    except Exception as e:
        st.error(f"Error loading table: {e}")
        return pd.DataFrame()

# Function to generate recommendations
def generate_recommendations(clinical_note, relevant_conditions, filtered_table=None, extracted_text=None):
    table_str = ""
    if filtered_table is not None and not filtered_table.empty:
        for _, row in filtered_table.iterrows():
            table_str += (
                f"**Physical exam maneuver**: {row['Physical exam maneuver']}\n"
                f"**Finding**: {row['Finding']}\n"
                f"- Sensitivity (%): {row['Sensitivity (%)']}\n"
                f"- Specificity (%): {row['Specificity (%)']}\n"
                f"- LR+: {row['LR+']}\n"
                f"- LR-: {row['LR-']}\n"
                f"- Context: {row['Context']}\n"
                f"- Condition: {row['Condition']}\n\n"
            )
    else:
        table_str = "No relevant exam maneuvers found."

    # Prompt for GPT
    prompt = f"""
Using the following information, identify and prioritize the most relevant specialized physical exam maneuvers for the patient. Provide step-by-step instructions, positive/negative findings, relevant statistics (sensitivity, specificity, LR+/-), and clinical implications.

**Conditions:**  
{', '.join(relevant_conditions)}

**Exam Table:**  
{table_str}

**Extracted Text:**  
{extracted_text if extracted_text else "No additional extracted text provided."}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a teaching physician recommending the top exam maneuvers based on the provided information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating recommendations from GPT: {e}")
        return ""

# Streamlit App
st.title("Enhanced Bedside Diagnosis Recommender")

# Sidebar for generating sample clinical notes
st.sidebar.title("Generate Sample Clinical Note")
condition_options = [
    "Aortic stenosis", "Anemia", "Aortic regurgitation", 
    "Shoulder pain", "Knee pain", 
    "Hand pain", "Hip pain", "Pneumonia", "COPD", "Shortness of breath", "Chest pain", "Jaundice"
]
selected_conditions = st.sidebar.multiselect("Select condition(s):", condition_options)

if st.sidebar.button("Generate Sample Note"):
    with st.spinner("Generating sample clinical note..."):
        sample_note = generate_sample_note(selected_conditions)
    st.sidebar.markdown("### Sample Clinical Note")
    st.sidebar.text_area("Generated Note:", value=sample_note, height=300)

# Main area for diagnosis and recommendations
clinical_note = st.text_area("Enter the clinical note here:", placeholder="Type or paste your clinical note...")

if st.button("Recommend Maneuvers"):
    if clinical_note.strip():
        with st.spinner("Retrieving relevant findings..."):
            try:
                # Independent conditions list for recommendations
                conditions_list = ["aortic stenosis", "anemia", "aortic regurgitation", 
                                   "musculoskeletal-shoulder", "musculoskeletal-knee", 
                                   "musculoskeletal-hand", "musculoskeletal-hip", 
                                   "pneumonia", "copd"]
                relevant_conditions = get_relevant_conditions(clinical_note, conditions_list)
                print(relevant_conditions)

                if not relevant_conditions:
                    st.warning("No relevant conditions identified. Please refine your clinical note.")
                else:
                    st.success("Relevant conditions identified")
            except Exception as e:
                st.error(f"An error occurred: {e}")

        with st.spinner("Identifying specialized physical exam maneuvers..."):
            try:
                exam_table = load_exam_table()
                exam_table['Condition'] = exam_table['Condition'].str.strip().str.lower()
                relevant_conditions = [condition.strip().lower() for condition in relevant_conditions]
                filtered_table = exam_table[exam_table['Condition'].isin(relevant_conditions)]
                recommendations_generated = True
            except Exception as e:
                st.error(f"An error occurred: {e}")
                recommendations_generated = False

        if recommendations_generated:
            st.subheader("Recommended Physical Exam Maneuvers by Condition")
            for condition in relevant_conditions:
                condition_filtered_table = filtered_table[filtered_table['Condition'] == condition]
                recommendations = generate_recommendations(
                    clinical_note, [condition], condition_filtered_table, extracted_text=None
                )
                with st.expander(f"Physical Exam Maneuvers for {condition.title()}"):
                    st.markdown(recommendations)
    else:
        st.warning("Please enter a clinical note.")
