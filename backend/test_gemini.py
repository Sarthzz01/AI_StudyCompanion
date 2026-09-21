import os
from dotenv import load_dotenv

# Load from backend/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY", "").strip()
model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

print("=" * 60)
print("GEMINI API CONFIGURATION CHECK")
print("=" * 60)
print(f"API Key present: {'YES (Length: ' + str(len(api_key)) + ')' if api_key else 'NO'}")
print(f"API Key preview: {api_key[:6]}...{api_key[-4:] if len(api_key) > 10 else ''}")
print(f"Target Model:    {model_name}")
print("-" * 60)

if not api_key:
    print("ERROR: GEMINI_API_KEY is empty in backend/.env!")
    exit(1)

try:
    from google import genai
    print("[INFO] Successfully imported google-genai SDK.")
except ImportError as e:
    print(f"ERROR: Failed to import google-genai: {e}")
    exit(1)

try:
    print(f"[INFO] Connecting to Gemini API using model '{model_name}'...")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents="Say 'Hello, Study Companion! Your Gemini API is working perfectly.' in one short sentence."
    )
    print("\n" + "=" * 60)
    print("TEST SUCCESSFUL!")
    print("=" * 60)
    print(f"Response from {model_name}:\n{response.text.strip()}")
    print("=" * 60)
except Exception as e:
    print("\n" + "=" * 60)
    print("GEMINI API CALL FAILED")
    print("=" * 60)
    print(f"Error Type: {type(e).__name__}")
    print(f"Details:    {e}")
    print("=" * 60)
