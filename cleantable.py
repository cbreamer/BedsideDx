import pandas as pd

# Path to the CSV file
csv_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/organized_findings_table_6.csv"  # Update with your actual path

# Load the CSV file
table_data = pd.read_csv(csv_path)

def format_table_data(table, top_n=5):
    """
    Formats the data from the table for GPT to understand and process.
    
    Args:
        table (pd.DataFrame): The DataFrame containing the maneuver data.
        top_n (int): Number of top maneuvers to include.
    
    Returns:
        str: Formatted table data as a string.
    """
    table_str = "Relevant Exam Maneuvers:\n"
    table = table.dropna(subset=['Finding'])  # Drop rows where 'Finding' is NaN
    table = table.head(top_n)  # Limit to top N rows
    
    for _, row in table.iterrows():
        table_str += (
            f"- {row['Finding']} ({row['Header']}):\n"
            f"  Sensitivity: {row['Sensitivity (%)']}%, Specificity: {row['Specificity (%)']}%\n"
            f"  LR+: {row['LR+']}, LR-: {row['LR-']}\n\n"
        )
    return table_str

