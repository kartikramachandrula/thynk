import requests
import json

# Example usage of the tutor bot API endpoints

BASE_URL = "http://localhost:3000"

# Example student work data
example_work_correct = {
    "work": [
        {
            "step": 1,
            "description": "Identify the equation",
            "equation": "2x + 5 = 13",
            "action": "Given equation"
        },
        {
            "step": 2,
            "description": "Subtract 5 from both sides",
            "equation": "2x = 8",
            "action": "Subtracted 5 from both sides"
        },
        {
            "step": 3,
            "description": "Divide both sides by 2",
            "equation": "x = 4",
            "action": "Divided both sides by 2"
        }
    ],
    "lesson": {}  # Empty as requested
}

example_work_with_error = {
    "work": [
        {
            "step": 1,
            "description": "Identify the equation",
            "equation": "2x + 5 = 13",
            "action": "Given equation"
        },
        {
            "step": 2,
            "description": "Subtract 5 from both sides",
            "equation": "2x = 18",  # Error: should be 8, not 18
            "action": "Subtracted 5 from both sides"
        }
    ],
    "lesson": {}  # Empty as requested
}

def test_check_endpoint():
    """Test the /check endpoint"""
    print("Testing /check endpoint...")
    
    # Test with correct work
    print("\n1. Testing with correct work:")
    response = requests.get(f"{BASE_URL}/check", json=example_work_correct)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test with incorrect work
    print("\n2. Testing with incorrect work:")
    response = requests.get(f"{BASE_URL}/check", json=example_work_with_error)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_hint_endpoint():
    """Test the /hint endpoint"""
    print("\n\nTesting /hint endpoint...")
    
    # Test with partial work (needs next step)
    partial_work = {
        "work": [
            {
                "step": 1,
                "description": "Identify the equation",
                "equation": "2x + 5 = 13",
                "action": "Given equation"
            },
            {
                "step": 2,
                "description": "Subtract 5 from both sides",
                "equation": "2x = 8",
                "action": "Subtracted 5 from both sides"
            }
        ],
        "lesson": {}  # Empty as requested
    }
    
    print("\n1. Testing with partial work (needs next step):")
    response = requests.get(f"{BASE_URL}/hint", json=partial_work)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_health_endpoint():
    """Test the /health endpoint"""
    print("\n\nTesting /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Tutor Bot API Test Script")
    print("=" * 40)
    
    try:
        test_health_endpoint()
        test_check_endpoint()
        test_hint_endpoint()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the tutor bot is running on localhost:3000")
    except Exception as e:
        print(f"Error: {e}")
