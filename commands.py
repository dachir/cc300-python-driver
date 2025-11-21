"""
Commands module for CC300 device operations
"""
import logging
from datetime import datetime
from typing import Dict, Union, Optional
from device import (
    Device, Request,
    DEV_STATE, NETWORK_STATE, TAXPAYER_INFO,
    START_BILL, ADD_BILL_ITEM, GET_BILL_TOTAL, END_BILL,
    RESPONSE_DELIMITER
)
from models import SellBill, RefundBill

logger = logging.getLogger(__name__)


def get_device_state(device: Device) -> Dict[str, str]:
    """Get device state information"""
    request = Request(cmd=DEV_STATE, data=b'')
    response = device.send(request)
    
    data = response.get_data()
    if not data:
        raise Exception("Failed to get device state")
    
    # Parse comma-separated response
    parts = data.split(chr(RESPONSE_DELIMITER))
    logger.debug(f"Device state response: {parts}")
    
    if len(parts) < 10:
        raise Exception("Invalid device state response")
    
    # Parse datetime (format: YYYYMMDDHHMMSS)
    try:
        dt = datetime.strptime(parts[2], "%Y%m%d%H%M%S")
        # Format as string with timezone
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S") + " +0100 WAT"
    except Exception as e:
        logger.warning(f"Failed to parse datetime: {e}")
        time_str = parts[2]
    
    return {
        "NIM": parts[0],
        "IFU": parts[1],
        "TIME": time_str,
        "COUNTER": parts[3],
        "SellBillCounter": parts[4],
        "SettlementBillCounter": parts[5],
        "TaxA": parts[6],
        "TaxB": parts[7],
        "TaxC": parts[8],
        "TaxD": parts[9]
    }


def get_tax_server_state(device: Device) -> Dict[str, str]:
    """Get tax server state information"""
    request = Request(cmd=NETWORK_STATE, data=b'')
    response = device.send(request)
    
    data = response.get_data()
    if not data:
        raise Exception("Failed to get tax server state")
    
    parts = data.split(chr(RESPONSE_DELIMITER))
    logger.debug(f"Tax server state response: {parts}")
    
    if len(parts) < 3:
        raise Exception("Invalid tax server state response")
    
    # Parse datetime
    try:
        dt = datetime.strptime(parts[2], "%Y%m%d%H%M%S")
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S") + " +0100 WAT"
    except Exception as e:
        logger.warning(f"Failed to parse datetime: {e}")
        time_str = parts[2]
    
    return {
        "UploadedDocumentCount": parts[0],
        "DocumentOnDeviceCount": parts[1],
        "LastConnectionToServer": time_str
    }


def get_taxpayer_info(device: Device) -> Dict[str, str]:
    """Get taxpayer information"""
    info = {}
    
    # Query different info fields (I0 to I5)
    info_fields = {
        0: "CompanyName",
        1: "CompanyLocationAddress",
        2: "CompanyLocationAddress2",  # Will be appended to address
        3: "CompanyLocationCity",
        4: "CompanyContactPhone",
        5: "CompanyContactEmail"
    }
    
    for i, field_name in info_fields.items():
        data = f"I{i}".encode('utf-8')
        request = Request(cmd=TAXPAYER_INFO, data=data)
        response = device.send(request)
        
        field_data = response.get_data()
        if field_data:
            if i == 2:
                # Append to address
                info["CompanyLocationAddress"] = info.get("CompanyLocationAddress", "") + " " + field_data
            else:
                info[field_name] = field_data
        else:
            logger.warning(f"Failed to get taxpayer info field {i}")
            info[field_name] = ""
    
    return info


def get_device_info(device: Device) -> Dict[str, str]:
    """Get complete device information"""
    info = {}
    
    # Get device state
    device_state = get_device_state(device)
    info.update(device_state)
    
    # Get taxpayer info
    taxpayer_info = get_taxpayer_info(device)
    info.update(taxpayer_info)
    
    # Get tax server state
    tax_server_state = get_tax_server_state(device)
    info.update(tax_server_state)
    
    return info


