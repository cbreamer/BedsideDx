import pdfplumber
import pandas as pd

# Paths for input and output
pdf_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/COPD_Mcgee.pdf"
text_output_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/copd_raw_text.txt"
table_text_output_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/copd_table_text.txt"
tables_output_excel_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/copd_tables.xlsx"

def extract_text_and_format_tables(pdf_path, text_output_path, table_text_output_path, tables_output_excel_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            table_text = ""
            tables = []

            # Extract text and tables from each page
            for page in pdf.pages:
                # Extract and append page text
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

                # Extract and format tables
                page_tables = page.extract_tables()
                for table in page_tables:
                    # Convert each table to a DataFrame
                    if table:
                        headers = table[0]  # Table headers
                        rows = table[1:]   # Table rows
                        df = pd.DataFrame(rows, columns=headers)
                        tables.append(df)

                        # Format table as readable text
                        table_text += "Table:\n"
                        for row in rows:
                            formatted_row = ", ".join(
                                f"{headers[i]}: {value.strip() if value else 'N/A'}"  # Handle None values
                                for i, value in enumerate(row)
                            )
                            table_text += f"  - {formatted_row}\n"
                        table_text += "\n"

            # Save extracted plain text
            with open(text_output_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Text successfully extracted to {text_output_path}")

            # Save formatted table text
            with open(table_text_output_path, "w", encoding="utf-8") as f:
                f.write(table_text)
            print(f"Formatted tables successfully extracted to {table_text_output_path}")

            # Save tables to an Excel file
            if tables:
                with pd.ExcelWriter(tables_output_excel_path) as writer:
                    for i, df in enumerate(tables):
                        sheet_name = f"Table_{i+1}"
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"Tables successfully saved to {tables_output_excel_path}")
            else:
                print("No tables found in the PDF.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the extraction
extract_text_and_format_tables(pdf_path, text_output_path, table_text_output_path, tables_output_excel_path)
