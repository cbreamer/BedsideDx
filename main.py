import streamlit as st
from openai import OpenAI
import pandas as pd

stored_password = st.secrets["passwords"]["app_password"]


# Initialize session state for password check
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False  # Initial state: not authenticated

# Function to check password
def check_password():
    if st.session_state["password_input"] == stored_password:
        st.session_state.authenticated = True  # Correct password entered
    else:
        st.error("Incorrect password. Please try again.")

# Show password input if not authenticated
if not st.session_state.authenticated:
    st.text_input(
        "Enter Password:", 
        type="password", 
        key="password_input", 
        on_change=check_password
    )
else:
        
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
                model="gpt-4o",
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
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a physician creating sample clinical notes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7,
                stream=True
            )
            result = ""
            for chunk in response:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", "")
                if content:
                    result += content
            return result
        except Exception as e:
            return f"Error generating sample note: {e}"

    # Function to load the exam table
    def load_exam_table():
        try:
            return pd.read_csv(EXAM_TABLE_PATH)
        except Exception as e:
            st.error(f"Error loading table: {e}")
            return pd.DataFrame()

    # Function to generate recommendations with dynamic streaming
    def generate_recommendations(relevant_conditions, filtered_table=None):
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

        prompt = f"""
        Using the following information, identify and prioritize the most relevant specialized physical exam maneuvers for the patient. Provide step-by-step instructions, positive/negative findings, relevant statistics (sensitivity, specificity, LR+/-), and clinical implications.

        **Conditions:**  
        {', '.join(relevant_conditions)}

        **Exam Table:**  
        {table_str}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a teaching physician recommending the top exam maneuvers based on the provided information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.5,
                stream=True
            )
            placeholder = st.empty()  # Placeholder for dynamic updates
            result = ""
            for chunk in response:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", "")
                if content:
                    result += content
                    placeholder.markdown(result)  # Dynamically update the content
            result += "\n\n---\n**Citation:** McGee S. Evidence-Based Physical Diagnosis. Elsevier - Health Science; 2021."
            placeholder.markdown(result)  # Final update with the citation
            return result
        except Exception as e:
            st.error(f"Error generating recommendations from GPT: {e}")
            return "An error occurred while generating recommendations."

    # Streamlit App
    st.title("Enhanced Bedside Physical Exam")

    st.info(
        """
        This is an educational app that will take a clinical note and recommend specialized physical exam tests to perform based on the clinical situation.  
        **Do not include any PHI!**
        """,
        icon="ℹ️"
    )

    st.warning(
        """
        **Disclaimer:** This tool is a prototype and currently only suggests physical exam maneuvers for a limited number of conditions. 
        It should be used for educational purposes only and not as a clinical decision-making tool.
        """,
        icon="⚠️"
    )
    # Sidebar for generating sample clinical notes
    st.sidebar.title("Generate Sample Clinical Note")
    condition_options = [
        "Aortic stenosis", "Anemia", "Aortic regurgitation", 
        "Shoulder pain", "Knee pain", 
        "Hand pain", "Hip pain", "Pneumonia", "COPD", "Shortness of breath", "Chest pain"
    ]
    selected_conditions = st.sidebar.multiselect("Select condition(s):", condition_options)

    # Spinner in the main area, but output in the sidebar
    if st.sidebar.button("Generate Sample Note"):
        with st.spinner("Generating sample clinical note..."):
            sample_note = generate_sample_note(selected_conditions)
        st.sidebar.markdown("### Sample Clinical Note")
        st.sidebar.text_area("Generated Note:", value=sample_note, height=300)

    # Main area for clinical notes and recommendations
    clinical_note = st.text_area("Enter the clinical note here:", placeholder="Type or paste your clinical note...")

    if st.button("Recommend physical exam maneuvers"):
        if clinical_note.strip():
            with st.spinner("Retrieving relevant findings..."):
                try:
                    conditions_list = [
                        "aortic stenosis", "anemia", "aortic regurgitation", 
                        "musculoskeletal-shoulder", "musculoskeletal-knee", 
                        "musculoskeletal-hand", "musculoskeletal-hip", 
                        "pneumonia", "copd"
                    ]
                    relevant_conditions = get_relevant_conditions(clinical_note, conditions_list)

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
                    st.markdown(f"## {condition.title()}")  # Add a title for the condition
                    condition_filtered_table = filtered_table[filtered_table['Condition'] == condition]

                    # Stream recommendations dynamically
                    generate_recommendations([condition], condition_filtered_table)
        else:
            st.warning("Please enter a clinical note.")
