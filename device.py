"""
Device communication module for CC300
Implements the Eltrade CC300 protocol for serial communication
"""
import serial
import serial.tools.list_ports
import logging
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

# Constants
SOH = 0x01
AMB = 0x05
ETX = 0x03
BRK = 0x04
LEN_OFFSET = 0x24
MIN_SEQ = 0x20
MAX_SEQ = 0xFF

# Commands
DEV_STATE = 0xC1
NETWORK_STATE = 0xC2
TAXPAYER_INFO = 0x2B
START_BILL = 0xC0
ADD_BILL_ITEM = 0x31
GET_BILL_SUB_TOTAL = 0x33
GET_BILL_TOTAL = 0x35
END_BILL = 0x38

RESPONSE_DELIMITER = 0x2C  # comma

# Device identification
ELTRADE_VID = "03EB"
ELTRADE_PID = "6119"

# Response status codes
NAK = 0x15
SYN = 0x16
OK = 0x01

logger = logging.getLogger(__name__)


def calculate_bcc(data: bytes, length: int) -> bytes:
    """Calculate BCC (Block Check Character) for the message"""
    bcc = 0
    for i in range(1, length):
        bcc ^= data[i]
    return bytes([bcc])


@dataclass
class Request:
    """Represents a request to the CC300 device"""
    cmd: int
    data: bytes = b''
    seq: int = MIN_SEQ
    
    def build(self) -> bytes:
        """Build the request message following CC300 protocol
        Format: <01><LEN><SEQ><CMD><DATA><05><BCC><03>
        """
        # Build payload
        payload = bytes([
            SOH,
            LEN_OFFSET + len(self.data),
            self.seq,
            self.cmd
        ]) + self.data + bytes([AMB])
        
        # Calculate BCC from position 1 to AMB position
        bcc = calculate_bcc(payload, len(payload))
        
        # Complete message
        message = payload + bcc + bytes([ETX])
        
        logger.debug(f"Built request: {message.hex()}")
        return message


@dataclass
class Response:
    """Represents a response from the CC300 device"""
    raw: bytes
    status: int = 0
    
    def parse(self) -> bool:
        """Parse the response message"""
        if len(self.raw) < 1:
            return False
        
        # Clean the response
        cleaned = self._clean(self.raw)
        logger.debug(f"Parsed response: {cleaned.hex()}")
        
        self.status = cleaned[0] if cleaned else 0
        self.raw = cleaned
        return self.status == OK
    
    def _clean(self, data: bytes) -> bytes:
        """Clean the response data"""
        # Remove trailing bytes that aren't ETX
        while len(data) > 1 and data[-1] != ETX:
            data = data[:-1]
        
        # Remove leading bytes that aren't SOH
        while len(data) > 1 and data[0] != SOH:
            data = data[1:]
        
        return data
    
    def get_seq(self) -> Optional[int]:
        """Get sequence number from response"""
        if self.status != OK or len(self.raw) < 4:
            return None
        return self.raw[2]
    
    def get_data(self) -> Optional[str]:
        """Extract data from response"""
        if self.status != OK:
            return None
        
        # Skip SOH, LEN, SEQ, CMD (4 bytes)
        data_start = 4
        data_end = self.raw.find(BRK, data_start)
        
        if data_end == -1:
            return None
        
        data_bytes = self.raw[data_start:data_end]
        return data_bytes.decode('utf-8', errors='ignore')


class Device:
    """Represents a CC300 device connection"""
    
    def __init__(self, port_name: str):
        self.port_name = port_name
        self.serial: Optional[serial.Serial] = None
        self.is_open = False
        self.seq = MIN_SEQ
    
    def open(self) -> bool:
        """Open serial connection to device"""
        try:
            self.serial = serial.Serial(
                port=self.port_name,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
                inter_byte_timeout=0.5
            )
            self.is_open = True
            logger.info(f"Opened device on {self.port_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to open device: {e}")
            return False
    
    def close(self):
        """Close serial connection"""
        if self.serial and self.is_open:
            self.serial.close()
            self.is_open = False
            logger.info("Closed device connection")
    
    def send(self, request: Request) -> Response:
        """Send request and receive response"""
        if not self.is_open or not self.serial:
            return Response(raw=b'', status=-1)
        
        # Update sequence
        request.seq = self.seq
        message = request.build()
        
        # Send request
        self.serial.write(message)
        logger.debug(f"Sent request: {message.hex()}")
        
        # Read response
        response_data = b''
        
        # Handle SYN responses (command takes longer than 100ms)
        max_attempts = 50  # Wait up to 5 seconds
        for _ in range(max_attempts):
            chunk = self.serial.read(256)
            if chunk:
                response_data += chunk
                
                # Check if we have a complete response
                if ETX in chunk:
                    break
        
        response = Response(raw=response_data)
        response.parse()
        
        # Update sequence
        self.seq += 1
        if self.seq > MAX_SEQ:
            self.seq = MIN_SEQ
        
        return response
    
    @staticmethod
    def find_device() -> Optional[str]:
        """Find CC300 device on serial ports"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            vid_str = f"{port.vid:04X}" if port.vid else "N/A"
            pid_str = f"{port.pid:04X}" if port.pid else "N/A"
            logger.debug(f"Found port: {port.device}, VID: {vid_str}, PID: {pid_str}")
            
            # Check if it's an Eltrade device
            if port.vid and port.pid:
                vid_hex = f"{port.vid:04X}"
                pid_hex = f"{port.pid:04X}"
                
                if vid_hex == ELTRADE_VID and pid_hex == ELTRADE_PID:
                    logger.info(f"Found Eltrade CC300 device on {port.device}")
                    return port.device
        
        logger.warning("No Eltrade CC300 device found")
        return None


def open_device() -> Optional[Device]:
    """Open connection to CC300 device"""
    port_name = Device.find_device()
    if not port_name:
        return None
    
    device = Device(port_name)
    if device.open():
        return device
    
    return None
