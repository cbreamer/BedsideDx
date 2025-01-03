import pandas as pd
from sentence_transformers import SentenceTransformer

# Define the file path for the CSV file
file_path = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/combined_aortic_stenosis.csv"

# Load the CSV file into a DataFrame
combined_aortic_stenosis = pd.read_csv(file_path)

# Check if the file loaded correctly
print("Data loaded successfully!")
print(combined_aortic_stenosis.head())

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Separate rows with valid "content" for embedding
rows_with_content = combined_aortic_stenosis[combined_aortic_stenosis['content'].notna()]
rows_with_content['content'] = rows_with_content['content'].astype(str)  # Ensure all are strings

# Generate embeddings only for rows with valid content
rows_with_content['embedding'] = rows_with_content['content'].apply(lambda x: model.encode(x))

# Merge the embeddings back into the original DataFrame
combined_aortic_stenosis = pd.merge(
    combined_aortic_stenosis,
    rows_with_content[['content', 'embedding']],
    on='content',
    how='left'
)

print("Embeddings added successfully!")
print(combined_aortic_stenosis.head(10))

