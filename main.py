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
                    f"- Condition: {row['Condition']}\n"
                    f"- Video URL: {row.get('Video URL', '')}\n"
                    f"- Image URL: {row.get('Image URL', '')}\n\n"
                )
        else:
            table_str = "No relevant exam maneuvers found."

        prompt = f"""
            Using the following information, identify and prioritize the most relevant specialized physical exam maneuvers for the patient. For each maneuver, include:
            - Step-by-step instructions
            - How to interpret positive/negative findings
            - Relevant statistics (sensitivity, specificity, LR+/-)
            - Clinical implications
            - At the end, provide any available media links in this format:
            - [🎥 Video Link](https://...)
            - [🖼️ Image Link](https://...).

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
        "Hand pain", "Hip pain", "Pneumonia", "COPD", "Shortness of breath", "Chest pain", "Cushing's syndrome"
    ]
    selected_conditions = st.sidebar.multiselect("Select condition(s):", condition_options)

    # Spinner in the main area, but output in the sidebar
    if st.sidebar.button("Generate Sample Note"):
        with st.spinner("Generating sample clinical note..."):
            sample_note = generate_sample_note(selected_conditions)
        st.sidebar.markdown("### Sample Clinical Note")
        st.sidebar.text_area("Generated Note:", value=sample_note, height=300)

    # Main area for clinical notes and recommendations
    if "clinical_note" not in st.session_state:
        st.session_state["clinical_note"] = ""

    clinical_note = st.text_area(
        "Enter the clinical note here:",
        value=st.session_state["clinical_note"],
        placeholder="Type or paste your clinical note...",
        key="clinical_note_input"
)

        # Keep it synced
    st.session_state["clinical_note"] = clinical_note


    if st.button("Recommend physical exam maneuvers"):
        if clinical_note.strip():
            with st.spinner("Retrieving relevant findings..."):
                try:
                    conditions_list = [
                        "aortic stenosis", "anemia", "aortic regurgitation", 
                        "musculoskeletal-shoulder", "musculoskeletal-knee", 
                        "musculoskeletal-hand", "musculoskeletal-hip", 
                        "pneumonia", "copd", "cushing's syndrome"
                    ]
                    relevant_conditions = get_relevant_conditions(clinical_note, conditions_list)
                    st.session_state["relevant_conditions"] = relevant_conditions


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
                    st.session_state["filtered_table"] = filtered_table
                    st.session_state["recommendations_ready"] = True
                    print(filtered_table)
                    recommendations_generated = True
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    recommendations_generated = False
                    
    if st.session_state.get("recommendations_ready", False):
        st.subheader("Recommended Physical Exam Maneuvers by Condition")
        relevant_conditions = st.session_state.get("relevant_conditions", [])
        filtered_table = st.session_state.get("filtered_table", pd.DataFrame())
        for condition in relevant_conditions:
            st.markdown(f"## {condition.title()}")  # Add a title for the condition
            
            #create data frame: condition_filtred_table that includes only the rows from the 
            # filtered_table where Condition matches the column condition
            condition_filtered_table = filtered_table[filtered_table['Condition'] == condition]

            # Stream recommendations dynamically
            generate_recommendations([condition], condition_filtered_table)
            clinical_note = st.session_state.get("clinical_note", "")
            relevant_conditions = st.session_state.get("relevant_conditions", [])
            st.session_state["recommendations_ready"] = True
            
            # Create editable table below GPT output
            editable_table = condition_filtered_table.copy()
            # Display exam maneuvers in a table with dropdowns for selection
            st.markdown("### \U0001F4CB Select Findings for Post-Test Probability")
            selections = []

            with st.form(key=f"post_test_form_{condition}"):
                # --- HEADINGS ---
                heading_cols = st.columns([2, 2, 3, 2.5, 2.5, 2.5, 2.5, 2.5])
                heading_cols[0].markdown("**Physical Exam Maneuver**")
                heading_cols[1].markdown("**Finding**")
                heading_cols[2].markdown("**Result**")
                heading_cols[3].markdown("**Sensitivity (%)**")
                heading_cols[4].markdown("**Specificity (%)**")
                heading_cols[5].markdown("**LR+**")
                heading_cols[6].markdown("**LR-**")
                heading_cols[7].markdown("**Pretest_PR (%)**")
                
                for idx, row in editable_table.iterrows():
                    cols = st.columns([2, 2, 3, 2.5, 2.5, 2.5, 2.5, 2.5])
                    cols[0].markdown(f"**{row['Physical exam maneuver']}**")
                    cols[1].markdown(f"{row['Finding']}")
                    result_key = f"{condition}_{idx}_result"
                    default_value = st.session_state.get(result_key, "Not Done")
                    selection = cols[2].selectbox(
                        "",
                        ["Not Done", "Present", "Absent"],
                        index=["Not Done", "Present", "Absent"].index(default_value),
                        key=result_key
                    )
                    cols[3].markdown(f":green[{row['Sensitivity (%)']}]")
                    cols[4].markdown(f":green[{row['Specificity (%)']}]")
                    cols[5].markdown(f":green[{row['LR+']}]")
                    cols[6].markdown(f":green[{row['LR-']}]")
                    cols[7].markdown(f":green[{row['Pretest_PR (%)']}]")

                    selections.append({
                        "Result": selection,
                        "Sensitivity (%)": row["Sensitivity (%)"],
                        "Specificity (%)": row["Specificity (%)"],
                        "LR+": row["LR+"],
                        "LR-": row["LR-"],
                        "Pretest_PR (%)": row["Pretest_PR (%)"]
                    })

            # Add a submit button to calculate post-test probability
                submitted = st.form_submit_button(f"Calculate Post-Test Probability for {condition.title()}")

                if submitted:
                    selected_df = pd.DataFrame([s for s in selections if s["Result"] != "Not Done"])

                    if not selected_df.empty:
                        pretest_probs = pd.to_numeric(selected_df["Pretest_PR (%)"], errors='coerce') / 100
                        pretest_probs = pretest_probs.dropna()
                        pretest_prob = pretest_probs.mean() if not pretest_probs.empty else 0.1
                        pretest_odds = pretest_prob / (1 - pretest_prob)

                        for _, row in selected_df.iterrows():
                            lr = None
                            if row["Result"] == "Present":
                                lr = pd.to_numeric(row["LR+"], errors='coerce')
                            elif row["Result"] == "Absent":
                                lr = pd.to_numeric(row["LR-"], errors='coerce')
                            if pd.notna(lr) and lr > 0:
                                pretest_odds *= lr

                        posttest_prob = pretest_odds / (1 + pretest_odds)
                        st.success(f"\U0001F4C8 Post-Test Probability for **{condition.title()}**: **{posttest_prob*100:.1f}%**")
                    else:
                        st.warning("Please select at least one finding as Present or Absent.")
                
        else:
            st.warning("Please enter a clinical note.")