# Quick Start Guide - CC300 Python Driver

## Installation (5 minutes)

### Step 1: Clone the repository
```bash
git clone https://github.com/dachir/cc300-python-driver.git
cd cc300-python-driver
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Start the server
```bash
python main.py
```

You should see:
```
INFO - Starting CC300 Driver API on http://localhost:38917
INFO - Uvicorn running on http://0.0.0.0:38917
```

## Testing (2 minutes)

### Test without device (returns 503 - device not connected)

```bash
# Check device connection
curl http://localhost:38917/check

# Expected response:
{"status":"DeviceNotConnected"}
```

### Test with device connected (returns 200 - success)

1. Connect your CC300 device via USB
2. Restart the server: `python main.py`
3. Test the endpoints:

```bash
# Check device
curl http://localhost:38917/check
# Expected: {"status":"Ready"}

# Get device information
curl http://localhost:38917/info
# Expected: Full device info JSON

# Create a bill
curl -X POST http://localhost:38917/bill \
  -H "Content-Type: application/json" \
  -d @example_bill.json
# Expected: {"qr_code":"F;..."}
```

## Interactive Documentation

Open your browser and go to: **http://localhost:38917/docs**

This provides:
- Interactive API testing
- Request/response schemas
- Example values
- Try it out functionality

## Common Issues

### Device not detected
**Problem**: Returns `{"status":"DeviceNotConnected"}` even with device connected

**Solutions**:
1. Check USB connection
2. Verify device VID:PID (should be 03EB:6119)
3. On Linux: Add user to `dialout` group
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```
4. Check device appears in system:
   ```bash
   # Linux/Mac
   ls -la /dev/tty*
   
   # Or use Python
   python -m serial.tools.list_ports
   ```

### Port already in use
**Problem**: `Address already in use`

**Solution**: Kill existing process or change port
```bash
# Kill process on port 38917
lsof -ti:38917 | xargs kill -9

# Or change port in main.py (bottom of file)
uvicorn.run(app, host="0.0.0.0", port=8000)  # Use different port
```

### Import errors
**Problem**: `ModuleNotFoundError`

**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

## Next Steps

1. **Read the API Documentation**: Open http://localhost:38917/docs
2. **Customize bills**: Edit `example_bill.json` with your data
3. **Integrate with your app**: Use the HTTP API from any language
4. **Read implementation notes**: See `IMPLEMENTATION_NOTES.md` for technical details
5. **Run automated tests**: `python test_api.py`

## Example: Creating a Bill from Python

```python
import requests

bill = {
    "seller_id": "SELLER123",
    "seller_name": "My Store",
    "vt": "FV",  # Facture de vente
    "payments": [{"mode": "E", "amount": 1000.0}],  # E = cash
    "products": [{
        "label": "Product Name",
        "tax": "B",  # B = Taxable
        "price": 1000.0,
        "items": 1.0
    }]
}

response = requests.post(
    "http://localhost:38917/bill",
    json=bill
)

if response.status_code == 200:
    qr_code = response.json()["qr_code"]
    print(f"Bill created: {qr_code}")
else:
    print(f"Error: {response.json()}")
```

## Support

- Check `README.md` for full documentation
- Review `IMPLEMENTATION_NOTES.md` for technical details
- Open an issue on GitHub for bugs or questions
