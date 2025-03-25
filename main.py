import streamlit as st
from openai import OpenAI
import pandas as pd
import json 

stored_password = st.secrets["passwords"]["app_password"]
#using tools with large language model. Come up with post-test probability for combining these findings and use calculator (include in prompt)
#openapi- defined tool as calculator, explain how to use calculator. make funciton in python of formula. calculation being performed by tool
#look at openapi tools

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
    EXAM_TABLE_PATH = "Extracted_phys_exam-updated.csv"
    
    for key in ["user_findings", "relevant_conditions", "filtered_table"]:
        if key not in st.session_state:
            st.session_state[key] = None

    # Function to get relevant conditions
    def get_relevant_conditions(clinical_note, conditions_list):
        prompt = f"""
        You are a teaching physician. Your task is to extract relevant conditions from the provided clinical note.

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
            You are a clinician reviewing a list of physical exam maneuvers relevant to the following condition(s): {', '.join(relevant_conditions)}.

            From the list below, choose the 5 most relevant maneuvers based on diagnostic value (e.g., LR+, LR-, context). For each, return:
            - "name": the maneuver name (as written in the list)
            - "description": a brief instruction on how to perform the maneuver and interpret a positive finding.

            Return **only a valid JSON array** in the following format — no extra text or explanation:
            [
            {{"name": "maneuver name", "description": "how to perform and interpret the finding:}}, 
            ...
            ]
            You must return exactly 5 items. 
            
            Here is the list:
            {table_str}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a teaching physician who explains evidence-based physical exam maneuvers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.5
            )
            content = response.choices[0].message.content

            # Parse GPT's JSON
            st.text("Raw GPT response:")
            st.code(content)
            if content.strip().startswith("```"):
                content = content.strip().strip("```json").strip("```").strip()
            recommendations = json.loads(content)
            # Clean content if it comes wrapped in Markdown-style triple backticks

            return recommendations

        except Exception as e:
            st.error(f"Error generating maneuver descriptions: {e}")
            return []

    # Streamlit App
    # Initialize session state variables
    for key in ["user_findings", "relevant_conditions", "filtered_table"]:
        if key not in st.session_state:
            st.session_state[key] = None

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

    # Clinical note input
    clinical_note = st.text_area("Enter the clinical note here:", placeholder="Type or paste your clinical note...")

    # Recommend button
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
                        st.session_state.relevant_conditions = [c.lower() for c in relevant_conditions]
                        st.success("Relevant conditions identified")
                except Exception as e:
                    st.error(f"Error: {e}")

            with st.spinner("Identifying specialized physical exam maneuvers..."):
                try:
                    exam_table = load_exam_table()
                    exam_table['Condition'] = exam_table['Condition'].str.strip().str.lower()
                    filtered_table = exam_table[exam_table['Condition'].isin(st.session_state.relevant_conditions)]
                    st.session_state.filtered_table = filtered_table
                except Exception as e:
                    st.error(f"Error loading maneuvers: {e}")
        else:
            st.warning("Please enter a clinical note.")

    # Show recommendations if already available
    if st.session_state.filtered_table is not None and st.session_state.relevant_conditions is not None:
        st.subheader("Recommended Physical Exam Maneuvers by Condition")
        user_findings = {}

        for condition in st.session_state.relevant_conditions:
            st.subheader(f"Top Exam Maneuvers for {condition.title()}")

            condition_filtered = st.session_state.filtered_table[
                st.session_state.filtered_table['Condition'] == condition
            ]

            recommendations = generate_recommendations([condition], condition_filtered)

            for idx, item in enumerate(recommendations):
                name = item["name"]
                description = item["description"]

                match = condition_filtered[condition_filtered["Physical exam maneuver"] == name]
                if match.empty:
                    continue
                row = match.iloc[0]

                with st.expander(f"{name}"):
                    st.markdown(f"**Description:** {description}")
                    st.markdown(f"""
                    **Finding:** {row['Finding']}  
                    **Sensitivity:** {row['Sensitivity (%)']}%  
                    **Specificity:** {row['Specificity (%)']}%  
                    **LR+:** {row['LR+']}  
                    **LR-:** {row['LR-']}
                    """)

                    response = st.radio(
                        "Was the finding present?",
                        ["Not Done", "Present", "Absent"],
                        key=f"{condition}_{idx}"
                    )

                    user_findings[f"{condition}_{name}"] = {
                        "maneuver": name,
                        "finding": row['Finding'],
                        "description": description,
                        "present": response,
                        "LR+": float(row["LR+"]),
                        "LR-": float(row["LR-"]),
                        "Pretest_PR": float(row["Pretest_PR (%)"]) / 100
                    }

        # Store findings for post-test probability calculation
        st.session_state.user_findings = user_findings

        # Post-test probability calculator
        if st.button("Calculate Post-Test Probability"):
            # Store findings for post-test probability calculation
            results = {}  # ✅ Initialize results dictionary here

            for condition in st.session_state.relevant_conditions:
                condition_findings = {
                    k: v for k, v in st.session_state.user_findings.items()
                    if k.startswith(condition)
                }

                if not condition_findings:
                    continue

                pretest_probs = [v["Pretest_PR"] for v in condition_findings.values()]
                pretest_prob = sum(pretest_probs) / len(pretest_probs)
                pretest_odds = pretest_prob / (1 - pretest_prob)

                for v in condition_findings.values():
                    if v["present"] == "Present":
                        pretest_odds *= v["LR+"]
                    elif v["present"] == "Absent":
                        pretest_odds *= v["LR-"]
                    # Not Done → skip

                posttest_prob = pretest_odds / (1 + pretest_odds)

                # ✅ Save results
                results[condition] = {
                    "pretest_prob": pretest_prob,
                    "posttest_prob": posttest_prob
                }

    # Save to session state so it persists on rerun
            st.session_state.posttest_results = results

#Outside the button block — always render if results are available
    if "posttest_results" in st.session_state:
        for condition, result in st.session_state.posttest_results.items():
            st.markdown(f"""
            ### 🧮 Post-Test Probability for **{condition.title()}**  
            - **Pre-test probability**: {result['pretest_prob'] * 100:.2f}%  
            - **Post-test probability**: **{result['posttest_prob'] * 100:.2f}%**
            """)

               


    else:
        st.warning("Please enter a clinical note.")
