from retrieval import retrieve_relevant_entries, generate_recommendations
from sentence_transformers import SentenceTransformer

# Paths for the FAISS index and metadata file
INDEX_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/combined_aortic_stenosis_index.faiss"
METADATA_PATH = "/Users/courtneyreamer/Documents/Fellowship/BedsideEvalAI/combined_aortic_stenosis.csv"

# Load the API key from Streamlit secrets
api_key = st.secrets["openai"]["api_key"]

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define a sample query
query = "What are the findings associated with delayed carotid artery upstroke?"

# Test the retrieval function
print("Testing retrieval...")
try:
    relevant_entries = retrieve_relevant_entries(query, INDEX_PATH, METADATA_PATH, model, top_k=5)

    # Print the retrieved entries
    if relevant_entries:
        print("Retrieved relevant entries:")
        for i, entry in enumerate(relevant_entries, 1):
            print(f"{i}. Type: {entry['type']}, Content: {entry['content']}")

        # Test GPT recommendations
        print("\nGenerating GPT recommendations...")
        clinical_note = "Patient presents with dyspnea and fatigue, suspected aortic stenosis."
        recommendations = generate_recommendations(clinical_note, relevant_entries, api_key)
        print("Generated Recommendations:")
        print(recommendations)
    else:
        print("No relevant entries found. Please check your query or data.")
except Exception as e:
    print(f"Error during retrieval or GPT recommendation generation: {e}")
