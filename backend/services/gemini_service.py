import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

#Simple Test Function

def test_gemini_connection(prompt: str = "Say hello in one sentence") -> str:
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
    

if __name__ == "__main__":
    print("Testing Gemini connection...")
    result = test_gemini_connection()
    print(f"Response: {result}")