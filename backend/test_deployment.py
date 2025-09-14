#!/usr/bin/env python3
"""
Test script to verify Modal deployment and endpoints functionality
Run this after deploying to Modal to ensure everything works
"""

import requests
import base64
import json
import time
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_image(text: str) -> str:
    """Create a test image with text for OCR testing"""
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((20, 30), text, fill='black', font=font)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

def test_modal_deployment(modal_url: str):
    """Test all endpoints on Modal deployment"""
    print(f"🚀 Testing Modal deployment at: {modal_url}")
    print("=" * 60)
    
    # Test 1: Health check
    print("1️⃣ Testing /health endpoint...")
    try:
        response = requests.get(f"{modal_url}/health", timeout=30)
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    print()
    
    # Test 2: Root endpoint
    print("2️⃣ Testing / endpoint...")
    try:
        response = requests.get(f"{modal_url}/", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint passed")
            print(f"   Available endpoints: {data.get('endpoints', [])}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    print()
    
    # Test 3: OCR endpoint
    print("3️⃣ Testing /ocr endpoint...")
    test_text = "Hello Smart Glasses OCR Test"
    image_b64 = create_test_image(test_text)
    
    try:
        payload = {"image_base64": image_b64}
        response = requests.post(f"{modal_url}/ocr", json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ OCR endpoint passed")
            print(f"   Detected text: '{data['text']}'")
            print(f"   Confidence: {data['confidence']:.2f}")
            print(f"   Processing time: {data.get('processing_time', 'N/A')}s")
        else:
            print(f"❌ OCR endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ OCR endpoint error: {e}")
    
    print()
    
    # Test 4: Analysis endpoint
    print("4️⃣ Testing /analyze endpoint...")
    try:
        payload = {
            "text": "I need help with calculus derivatives",
            "context": "Smart glasses tutoring session"
        }
        response = requests.post(f"{modal_url}/analyze", json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis endpoint passed")
            print(f"   Analysis: {data['analysis'][:100]}...")
            print(f"   Suggestions count: {len(data.get('suggestions', []))}")
            print(f"   Confidence: {data['confidence']}")
        else:
            print(f"❌ Analysis endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Analysis endpoint error: {e}")
    
    print()
    
    # Test 5: Complete pipeline
    print("5️⃣ Testing /process-glasses-image endpoint...")
    pipeline_text = "Math problem: x^2 + 5x - 6 = 0"
    pipeline_image = create_test_image(pipeline_text)
    
    try:
        payload = {"image_base64": pipeline_image}
        response = requests.post(f"{modal_url}/process-glasses-image", json=payload, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pipeline endpoint passed")
            print(f"   OCR Success: {data['ocr_result']['success']}")
            print(f"   OCR Text: '{data['ocr_result']['text']}'")
            print(f"   Analysis Success: {data['analysis_result']['success']}")
            print(f"   Analysis: {data['analysis_result']['analysis'][:100]}...")
        else:
            print(f"❌ Pipeline endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Pipeline endpoint error: {e}")
    
    print()
    print("🏁 Modal deployment testing complete!")
    return True

if __name__ == "__main__":
    # You'll get this URL after running: modal deploy backend/main.py
    modal_url = input("Enter your Modal deployment URL (e.g., https://your-app--modal-fastapi-app.modal.run): ").strip()
    
    if not modal_url:
        print("❌ No URL provided. Deploy first with: modal deploy backend/main.py")
        exit(1)
    
    if not modal_url.startswith('http'):
        modal_url = f"https://{modal_url}"
    
    test_modal_deployment(modal_url)
