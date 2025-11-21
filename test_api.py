#!/usr/bin/env python3
"""
Test script for CC300 Driver API
Tests the data models and API structure without requiring a physical device
"""

import json
from models import SaleBill, RefundBill, Payment, Product


def test_sale_bill_validation():
    """Test sale bill model validation"""
    print("Testing sale bill validation...")
    
    # Valid sale bill
    bill_data = {
        "seller_id": "SELLER123",
        "seller_name": "Test Shop",
        "vt": "FV",
        "buyer_ifu": "3201910768821",
        "buyer_name": "Test Client",
        "aib": "N/A",
        "payments": [
            {"mode": "E", "amount": 10000}
        ],
        "products": [
            {
                "label": "Test Product",
                "tax": "B",
                "price": 10000,
                "items": 1.0
            }
        ]
    }
    
    try:
        bill = SaleBill(**bill_data)
        print("✓ Valid sale bill created successfully")
        print(f"  Seller: {bill.seller_name}")
        print(f"  Type: {bill.vt}")
        print(f"  Products: {len(bill.products)}")
        print(f"  Payments: {len(bill.payments)}")
        return True
    except Exception as e:
        print(f"✗ Sale bill validation failed: {e}")
        return False


def test_refund_bill_validation():
    """Test refund bill model validation"""
    print("\nTesting refund bill validation...")
    
    # Valid refund bill
    bill_data = {
        "seller_id": "SELLER123",
        "seller_name": "Test Shop",
        "rt": "FA",
        "rn": "ED04000623-12345",
        "buyer_ifu": "3201910768821",
        "buyer_name": "Test Client",
        "payments": [
            {"mode": "E", "amount": 5000}
        ],
        "products": [
            {
                "label": "Returned Product",
                "tax": "B",
                "price": 5000
            }
        ]
    }
    
    try:
        bill = RefundBill(**bill_data)
        print("✓ Valid refund bill created successfully")
        print(f"  Seller: {bill.seller_name}")
        print(f"  Type: {bill.rt}")
        print(f"  Reference: {bill.rn}")
        print(f"  Products: {len(bill.products)}")
        return True
    except Exception as e:
        print(f"✗ Refund bill validation failed: {e}")
        return False


def test_complex_bill():
    """Test a more complex bill with multiple products and payments"""
    print("\nTesting complex bill with multiple items...")
    
    bill_data = {
        "seller_id": "SELLER456",
        "seller_name": "Complex Shop",
        "vt": "FV",
        "buyer_ifu": "3201910768821",
        "buyer_name": "VIP Client",
        "aib": "5%",
        "payments": [
            {"mode": "E", "amount": 15000},
            {"mode": "C", "amount": 10000}
        ],
        "products": [
            {
                "label": "Product with bar code",
                "bar_code": "1234567890123",
                "tax": "B",
                "price": 10000,
                "items": 2.0
            },
            {
                "label": "Product with specific tax",
                "tax": "B",
                "price": 5000,
                "items": 1.0,
                "specific_tax": 500,
                "specific_tax_desc": "Special levy"
            }
        ]
    }
    
    try:
        bill = SaleBill(**bill_data)
        print("✓ Complex bill created successfully")
        print(f"  Total products: {len(bill.products)}")
        print(f"  Total payments: {len(bill.payments)}")
        print(f"  AIB: {bill.aib}")
        
        # Calculate totals
        total_amount = sum(p.amount for p in bill.payments)
        print(f"  Total payment amount: {total_amount}")
        return True
    except Exception as e:
        print(f"✗ Complex bill validation failed: {e}")
        return False


def test_invalid_bill():
    """Test that invalid data is rejected"""
    print("\nTesting invalid bill data (should fail)...")
    
    # Missing required field
    bill_data = {
        "seller_id": "SELLER123",
        # Missing seller_name
        "vt": "FV",
        "payments": [{"mode": "E", "amount": 1000}],
        "products": [{"label": "Test", "tax": "B", "price": 1000}]
    }
    
    try:
        bill = SaleBill(**bill_data)
        print("✗ Invalid bill was accepted (should have failed)")
        return False
    except Exception as e:
        print(f"✓ Invalid bill correctly rejected: {type(e).__name__}")
        return True


def test_payment_modes():
    """Test all payment modes"""
    print("\nTesting payment modes...")
    
    modes = ["V", "C", "M", "D", "E", "A"]
    for mode in modes:
        try:
            payment = Payment(mode=mode, amount=1000)
            print(f"✓ Payment mode '{mode}' validated")
        except Exception as e:
            print(f"✗ Payment mode '{mode}' failed: {e}")
            return False
    
    return True


def test_tax_types():
    """Test all tax types"""
    print("\nTesting tax types...")
    
    taxes = ["A", "B", "C", "D", "E", "F"]
    for tax in taxes:
        try:
            product = Product(label="Test", tax=tax, price=1000)
            print(f"✓ Tax type '{tax}' validated")
        except Exception as e:
            print(f"✗ Tax type '{tax}' failed: {e}")
            return False
    
    return True


def test_json_serialization():
    """Test JSON serialization"""
    print("\nTesting JSON serialization...")
    
    bill_data = {
        "seller_id": "SELLER123",
        "seller_name": "Test Shop",
        "vt": "FV",
        "payments": [{"mode": "E", "amount": 10000}],
        "products": [{"label": "Test", "tax": "B", "price": 10000}]
    }
    
    try:
        bill = SaleBill(**bill_data)
        json_str = bill.model_dump_json()
        print("✓ Bill serialized to JSON successfully")
        
        # Try to parse it back
        parsed = json.loads(json_str)
        bill2 = SaleBill(**parsed)
        print("✓ Bill deserialized from JSON successfully")
        return True
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("CC300 Driver API - Data Model Tests")
    print("=" * 60)
    
    tests = [
        test_sale_bill_validation,
        test_refund_bill_validation,
        test_complex_bill,
        test_invalid_bill,
        test_payment_modes,
        test_tax_types,
        test_json_serialization,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
