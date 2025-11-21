# CC300 Python Driver - Implementation Notes

## Overview

This document provides technical details about the Python implementation of the CC300 driver, based on the reference Go implementation at https://github.com/dachir/eltrade-cc300-driver.

## Architecture

### Components

1. **main.py** - FastAPI application with REST endpoints
2. **device.py** - Serial communication and protocol handling
3. **commands.py** - High-level device operations
4. **models.py** - Pydantic data models for validation
5. **bill.spec.json** - JSON schema for bill validation

### Data Flow

```
HTTP Request → FastAPI → Commands → Device Protocol → Serial Port → CC300 Device
                ↓           ↓           ↓                 ↓
            Validation   Business    Protocol         Hardware
                         Logic      Encoding
```

## Protocol Implementation

### Message Format

The CC300 uses a custom binary protocol over serial communication:

**Request**: `<SOH><LEN><SEQ><CMD><DATA><AMB><BCC><ETX>`
- SOH (0x01): Start of header
- LEN: Data length + 0x24 offset
- SEQ: Sequential number (0x20-0xFF)
- CMD: Command code
- DATA: Command-specific data
- AMB (0x05): Separator
- BCC: Block check character (XOR checksum)
- ETX (0x03): End of transmission

**Response**: `<SOH><LEN><SEQ><CMD><DATA><BRK><STATUS><AMB><BCC><ETX>`
- BRK (0x04): Separator before status
- STATUS: Response status byte

### Command Codes

- `0xC1` - Get device state (NIM, IFU, counters, tax rates)
- `0xC2` - Get network state (server connection, document counts)
- `0x2B` - Get taxpayer info (company details)
- `0xC0` - Start bill
- `0x31` - Add bill item
- `0x35` - Get bill total (process payment)
- `0x38` - End bill

## API Endpoints

### GET /check
- **Purpose**: Verify device connection
- **Response Codes**: 200 (Ready), 503 (DeviceNotConnected)
- **No device required for testing**: Always returns appropriate status

### GET /info
- **Purpose**: Get complete device and taxpayer information
- **Execution Time**: ~4 seconds (multiple serial queries)
- **Response**: Combined data from three device commands
- **No device required for testing**: Returns 503 when device not connected

### POST /bill
- **Purpose**: Create a bill on the device
- **Validation**: Two-stage (JSON schema + Pydantic)
- **Bill Types**:
  - Sell bills (vt field): FV, CV, EV, EC
  - Refund bills (rt field): FA, CA, EA, ER
- **Response**: QR code string in format `F;NIM;CODE;IFU;DATETIME`

## Serial Communication

### Device Detection

The driver searches for devices with:
- **VID**: 03EB (Atmel/Microchip)
- **PID**: 6119 (CC300 device)

### Connection Parameters

- **Baudrate**: 115200
- **Data bits**: 8
- **Stop bits**: 1
- **Parity**: None
- **Timeout**: 0.5s

### Read Strategy

The implementation reads responses byte-by-byte until ETX is found, which:
- Ensures complete message reception
- Handles variable-length responses
- Prevents buffer overflows
- Supports SYN responses (for long commands)

## Error Handling

### Device Errors

1. **Connection Errors**: Return 503 with DeviceNotConnected status
2. **Protocol Errors**: Logged with debug information
3. **Validation Errors**: Return 400 with detailed error message
4. **Device Response Errors**: Return 500 with error details

### Logging Strategy

- **DEBUG**: Protocol details (hex dumps, parsed responses)
- **INFO**: Major operations (device opened, bill created)
- **WARNING**: Non-critical issues (device not found)
- **ERROR**: Failures requiring attention

## Testing

### Test Suite (test_api.py)

Tests all endpoints without requiring physical device:
- Root endpoint information
- Device connection check
- Info retrieval
- Bill validation (invalid data)
- Bill creation (valid data)
- OpenAPI documentation

### Manual Testing

```bash
# Start server
python main.py

# Test in another terminal
curl http://localhost:38917/check
curl http://localhost:38917/info
curl -X POST http://localhost:38917/bill -H "Content-Type: application/json" -d @example_bill.json
```

## Differences from Go Implementation

### Improvements

1. **Type Safety**: Pydantic provides runtime validation
2. **API Documentation**: Automatic OpenAPI/Swagger docs
3. **Async Support**: FastAPI's async capabilities
4. **Better Error Messages**: Detailed validation feedback

### Equivalents

1. **Serial Communication**: pyserial ≈ go-serial
2. **Schema Validation**: jsonschema ≈ gojsonschema
3. **HTTP Server**: FastAPI/Uvicorn ≈ net/http
4. **Data Encoding**: Manual bytes ≈ Go's byte handling

## Deployment

### Requirements

- Python 3.8+
- USB serial drivers for CC300
- Port 38917 available

### Production Considerations

1. **Logging**: Configure appropriate log levels
2. **Error Handling**: Monitor device connection issues
3. **Timeouts**: Adjust serial timeouts if needed
4. **Security**: Consider adding authentication
5. **CORS**: Add CORS middleware if needed for web clients

### Running as Service

The application can be run as:
- **Standalone**: `python main.py`
- **With uvicorn**: `uvicorn main:app --host 0.0.0.0 --port 38917`
- **Systemd service**: Create unit file for auto-start

## Future Enhancements

Potential improvements:
1. Authentication/Authorization
2. WebSocket support for real-time updates
3. Device connection pooling
4. Async device operations
5. Prometheus metrics
6. Docker container support
7. Configuration file support

## References

- Original Go implementation: https://github.com/dachir/eltrade-cc300-driver
- CC300 Protocol: MECeF_MCF_SFE_Protocole_v2.pdf
- FastAPI docs: https://fastapi.tiangolo.com/
- PySerial docs: https://pythonhosted.org/pyserial/
