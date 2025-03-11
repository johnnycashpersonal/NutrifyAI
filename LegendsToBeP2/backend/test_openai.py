# test_openai.py
import os
import openai
from dotenv import load_dotenv

load_dotenv()  # Make sure your .env has OPENAI_API_KEY

# Configure your global API key
openai.api_key = os.getenv("OPENAI_API_KEY")
#gpt-3.5-turbo

def test_openai():
    try:
        # This call is valid in openai>=1.0.0 for chat-based models
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello from a test script."}],
            max_tokens=30,
            temperature=0.7,
        )
        # Print the assistant's reply
        print("OpenAI response:\n", response.choices[0].message.content.strip())
    except Exception as e:
        print("Error calling OpenAI API:", e)

if __name__ == "__main__":
    test_openai()
