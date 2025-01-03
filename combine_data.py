import pandas as pd

# Path to your raw text and table data
text_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/aortic_stenosis_raw_text.txt"
table_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/organized_findings_table_6.csv"

# Load the raw text file
with open(text_path, "r") as f:
    raw_text = f.read()

# Create a DataFrame for the raw text
text_data = [{"type": "text", "content": raw_text}]
text_df = pd.DataFrame(text_data)

# Load the table data
tables_df = pd.read_csv(table_path)

# Add a "type" column to differentiate between text and tables
tables_df["type"] = "table"

# Combine text and tables into one DataFrame
combined_aortic_stenosis = pd.concat([text_df, tables_df], ignore_index=True)

# Save the combined dataset (optional)
combined_aortic_stenosis.to_csv("/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/combined_aortic_stenosis.csv", index=False)
print("Combined dataset saved as combined_aortic_stenosis.csv.")
