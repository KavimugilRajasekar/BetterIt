import os
import requests
from dotenv import load_dotenv

load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

try:
    from aiwriter.tag_store import TagStore
    store = TagStore()
    api_key = store.get_active_api_key() or os.getenv("OPEN_ROUTER")
    model = store.get_active_model() or os.getenv("MODEL")
except Exception:
    api_key = os.getenv("OPEN_ROUTER")
    model = os.getenv("MODEL")

if not api_key:
    print("ERROR: OPEN_ROUTER is missing in .env")
    exit(1)

if not model:
    print("ERROR: MODEL is missing in .env")
    exit(1)

print(f"Testing OpenRouter...")
print(f"Model: {model}")

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": "Reply with exactly: MODEL_REACHABLE"
        }
    ]
}

try:
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()

        answer = data["choices"][0]["message"]["content"]

        print("\nSUCCESS")
        print("OpenRouter: REACHABLE")
        print(f"Model: {model}")
        print(f"Response: {answer}")

    else:
        print("\nFAILED")
        print(f"HTTP Status: {response.status_code}")
        print("Response:")
        print(response.text)

except requests.exceptions.Timeout:
    print("\nFAILED")
    print("Request timed out.")

except requests.exceptions.RequestException as e:
    print("\nFAILED")
    print(f"Network error: {e}")

except Exception as e:
    print("\nFAILED")
    print(f"Unexpected error: {e}")