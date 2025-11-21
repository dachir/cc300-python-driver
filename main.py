"""
CC300 Driver FastAPI Application
Main server implementation with HTTP endpoints
"""
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Union
import json
from jsonschema import validate, ValidationError as JsonSchemaValidationError

from device import open_device
from commands import get_device_info, create_bill
from models import (
    StatusResponse, DeviceInfo, BillResponse,
    SellBill, RefundBill
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CC300 Driver API",
    description="Driver API for Eltrade CC300 fiscal device",
    version="0.1.0"
)

# Load JSON schema for validation
with open("bill.spec.json", "r") as f:
    BILL_SCHEMA = json.load(f)


@app.get("/check", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def check_device():
    """
    Check if the CC300 device is connected
    
    Returns:
        - 200: Device is connected and ready
        - 503: Device not connected
    """
    logger.info("Checking device connection...")
    
    device = open_device()
    if device is None:
        logger.warning("Device not connected")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "DeviceNotConnected"}
        )
    
    try:
        # Device is open, it's ready
        logger.info("Device is ready")
        return {"status": "Ready"}
    finally:
        device.close()


@app.get("/info", response_model=DeviceInfo, status_code=status.HTTP_200_OK)
async def get_info():
    """
    Get device and taxpayer information
    
    Note: This request takes approximately 4 seconds to complete
    
    Returns:
        - 200: Device information
        - 503: Device not connected
    """
    logger.info("Getting device info...")
    
    device = open_device()
    if device is None:
        logger.warning("Device not connected")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "DeviceNotConnected"}
        )
    
    try:
        info = get_device_info(device)
        logger.info("Successfully retrieved device info")
        return info
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving device information: {str(e)}"
        )
    finally:
        device.close()


@app.post("/bill", response_model=BillResponse, status_code=status.HTTP_200_OK)
async def create_new_bill(bill_data: dict):
    """
    Create a new bill on the device
    
    The bill data must conform to the JSON schema defined in bill.spec.json
    
    Args:
        bill_data: Bill data (either SellBill or RefundBill)
    
    Returns:
        - 200: Bill created successfully with QR code
        - 400: Invalid bill data
        - 503: Device not connected
    """
    logger.info("Creating new bill...")
    
    # Validate against JSON schema
    try:
        validate(instance=bill_data, schema=BILL_SCHEMA)
    except JsonSchemaValidationError as e:
        logger.error(f"Bill validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid bill data: {e.message}"
        )
    
    device = open_device()
    if device is None:
        logger.warning("Device not connected")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "DeviceNotConnected"}
        )
    
    try:
        # Parse bill data into appropriate model
        if "vt" in bill_data:
            bill = SellBill(**bill_data)
        elif "rt" in bill_data:
            bill = RefundBill(**bill_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill must have either 'vt' (sell bill) or 'rt' (refund bill) field"
            )
        
        # Create bill on device
        qr_code = create_bill(device, bill)
        logger.info(f"Bill created successfully: {qr_code}")
        
        return {"qr_code": qr_code}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bill: {str(e)}"
        )
    finally:
        device.close()


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to documentation"""
    return {
        "message": "CC300 Driver API",
        "documentation": "/docs",
        "endpoints": {
            "check": "/check - Check device connection",
            "info": "/info - Get device information",
            "bill": "/bill - Create a bill (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting CC300 Driver API on http://localhost:38917")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=38917,
        log_level="info"
    )
