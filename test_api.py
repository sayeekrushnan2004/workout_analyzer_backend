"""
Test script for Posture Analysis API
Run this after starting the server to verify all endpoints work correctly
"""

import requests
import json
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# API Base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def create_test_image():
    """Create a simple test image"""
    # Create a 640x480 test image with random pixels
    img = Image.new('RGB', (640, 480), color=(73, 109, 137))
    
    # Save to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes

def test_start_session():
    """Test starting a posture session"""
    print("\n=== Testing Start Session ===")
    response = requests.post(f"{BASE_URL}/posture/start-session")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 200:
        return data.get('session_id')
    return None

def test_quick_analyze():
    """Test quick posture analysis without session"""
    print("\n=== Testing Quick Analyze ===")
    
    # Create test image
    img_bytes = create_test_image()
    
    files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
    response = requests.post(
        f"{BASE_URL}/posture/quick-analyze",
        files=files,
        params={'draw_landmarks': True}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Posture Status: {data.get('posture_status')}")
        print(f"Posture Score: {data.get('posture_score')}")
        print(f"Is Good Posture: {data.get('is_good_posture')}")
        print(f"Has Annotated Image: {'annotated_image' in data}")
        return True
    else:
        print(f"Error: {response.json()}")
    return False

def test_analyze_frame(session_id):
    """Test analyzing a frame with session"""
    print("\n=== Testing Analyze Frame ===")
    
    if not session_id:
        print("No session ID provided, skipping...")
        return False
    
    # Create test image
    img_bytes = create_test_image()
    
    files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
    response = requests.post(
        f"{BASE_URL}/posture/analyze-frame",
        files=files,
        params={
            'session_id': session_id,
            'draw_landmarks': True
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Posture Status: {data.get('posture_status')}")
        print(f"Posture Score: {data.get('posture_score')}")
        print(f"Session Stats: {json.dumps(data.get('session_stats'), indent=2)}")
        return True
    else:
        print(f"Error: {response.json()}")
    return False

def test_session_status(session_id):
    """Test getting session status"""
    print("\n=== Testing Get Session Status ===")
    
    if not session_id:
        print("No session ID provided, skipping...")
        return False
    
    response = requests.get(f"{BASE_URL}/posture/session-status/{session_id}")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Session Active: {data.get('is_active')}")
        print(f"Statistics: {json.dumps(data.get('statistics'), indent=2)}")
        return True
    else:
        print(f"Error: {response.json()}")
    return False

def test_end_session(session_id):
    """Test ending a session"""
    print("\n=== Testing End Session ===")
    
    if not session_id:
        print("No session ID provided, skipping...")
        return False
    
    response = requests.post(
        f"{BASE_URL}/posture/end-session",
        params={'session_id': session_id}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Message: {data.get('message')}")
        print(f"Final Statistics: {json.dumps(data.get('session_statistics'), indent=2)}")
        return True
    else:
        print(f"Error: {response.json()}")
    return False

def test_get_history():
    """Test getting posture history"""
    print("\n=== Testing Get History ===")
    
    response = requests.get(f"{BASE_URL}/posture/history", params={'limit': 5})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Session Count: {data.get('count')}")
        if data.get('sessions'):
            print(f"Latest Session: {json.dumps(data['sessions'][-1], indent=2)}")
        return True
    else:
        print(f"Error: {response.json()}")
    return False

def test_get_statistics():
    """Test getting overall statistics"""
    print("\n=== Testing Get Overall Statistics ===")
    
    response = requests.get(f"{BASE_URL}/posture/statistics")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Statistics: {json.dumps(data.get('statistics'), indent=2)}")
        return True
    else:
        print(f"Error: {response.json()}")
    return False

def test_get_active_sessions():
    """Test getting active sessions"""
    print("\n=== Testing Get Active Sessions ===")
    
    response = requests.get(f"{BASE_URL}/posture/active-sessions")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Active Session Count: {data.get('count')}")
        return True
    else:
        print(f"Error: {response.json()}")
    return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("POSTURE ANALYSIS API TEST SUITE")
    print("="*60)
    
    results = {}
    
    # Test 1: Health Check
    results['health_check'] = test_health_check()
    
    # Test 2: Quick Analyze (no session required)
    results['quick_analyze'] = test_quick_analyze()
    
    # Test 3: Full Session Flow
    session_id = test_start_session()
    results['start_session'] = session_id is not None
    
    if session_id:
        # Analyze a few frames
        for i in range(3):
            print(f"\n--- Analyzing Frame {i+1} ---")
            results[f'analyze_frame_{i+1}'] = test_analyze_frame(session_id)
        
        # Check session status
        results['session_status'] = test_session_status(session_id)
        
        # End session
        results['end_session'] = test_end_session(session_id)
    
    # Test 4: History and Statistics
    results['get_history'] = test_get_history()
    results['get_statistics'] = test_get_statistics()
    results['get_active_sessions'] = test_get_active_sessions()
    
    # Print Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running at http://localhost:8000")
        print("Start it with: python app.py")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
