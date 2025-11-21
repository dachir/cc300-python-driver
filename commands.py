import logging
from datetime import datetime
from typing import Dict, Any, Union
from models import DeviceInfo, SaleBill, RefundBill
from device import (
    CC300Device, Request,
    CMD_DEV_STATE, CMD_NETWORK_STATE, CMD_TAXPAYER_INFO,
    CMD_START_BILL, CMD_ADD_BILL_ITEM, CMD_GET_BILL_TOTAL, CMD_END_BILL,
    RESPONSE_DELIMITER
)


logger = logging.getLogger("cc300.commands")


# Timezone for date parsing
TIMEZONE_NAME = "Africa/Porto-Novo"


def get_device_state(device: CC300Device) -> Dict[str, str]:
    """Get device state information"""
    request = Request(CMD_DEV_STATE)
    response = device.send(request)
    data = response.get_data()
    
    data_parts = data.split(RESPONSE_DELIMITER)
    logger.debug(f"Device state response: {data_parts}")
    
    result = {}
    if len(data_parts) >= 10:
        result["NIM"] = data_parts[0]
        result["IFU"] = data_parts[1]
        
        # Parse timestamp
        try:
            dt = datetime.strptime(data_parts[2], "%Y%m%d%H%M%S")
            result["TIME"] = dt.strftime("%Y-%m-%d %H:%M:%S +0100 WAT")
        except ValueError:
            result["TIME"] = data_parts[2]
        
        result["COUNTER"] = data_parts[3]
        result["SellBillCounter"] = data_parts[4]
        result["SettlementBillCounter"] = data_parts[5]
        result["TaxA"] = data_parts[6]
        result["TaxB"] = data_parts[7]
        result["TaxC"] = data_parts[8]
        result["TaxD"] = data_parts[9]
    
    return result


def get_tax_server_state(device: CC300Device) -> Dict[str, str]:
    """Get tax server connection state"""
    request = Request(CMD_NETWORK_STATE)
    response = device.send(request)
    data = response.get_data()
    
    data_parts = data.split(RESPONSE_DELIMITER)
    logger.debug(f"Tax server state response: {data_parts}")
    
    result = {}
    if len(data_parts) >= 3:
        result["UploadedDocumentCount"] = data_parts[0]
        result["DocumentOnDeviceCount"] = data_parts[1]
        
        # Parse timestamp
        try:
            dt = datetime.strptime(data_parts[2], "%Y%m%d%H%M%S")
            result["LastConnectionToServer"] = dt.strftime("%Y-%m-%d %H:%M:%S +0100 WAT")
        except ValueError:
            result["LastConnectionToServer"] = data_parts[2]
    
    return result


def get_taxpayer_info(device: CC300Device) -> Dict[str, str]:
    """Get taxpayer information"""
    result = {}
    
    # Query each info field (I0 to I5)
    info_fields = [
        ("I0", "CompanyName"),
        ("I1", "CompanyLocationAddress"),
        ("I2", "CompanyLocationAddressPart2"),
        ("I3", "CompanyLocationCity"),
        ("I4", "CompanyContactPhone"),
        ("I5", "CompanyContactEmail"),
    ]
    
    for field_code, field_name in info_fields:
        request = Request(CMD_TAXPAYER_INFO)
        request.set_body(field_code)
        response = device.send(request)
        data = response.get_data()
        logger.debug(f"Taxpayer info {field_code}: {data}")
        
        if field_name == "CompanyLocationAddressPart2":
            # Append to address
            if "CompanyLocationAddress" in result:
                result["CompanyLocationAddress"] += " " + data
        else:
            result[field_name] = data
    
    return result


def get_info(device: CC300Device) -> DeviceInfo:
    """Get complete device information"""
    info = {}
    
    # Get device state
    info.update(get_device_state(device))
    
    # Get taxpayer info
    info.update(get_taxpayer_info(device))
    
    # Get tax server state
    info.update(get_tax_server_state(device))
    
    return DeviceInfo(**info)


def create_bill(device: CC300Device, bill: Union[SaleBill, RefundBill]) -> str:
    """Create a bill and return QR code"""
    
    # Get device info for IFU and tax rates
    device_state = get_device_state(device)
    
    # Build start bill command
    request = Request(CMD_START_BILL)
    
    # Build data string with commas as delimiters
    parts = [
        bill.seller_id,
        bill.seller_name,
        device_state.get("IFU", ""),
        device_state.get("TaxA", ""),
        device_state.get("TaxB", ""),
        device_state.get("TaxC", ""),
        device_state.get("TaxD", ""),
    ]
    
    # Add bill type
    if isinstance(bill, SaleBill):
        parts.append(bill.vt)
        parts.append("")  # RT empty for sale bills
        parts.append("")  # RN empty for sale bills
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
    
    request.set_body(RESPONSE_DELIMITER.join(parts))
    response = device.send(request)
    result = response.get_data()
    
    if "E:" in result:
        raise Exception(f"Device initialization failed: {result}")
    
    # Add products
    request = Request(CMD_ADD_BILL_ITEM)
    for product in bill.products:
        parts = []
        
        # Product label
        parts.append(product.label)
        
        # Bar code if present
        if product.bar_code:
            parts.append(f"\n{product.bar_code}")
        
        # Tab separator
        parts.append("\t")
        
        # Tax, price, quantity
        parts.append(product.tax)
        parts.append(str(product.price))
        parts.append(f"*{product.items if product.items else 1.0}")
        
        # Specific tax if present
        if product.specific_tax:
            parts.append(f";{product.specific_tax}")
            if product.specific_tax_desc:
                parts.append(product.specific_tax_desc)
        
        # Original price and explanation if present
        if product.original_price:
            parts.append(f"\t{product.original_price}")
            if product.price_change_explanation:
                parts.append(f",{product.price_change_explanation}")
        
        request.set_body("".join(parts))
        response = device.send(request)
        result = response.get_data()
        
        if "E:" in result:
            raise Exception(f"Failed to add product: {result}")
    
    # Process payments
    request = Request(CMD_GET_BILL_TOTAL)
    for payment in bill.payments:
        payment_str = f"{payment.mode}{payment.amount}"
        
        # Retry up to 3 times
        for attempt in range(3):
            request.set_body(payment_str)
            response = device.send(request)
            result = response.get_data()
            
            if result and result[0] == 'R':
                break
            
            if attempt >= 2:
                break
    
    # End bill
    request = Request(CMD_END_BILL)
    request.set_body("")
    response = device.send(request)
    result = response.get_data()
    
    # Parse result: expecting format with comma-separated values
    result_parts = result.split(RESPONSE_DELIMITER)
    logger.debug(f"End bill response: {result_parts}")
    
    if len(result_parts) < 7:
        raise Exception(f"Invalid command response: {result}")
    
    # Build QR code: F;NIM;COUNTERS;IFU;TIMESTAMP
    # From Go code: fmt.Sprintf("F;%s;%s;%s;%s", splitedRes[4], splitedRes[6], splitedRes[5], splitedRes[3])
    qr_code = f"F;{result_parts[4]};{result_parts[6]};{result_parts[5]};{result_parts[3]}"
    
    return qr_code
