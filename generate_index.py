import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Paths
DATA_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/combined_aortic_stenosis.csv"
INDEX_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/combined_aortic_stenosis_index.faiss"

# Load metadata
print("Loading metadata...")
metadata = pd.read_csv(DATA_PATH)

# Filter rows with valid content
metadata = metadata[metadata['content'].notna()]  # Remove rows with NaN in content
metadata['content'] = metadata['content'].astype(str)  # Ensure all content is string

# Initialize the SentenceTransformer model
print("Initializing the model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings for the content column
print("Generating embeddings...")
content_embeddings = metadata['content'].apply(lambda x: model.encode(x)).to_list()
embedding_array = np.vstack(content_embeddings)  # Convert list of embeddings to a NumPy array

# Create FAISS index
print("Creating FAISS index...")
dimension = embedding_array.shape[1]  # Dimension of embeddings
index = faiss.IndexFlatL2(dimension)  # L2 distance index
index.add(embedding_array)  # Add embeddings to the index

# Save the FAISS index
faiss.write_index(index, INDEX_PATH)
print(f"FAISS index saved to {INDEX_PATH}")
