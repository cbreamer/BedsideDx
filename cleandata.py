import pandas as pd

# Path to your Excel file
excel_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/aortic_stenosis_tables.xlsx"

# Load the specific sheet (e.g., "Table_6") from the Excel file
df = pd.read_excel(excel_path, sheet_name="Table_6", header=None)  # Replace "Table_6" with your sheet name

# Initialize variables
organized_data = []
current_header = None

# Iterate over the rows to organize data
for _, row in df.iterrows():
    if len(row) > 2 and pd.isna(row.iloc[1]) and pd.isna(row.iloc[2]):  # Safely check for header
        current_header = row.iloc[0]  # Set the header
    else:
        organized_data.append({
            "Header": current_header,
            "Finding": row.iloc[0] if len(row) > 0 else None,
            "Sensitivity (%)": row.iloc[1] if len(row) > 1 else None,
            "Specificity (%)": row.iloc[2] if len(row) > 2 else None,
            "LR+": row.iloc[3] if len(row) > 3 else None,
            "LR-": row.iloc[4] if len(row) > 4 else None
        })

# Convert to DataFrame
organized_df = pd.DataFrame(organized_data)

# Save to CSV
organized_df.to_csv("/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/organized_findings_table_6.csv", index=False)
print("Data saved to /Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/organized_findings_table_6.csv")
