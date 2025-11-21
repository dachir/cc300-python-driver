import logging
from typing import Union
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
import uvicorn

from models import (
    StatusResponse, DeviceInfo, BillResponse,
    SaleBill, RefundBill
)
from device import CC300Device
from commands import get_info, create_bill


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cc300.main")


# Create FastAPI app
app = FastAPI(
    title="CC300 Driver API",
    description="Driver API for CC300 fiscal device",
    version="0.1.0"
)


@app.get("/check", response_model=StatusResponse)
async def check_device():
    """
    Check if the CC300 device is connected
    
    Returns:
        - 200: {"status": "Ready"} when device is connected
        - 503: {"status": "DeviceNotConnected"} when device is not connected
    """
    try:
        device = CC300Device()
        if device.open():
            device.close()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "Ready"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "DeviceNotConnected"}
            )
    except Exception as e:
        logger.error(f"Error checking device: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "DeviceNotConnected"}
        )


@app.get("/info", response_model=DeviceInfo)
async def get_device_info():
    """
    Get device and taxpayer information
    
    This request takes approximately 4 seconds to execute.
    
    Returns:
        - 200: Device information including NIM, IFU, counters, tax rates, company info
        - 503: {"status": "DeviceNotConnected"} when device is not connected
    """
    device = CC300Device()
    
    try:
        if not device.open():
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "DeviceNotConnected"}
            )
        
        # Get device information
        info = get_info(device)
        device.close()
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        device.close()
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "DeviceNotConnected"}
        )


@app.post("/bill", response_model=BillResponse)
async def create_new_bill(bill: Union[SaleBill, RefundBill]):
    """
    Create a new bill on the CC300 device
    
    The bill must conform to the JSON schema defined in bill.spec.json.
    Bills can be either sale bills (with 'vt' field) or refund bills (with 'rt' and 'rn' fields).
    
    Args:
        bill: Bill data with products, payments, and other required information
    
    Returns:
        - 200: {"qr_code": "F;NIM;COUNTER;IFU;TIMESTAMP"} when successful
        - 400: Validation errors
        - 503: {"status": "DeviceNotConnected"} when device is not connected
    """
    device = CC300Device()
    
    try:
        if not device.open():
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "DeviceNotConnected"}
            )
        
        # Create the bill
        qr_code = create_bill(device, bill)
        device.close()
        
        return BillResponse(qr_code=qr_code)
        
    except Exception as e:
        logger.error(f"Error creating bill: {e}")
        device.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/")
async def root():
    """Redirect to documentation"""
    return {
        "message": "CC300 Driver API",
        "documentation": "/docs",
        "endpoints": ["/check", "/info", "/bill"]
    }


def main():
    """Run the server"""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=38917,
        log_level="info"
    )


if __name__ == "__main__":
    main()
