"""
Simple test script to validate the CC300 Driver API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:38917"


def test_root():
    """Test root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert "endpoints" in response.json()
    print("✓ Root endpoint OK\n")


def test_check():
    """Test check endpoint"""
    print("Testing check endpoint...")
    response = requests.get(f"{BASE_URL}/check")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # Either device is connected (200) or not connected (503)
    assert response.status_code in [200, 503]
    assert "status" in response.json()
    print("✓ Check endpoint OK\n")


def test_info():
    """Test info endpoint"""
    print("Testing info endpoint...")
    response = requests.get(f"{BASE_URL}/info")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # Either device is connected (200) or not connected (503)
    assert response.status_code in [200, 503]
    print("✓ Info endpoint OK\n")


def test_bill_validation():
    """Test bill endpoint with invalid data"""
    print("Testing bill endpoint with invalid data...")
    
    # Test with empty data
    response = requests.post(
        f"{BASE_URL}/bill",
        json={}
    )
    print(f"Status: {response.status_code}")
    assert response.status_code == 400  # Bad request
    print("✓ Bill validation works\n")


def test_bill_valid():
    """Test bill endpoint with valid data"""
    print("Testing bill endpoint with valid data...")
    
    # Load example bill
    with open("example_bill.json", "r") as f:
        bill_data = json.load(f)
    
    response = requests.post(
        f"{BASE_URL}/bill",
        json=bill_data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # Either device is connected (200) or not connected (503)
    assert response.status_code in [200, 503]
    print("✓ Bill endpoint OK\n")


def test_openapi():
    """Test OpenAPI documentation"""
    print("Testing OpenAPI documentation...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "paths" in openapi_spec
    assert "/check" in openapi_spec["paths"]
    assert "/info" in openapi_spec["paths"]
    assert "/bill" in openapi_spec["paths"]
    print("✓ OpenAPI documentation OK\n")


if __name__ == "__main__":
    print("=" * 60)
    print("CC300 Driver API Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_root()
        test_check()
        test_info()
        test_bill_validation()
        test_bill_valid()
        test_openapi()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Make sure the server is running:")
        print("  python main.py")
    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
