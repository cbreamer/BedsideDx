import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from secret.env
load_dotenv("secret.env")

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Make sure it's set in secret.env")
else:
    print("API key loaded successfully.")

# Create OpenAI client
client = OpenAI(api_key=api_key)

try:
    # Generate a chat completion
    response = client.chat.completions.create(  # New OpenAI SDK usage
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a haiku about recursion in programming."},
        ],
        max_tokens=50,
        temperature=0.5,
    )

    # Access the message content
    message_content = response.choices[0].message.content  # Access .content directly

    print("Response from OpenAI:")
    print(message_content)
except Exception as e:
    print(f"Error with OpenAI API: {e}")
