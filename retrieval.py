import pandas as pd
import faiss
import openai
import streamlit as st

# Retrieval function using FAISS
def retrieve_relevant_entries(query, index_path, metadata_path, model, top_k=5):
    # Load FAISS index
    index = faiss.read_index(index_path)

    # Load metadata
    metadata = pd.read_csv(metadata_path)

    # Encode the query using the provided model
    query_embedding = model.encode(query).reshape(1, -1)

    # Search for the top-k closest embeddings
    distances, indices = index.search(query_embedding, top_k)

    # Retrieve the corresponding content
    results = metadata.iloc[indices[0]].to_dict(orient="records")
    return results

# GPT function to generate recommendations
def generate_recommendations(clinical_note, relevant_entries, api_key):
    # Set OpenAI API key
    openai.api_key = api_key

    # Build the augmented prompt
    augmented_prompt = f"Clinical Note:\n{clinical_note}\n\nRelevant Findings:\n"
    for entry in relevant_entries:
        augmented_prompt += f"- {entry['type']}: {entry['content']}\n"

    # Query OpenAI GPT
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use GPT-3.5-Turbo
        messages=[
            {"role": "system", "content": "You are a physician recommending specialized physical exam maneuvers based on provided clinical notes and textbook data. For example assessing JVP when looking for fluid overload. Don't recommend basic maneuvers such as vitals or auscultation. When able, include sensitivity and specificity of each maneuver."},
            {"role": "user", "content": augmented_prompt}
        ],
        max_tokens=500,
        temperature=0.5
    )

    # Return GPT response content
    return response['choices'][0]['message']['content']