def create_bill(device: Device, bill: Union[SellBill, RefundBill]) -> str:
    """Create a bill on the device"""
    # Get device state for IFU and tax rates
    device_state = get_device_state(device)
    
    # Prepare START_BILL command
    parts = [
        bill.seller_id,
        bill.seller_name,
        device_state["IFU"],
        device_state["TaxA"],
        device_state["TaxB"],
        device_state["TaxC"],
        device_state["TaxD"]
    ]
    
    # Add bill type specific fields
    if isinstance(bill, SellBill):
        parts.append(bill.vt)
        parts.append("")  # RT empty for sell bills
        parts.append("")  # RN empty for sell bills
    else:  # RefundBill
        parts.append("")  # VT empty for refund bills
        parts.append(bill.rt)
        parts.append(bill.rn)
    
    # Add buyer info
    parts.append(bill.buyer_ifu or "")
    parts.append(bill.buyer_name or "")
    
    # Add AIB if not N/A
    if bill.aib and bill.aib != "N/A":
        parts.append(bill.aib)
    
    # Join with tab separator and encode
    start_data = "\t".join(parts).encode('utf-8')
    request = Request(cmd=START_BILL, data=start_data)
    response = device.send(request)
    
    result = response.get_data()
    if not result:
        raise Exception("Failed to start bill")
    
    if result.startswith("E:"):
        raise Exception(f"Device error: {result}")
    
    logger.info(f"Started bill: {result}")
    
    # Add products
    for product in bill.products:
        product_parts = []
        
        # Label
        product_parts.append(product.label)
        
        # Bar code (on new line if present)
        if product.bar_code:
            product_parts.append(f"\n{product.bar_code}")
        
        # Empty separator
        product_parts.append("\t")
        
        # Tax
        product_parts.append(product.tax)
        
        # Price
        product_parts.append(f"{product.price:.2f}")
        
        # Quantity (with * separator)
        if product.items:
            product_parts.append(f"*{product.items:.3f}")
        
        # Specific tax (with ; separator)
        if product.specific_tax:
            product_parts.append(f";{product.specific_tax:.2f}")
            if product.specific_tax_desc:
                product_parts.append(f"\t{product.specific_tax_desc}")
        
        # Original price (with \t separator)
        if product.original_price:
            product_parts.append(f"\t{product.original_price:.2f}")
            if product.price_change_explanation:
                product_parts.append(f",{product.price_change_explanation}")
        
        product_data = "".join(product_parts).encode('utf-8')
        request = Request(cmd=ADD_BILL_ITEM, data=product_data)
        response = device.send(request)
        
        result = response.get_data()
        if not result:
            raise Exception(f"Failed to add product: {product.label}")
        
        logger.info(f"Added product: {product.label}")
    
    # Process payments
    for payment in bill.payments:
        for attempt in range(3):
            payment_data = f"{payment.mode}{payment.amount:.2f}".encode('utf-8')
            request = Request(cmd=GET_BILL_TOTAL, data=payment_data)
            response = device.send(request)
            
            result = response.get_data()
            if not result:
                raise Exception(f"Failed to process payment")
            
            # Check if payment accepted (starts with 'R')
            if result.startswith('R') or attempt == 2:
                logger.info(f"Processed payment: {payment.mode} {payment.amount}")
                break
    
    # End bill
    request = Request(cmd=END_BILL, data=b'')
    response = device.send(request)
    
    result = response.get_data()
    if not result:
        raise Exception("Failed to end bill")
    
    # Parse result: should contain comma-separated values
    parts = result.split(',')
    logger.debug(f"End bill response: {parts}")
    
    if len(parts) < 7:
        raise Exception(f"Invalid bill response: {result}")
    
    # Build QR code: F;NIM;CODE;IFU;DATETIME
    # parts[4] = NIM, parts[6] = CODE, parts[5] = IFU, parts[3] = DATETIME
    qr_code = f"F;{parts[4]};{parts[6]};{parts[5]};{parts[3]}"
    
    logger.info(f"Created bill with QR code: {qr_code}")
    return qr_code
