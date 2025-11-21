#!/usr/bin/env python3
"""
Example usage of the CC300 Driver API

This script demonstrates how to interact with the CC300 Driver API
using Python requests library.

Note: The server must be running for this example to work.
Start the server with: python main.py
"""

import requests
import json


# API base URL
BASE_URL = "http://localhost:38917"


def check_device():
    """Check if the CC300 device is connected"""
    print("=" * 60)
    print("Checking device connection...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/check", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Device is connected and ready")
        else:
            print("✗ Device is not connected")
        
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to API: {e}")
        print("\nMake sure the server is running: python main.py")
        return False


def get_device_info():
    """Get device and taxpayer information"""
    print("\n" + "=" * 60)
    print("Getting device information...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/info", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            info = response.json()
            print("✓ Device information retrieved:")
            print(f"  NIM: {info.get('NIM')}")
            print(f"  IFU: {info.get('IFU')}")
            print(f"  Company: {info.get('CompanyName')}")
            print(f"  Bill Counter: {info.get('COUNTER')}")
            print(f"  Tax Rate B: {info.get('TaxB')}%")
            print("\nFull response:")
            print(json.dumps(info, indent=2))
        else:
            print("✗ Could not retrieve device information")
            print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")


def create_sale_bill():
    """Create a sample sale bill"""
    print("\n" + "=" * 60)
    print("Creating a sale bill...")
    print("=" * 60)
    
    # Example sale bill
    bill_data = {
        "seller_id": "EXAMPLE001",
        "seller_name": "Example Store",
        "vt": "FV",  # Facture de vente
        "buyer_ifu": "3201910768821",
        "buyer_name": "Example Customer",
        "aib": "N/A",
        "payments": [
            {
                "mode": "E",  # Cash
                "amount": 15000
            }
        ],
        "products": [
            {
                "label": "Example Product 1",
                "bar_code": "1234567890",
                "tax": "B",  # Taxable
                "price": 10000,
                "items": 1.0
            },
            {
                "label": "Example Product 2",
                "tax": "B",
                "price": 5000,
                "items": 1.0
            }
        ]
    }
    
    print("Bill data:")
    print(json.dumps(bill_data, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/bill",
            json=bill_data,
            timeout=10
        )
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Bill created successfully!")
            print(f"  QR Code: {result.get('qr_code')}")
        else:
            print("✗ Failed to create bill")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")


def create_refund_bill():
    """Create a sample refund bill"""
    print("\n" + "=" * 60)
    print("Creating a refund bill...")
    print("=" * 60)
    
    # Example refund bill
    bill_data = {
        "seller_id": "EXAMPLE001",
        "seller_name": "Example Store",
        "rt": "FA",  # Facture d'avoir
        "rn": "ED04000623-12345",  # Reference to original bill
        "buyer_ifu": "3201910768821",
        "buyer_name": "Example Customer",
        "payments": [
            {
                "mode": "E",  # Cash
                "amount": 5000
            }
        ],
        "products": [
            {
                "label": "Returned Product",
                "tax": "B",
                "price": 5000,
                "items": 1.0
            }
        ]
    }
    
    print("Bill data:")
    print(json.dumps(bill_data, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/bill",
            json=bill_data,
            timeout=10
        )
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Refund bill created successfully!")
            print(f"  QR Code: {result.get('qr_code')}")
        else:
            print("✗ Failed to create refund bill")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")


def main():
    """Run example operations"""
    print("CC300 Driver API - Example Usage")
    print("=" * 60)
    
    # Check device
    if not check_device():
        print("\nNote: Device checks will fail without a physical CC300 device.")
        print("The API is still running and you can test with the interactive docs.")
        print(f"Visit: {BASE_URL}/docs")
        return
    
    # Get device info
    get_device_info()
    
    # Create bills (comment out if you don't want to create actual bills)
    # create_sale_bill()
    # create_refund_bill()
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print(f"View interactive API docs at: {BASE_URL}/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
