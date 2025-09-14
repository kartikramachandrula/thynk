#!/usr/bin/env python3
"""
Test script for Thynk: Always Ask Y system
Tests all core functions and endpoints
"""

import asyncio
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import requests
import time

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user"

def create_test_image_with_math_problem(text: str) -> str:
    """Create a test image with math problem text and return as base64"""
    # Create a simple image with text
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Add the math problem text
    draw.text((20, 50), text, fill='black', font=font)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

def test_endpoint(method: str, endpoint: str, data: dict = None) -> dict:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                return {"text": response.text}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed - is the server running?"}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("🧠 Testing Thynk: Always Ask Y System")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    result = test_endpoint("GET", "/health")
    print(f"   Result: {result}")
    
    # Test 2: Clear context (start fresh)
    print("\n2. Clearing previous context...")
    result = test_endpoint("DELETE", "/clear-context")
    print(f"   Result: {result}")
    
    # Test 3: Test OCR with Math Problem
    print("\n3. Testing OCR with math problem...")
    math_problem = "Solve: 2x + 5 = 15\nStep 1: 2x = 15 - 5\nStep 2: 2x = 10"
    test_image = create_test_image_with_math_problem(math_problem)
    
    result = test_endpoint("POST", "/analyze-photo", {"image_base64": test_image})
    print(f"   OCR Result: {result}")
    
    # Wait a moment for context processing
    time.sleep(2)
    
    # Test 4: Check context status
    print("\n4. Checking context status...")
    result = test_endpoint("GET", "/context_status")
    print(f"   Context Status: {result}")
    
    # Test 5: Test is_different function
    print("\n5. Testing is_different with similar content...")
    result = test_endpoint("POST", "/is-different", {"text": math_problem})
    print(f"   Is Different: {result}")
    
    # Test 6: Test is_different with new content
    print("\n6. Testing is_different with new content...")
    new_problem = "Find the derivative of f(x) = x² + 3x + 2"
    result = test_endpoint("POST", "/is-different", {"text": new_problem})
    print(f"   Is Different: {result}")
    
    # Test 7: Test context compression
    print("\n7. Testing manual context compression...")
    result = test_endpoint("POST", "/context-compression", {"text": new_problem})
    print(f"   Compression Result: {result}")
    
    # Wait for processing
    time.sleep(2)
    
    # Test 8: Get context
    print("\n8. Getting current context...")
    result = test_endpoint("GET", "/get-context")
    print(f"   Context: {result}")
    
    # Test 9: Test hint generation
    print("\n9. Testing hint generation...")
    result = test_endpoint("POST", "/give-hint", {
        "learned": "I'm working on algebra problems",
        "question": "How do I solve 2x + 5 = 15?"
    })
    print(f"   Hint: {result}")
    
    # Test 10: Test hint generation with different question
    print("\n10. Testing hint generation with calculus question...")
    result = test_endpoint("POST", "/give-hint", {
        "learned": "I need help with calculus",
        "question": "How do I find derivatives?"
    })
    print(f"    Hint: {result}")
    
    # Test 11: Final context status
    print("\n11. Final context status...")
    result = test_endpoint("GET", "/context_status")
    print(f"    Final Status: {result}")
    
    print("\n" + "=" * 50)
    print("🎉 Thynk System Test Complete!")
    print("\nNext Steps:")
    print("1. Set up your Upstash Redis credentials in .env")
    print("2. Add your Anthropic API key in .env") 
    print("3. Test with real images from the smart glasses")
    print("4. Integrate the /give-hint endpoint with your frontend")

if __name__ == "__main__":
    main()