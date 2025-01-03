import pandas as pd

# Paths to raw text and table data
TEXT_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/aortic_stenosis_raw_text.txt"
TABLE_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/organized_findings_table_6.csv"
OUTPUT_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/combined_aortic_stenosis.csv"

# Load the raw text file
with open(TEXT_PATH, "r") as f:
    raw_text = f.read()

# Create a DataFrame for the raw text
text_data = [{"type": "text", "content": raw_text}]
text_df = pd.DataFrame(text_data)

# Load the table data
tables_df = pd.read_csv(TABLE_PATH)

# Check and clean table data
if 'content' not in tables_df.columns:
    # Combine all columns into a single 'content' column for embedding
    tables_df['content'] = tables_df.apply(lambda row: ', '.join(row.dropna().astype(str)), axis=1)

# Add a "type" column to differentiate between text and tables
tables_df["type"] = "table"

# Combine text and tables into one DataFrame
combined_aortic_stenosis = pd.concat([text_df, tables_df[['type', 'content']]], ignore_index=True)

# Save the combined dataset
combined_aortic_stenosis.to_csv(OUTPUT_PATH, index=False)
print(f"Combined dataset saved to {OUTPUT_PATH}")

data = pd.read_csv(OUTPUT_PATH)
print(data.head(10))