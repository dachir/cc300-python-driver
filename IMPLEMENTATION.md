# CC300 Python Driver - Implementation Details

## Overview

This document provides technical details about the implementation of the CC300 Python driver, based on the reference Go implementation at https://github.com/dachir/eltrade-cc300-driver.

## Architecture

### Project Structure

```
cc300-python-driver/
├── main.py              # FastAPI application with HTTP endpoints
├── models.py            # Pydantic data models for validation
├── device.py            # Low-level serial communication with CC300
├── commands.py          # High-level device commands
├── requirements.txt     # Python dependencies
├── bill.spec.json       # JSON schema for bill validation
├── test_api.py          # Test suite for data models
├── example.py           # Usage examples
├── run.sh               # Startup script
├── README.md            # User documentation
└── .gitignore           # Git ignore rules
```

## Core Components

### 1. main.py - FastAPI Application

Implements the REST API with three endpoints:

- **GET /check**: Device connectivity check
  - Returns 200 with `{"status": "Ready"}` if device is connected
  - Returns 503 with `{"status": "DeviceNotConnected"}` otherwise

- **GET /info**: Device and taxpayer information
  - Retrieves device state, taxpayer info, and tax server state
  - Takes ~4 seconds due to multiple serial operations
  - Returns comprehensive JSON with NIM, IFU, counters, tax rates, company info

- **POST /bill**: Create a fiscal bill
  - Validates input using Pydantic models
  - Supports both sale bills (vt) and refund bills (rt/rn)
  - Returns QR code in format: `F;NIM;COUNTER;IFU;TIMESTAMP`

### 2. models.py - Data Validation

Uses Pydantic v2 for data validation and serialization:

- **Payment**: Payment mode (V/C/M/D/E/A) and amount
- **Product**: Label, tax type, price, optional bar code, quantities, specific taxes
- **SaleBill**: Sale bill with 'vt' field
- **RefundBill**: Refund bill with 'rt' and 'rn' fields
- **DeviceInfo**: Complete device information response
- **StatusResponse**: Simple status response
- **BillResponse**: QR code response

All models include validation constraints (max length, enums, required fields).

### 3. device.py - Serial Communication

Implements the CC300 communication protocol:

#### Protocol Details

The CC300 uses a packet-based serial protocol at 115200 baud:

**Request Packet Structure:**
```
[SOH] [LEN] [SEQ] [CMD] [DATA...] [ETX] [BCC] [AMB]
```

- SOH (0x01): Start of header
- LEN: Packet length + 0x24 offset
- SEQ (0x20-0xFF): Sequence number
- CMD: Command code
- DATA: Command-specific data
- ETX (0x03): End of text
- BCC: XOR checksum of SEQ through ETX
- AMB (0x05): End of packet

**Response Packet Structure:**
```
[SOH] [LEN] [SEQ] [CMD] [DATA...] [BRK] [STATUS...] [ETX] [BCC] [AMB]
```

#### Device Identification

- Vendor ID (VID): 0x03EB
- Product ID (PID): 0x6119

The driver automatically detects the CC300 device by scanning USB serial ports.

#### Command Codes

- 0xC1: Get device state (NIM, IFU, time, counters, tax rates)
- 0xC2: Get network state (document counts, last server connection)
- 0x2B: Get taxpayer info (company details)
- 0xC0: Start bill
- 0x31: Add bill item
- 0x35: Get bill total (process payments)
- 0x38: End bill and get QR code

### 4. commands.py - High-Level Operations

Implements business logic for device operations:

- **get_device_state()**: Retrieves device state, parses timestamp
- **get_tax_server_state()**: Gets server connection status
- **get_taxpayer_info()**: Queries company information (6 queries)
- **get_info()**: Combines all info into DeviceInfo model
- **create_bill()**: Multi-step process to create a bill:
  1. Start bill with seller/buyer info
  2. Add each product
  3. Process payments (retry logic)
  4. End bill and get QR code

## Protocol Implementation Details

### Data Formatting

The device expects comma-separated values (0x2C) for most commands:

```python
# Example: Start bill command
data = "SELLER123,Shop Name,IFU123,0.00,18.00,0.00,18.00,FV,,,,"
```

### Timestamp Handling

Timestamps are formatted as `YYYYMMDDHHmmss` and converted to human-readable format with WAT timezone.

### Error Handling

- Responses starting with "E:" indicate errors
- Invalid/incomplete responses raise exceptions
- Device not found returns appropriate HTTP status codes

## Testing

### test_api.py

Comprehensive test suite covering:
- Sale bill validation
- Refund bill validation
- Complex bills with multiple products/payments
- Invalid data rejection
- All payment modes (V/C/M/D/E/A)
- All tax types (A/B/C/D/E/F)
- JSON serialization/deserialization

All tests pass successfully.

## Security

- No vulnerabilities found by CodeQL analysis
- Proper exception handling (catches specific exceptions)
- No hardcoded credentials or secrets
- Input validation via Pydantic models
- Serial communication properly isolated

## Compatibility

This implementation maintains API compatibility with the original Go driver:
- Same port (38917)
- Same endpoint paths
- Same JSON schema
- Same response formats

## Dependencies

- **fastapi**: Modern web framework with automatic API docs
- **uvicorn**: ASGI server for FastAPI
- **pydantic**: Data validation and settings management
- **pyserial**: Serial port communication
- **jsonschema**: JSON schema validation

## Running the Service

### Development Mode
```bash
python3 main.py
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 38917
```

### Using the Startup Script
```bash
./run.sh
```

## API Documentation

Interactive documentation is automatically generated and available at:
- Swagger UI: http://localhost:38917/docs
- ReDoc: http://localhost:38917/redoc

## Future Enhancements

Potential improvements:
- Add authentication/authorization
- Implement async device communication
- Add caching for device info
- Support multiple concurrent requests
- Add comprehensive logging configuration
- Create Windows service installer
- Add Docker support

## Reference

Original implementation: https://github.com/dachir/eltrade-cc300-driver
