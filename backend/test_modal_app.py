# Created by Melody Yu
# Created on Sep 13, 2025

import requests
import json

# IMPORTANT: Replace this with your actual Modal deployment URL
# You can find this URL in the output when you run `modal deploy backend.main`
BASE_URL = "https://melody-yu--rizzoids-tutor-bot-run-app.modal.run" 

# --- Example Data ---

# 1. Example lesson text for the /add_context endpoint
# This JSON contains a 'text' key as required by the endpoint
example_lesson_text = {
    "text": """
    Today we're learning to solve linear equations. The goal is to isolate the variable, usually 'x'.
    A key theorem is the addition property of equality, which says you can add or subtract the same number from both sides of an equation.
    For example, to solve `2x + 5 = 15`, we first subtract 5 from both sides to get `2x = 10`. 
    Then, using the division property of equality, we divide by 2 to get `x = 5`.
    """
}

# 2. Example student work that contains an error
# This will be used to test the /check and /hint endpoints
example_work_with_error = {
    "work": [
        {
            "step": 1,
            "description": "Start with the equation",
            "equation": "3x + 10 = 25"
        },
        {
            "step": 2,
            "description": "Subtract 10 from both sides",
            "equation": "3x = 35"  # Error: 25 - 10 is 15, not 35
        }
    ]
}

def run_test(endpoint: str, data: dict):
    """Helper function to run a test against a deployed Modal endpoint."""
    if "your-modal-app-url" in BASE_URL:
        print(f"--- SKIPPING TEST for /{endpoint} ---")
        print("Please update BASE_URL in this script with your deployed Modal URL.")
        print("-" * 25)
        return

    try:
        url = f"{BASE_URL}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        print(f"--- Testing /{endpoint} ---")
        print(f"Sending POST request to {url}")
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        print(f"Status: {response.status_code}")
        print("Response (Markdown):\n")
        print(response.text)
        print("-" * 25)

    except requests.exceptions.RequestException as e:
        print(f"--- Error testing /{endpoint} ---")
        print(f"Request failed: {e}")
        if e.response is not None:
            print(f"Response body: {e.response.text}")
        print("-" * 25)

if __name__ == "__main__":
    print("Tutor Bot API Test Script for Modal Deployment")
    print("=" * 50 + "\n")
    
    # Step 1: Add some lesson context to the persistent cache on Modal.
    # You can run this multiple times to add more context.
    run_test("add_context", example_lesson_text)
    
    # Step 2: Now, check student work. The tutor bot will use the context
    # we just added to provide a more informed response.
    run_test("check", example_work_with_error)
    
    # Step 3: Test the hint endpoint with the same context.
    run_test("hint", example_work_with_error)
