import os

# Get the OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    print("OpenAI API key is not set.")
else:
    print(f"Using OpenAI API Key: {openai_api_key}")
