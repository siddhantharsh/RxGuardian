import os
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_api():
    # Print current working directory
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")

    # Load environment variables, explicitly looking for .env in the root project directory
    # Assuming the project root is one level up from 'backend'
    dotenv_path = find_dotenv()
    if not dotenv_path:
        # If find_dotenv doesn't find it, assume it's one level up from current script
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if not os.path.exists(dotenv_path):
            print(f"Error: .env file not found at expected path: {dotenv_path}")
            return False

    print(f"Attempting to load .env from: {dotenv_path}")
    load_dotenv(dotenv_path)
    
    # Get API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set after loading .env. Please ensure your .env file is correct.")
        return False
    
    print(f"API Key (first 5 chars): {api_key[:5]}...")
    
    try:
        # Configure Gemini
        print("Configuring Gemini API...")
        genai.configure(api_key=api_key)
        
        # List available models
        print("\nListing available models...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                print(f"Found model: {m.name}")
        
        if not available_models:
            print("Error: No available models found")
            return False
        
        # Try different models in order of preference for the test
        models_to_try = [
            'models/gemini-1.5-pro',
            'models/gemini-1.5-pro-latest',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-latest'
        ]

        test_model_name = None
        for m_name in models_to_try:
            if m_name in available_models:
                test_model_name = m_name
                break
        
        if not test_model_name:
            print("Error: No suitable non-deprecated model found for testing.")
            return False

        print(f"\nTesting with model: {test_model_name}")
        model = genai.GenerativeModel(test_model_name)
        
        # Simple test prompt
        test_prompt = "What is 2+2? Answer in one word."
        print(f"\nSending test prompt: {test_prompt}")
        
        # Generate response
        response = model.generate_content(test_prompt)
        print("\nResponse received:")
        print(response.text)
        
        print("\nAPI test successful!")
        return True
        
    except Exception as e:
        print(f"\nError testing API: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting Gemini API test...")
    success = test_gemini_api()
    print(f"\nTest completed: {'Success' if success else 'Failed'}") 