import time
import logging
from typing import Optional, List, Tuple
import serial
import serial.tools.list_ports


logger = logging.getLogger("cc300.device")


# Protocol constants from the reference implementation
SOH = 0x01
AMB = 0x05
ETX = 0x03
BRK = 0x04
LEN_OFFSET = 0x24
MIN_SEQ = 0x20
MAX_SEQ = 0xFF
SYN = 0x16  # Used for wait responses

# Command codes
CMD_DEV_STATE = 0xC1
CMD_NETWORK_STATE = 0xC2
CMD_TAXPAYER_INFO = 0x2B
CMD_START_BILL = 0xC0
CMD_ADD_BILL_ITEM = 0x31
CMD_GET_BILL_SUB_TOTAL = 0x33
CMD_GET_BILL_TOTAL = 0x35
CMD_END_BILL = 0x38

# Device identification
ELTRADE_VID = 0x03EB
ELTRADE_PID = 0x6119

RESPONSE_DELIMITER = ','
CMD_PROCESSING_TIME = 0.1  # 100ms


class Request:
    """Represents a request to the CC300 device"""
    
    def __init__(self, cmd: int):
        self.cmd = cmd
        self.data = b""
        self.seq = MIN_SEQ
    
    def set_body(self, data: str):
        """Set the request body/data"""
        self.data = data.encode('latin-1')
        return self
    
    def build(self) -> bytes:
        """Build the complete request packet"""
        # Calculate length: from after LEN to ETX inclusive, plus offset
        data_len = len(self.data)
        length = 1 + 1 + data_len + 2 + 1 + 1  # SEQ + CMD + DATA + BCC + ETX + offset
        length_byte = (length + LEN_OFFSET) & 0xFF
        
        # Build packet without BCC first
        packet = bytearray([SOH, length_byte, self.seq, self.cmd])
        packet.extend(self.data)
        packet.append(ETX)
        
        # Calculate BCC (checksum): XOR of all bytes from SEQ to ETX (inclusive)
        bcc = 0
        for i in range(2, len(packet)):  # Start from SEQ (index 2)
            bcc ^= packet[i]
        
        packet.append(bcc)
        packet.append(AMB)
        
        return bytes(packet)


class Response:
    """Represents a response from the CC300 device"""
    
    def __init__(self):
        self.raw_data = b""
        self.seq = 0
        self.cmd = 0
        self.data = b""
        self.status = "INVALID"
    
    def parse(self, raw_data: bytes):
        """Parse raw response data"""
        self.raw_data = raw_data
        
        if len(raw_data) < 6:  # Minimum packet size
            self.status = "INVALID"
            return
        
        # Check for SOH
        if raw_data[0] != SOH:
            self.status = "INVALID"
            return
        
        # Extract fields
        self.seq = raw_data[2]
        self.cmd = raw_data[3]
        
        # Find ETX position
        try:
            etx_pos = raw_data.index(ETX, 4)
        except ValueError:
            self.status = "INVALID"
            return
        
        # Extract data between CMD and ETX
        if etx_pos > 4:
            self.data = raw_data[4:etx_pos]
        
        self.status = "OK"
    
    def get_seq(self) -> int:
        """Get the sequence number"""
        return self.seq
    
    def get_data(self) -> str:
        """Get the data as string"""
        if self.status != "OK":
            raise Exception("Invalid response")
        return self.data.decode('latin-1', errors='ignore')


class CC300Device:
    """CC300 Device communication handler"""
    
    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.is_open = False
        self.current_seq = MIN_SEQ
    
    def _find_device_port(self) -> Optional[str]:
        """Find the CC300 device port by VID/PID"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            logger.debug(f"Found port: {port.device}, VID: {port.vid:04X}, PID: {port.pid:04X}")
            if port.vid == ELTRADE_VID and port.pid == ELTRADE_PID:
                logger.info(f"Matched CC300 device on port: {port.device}")
                return port.device
        
        return None
    
    def open(self) -> bool:
        """Open connection to the device"""
        try:
            port_name = self._find_device_port()
            if not port_name:
                logger.error("CC300 device not found on any serial port")
                return False
            
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
                inter_byte_timeout=0.5
            )
            
            self.is_open = True
            logger.info(f"Successfully opened CC300 device on {port_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open device: {e}")
            self.is_open = False
            return False
    
    def close(self):
        """Close the device connection"""
        if self.serial_port and self.is_open:
            self.serial_port.close()
            self.is_open = False
            logger.debug("Device closed")
    
    def _next_seq(self) -> int:
        """Get next sequence number"""
        self.current_seq += 1
        if self.current_seq > MAX_SEQ:
            self.current_seq = MIN_SEQ
        return self.current_seq
    
    def send(self, request: Request) -> Response:
        """Send a request and receive response"""
        if not self.is_open or not self.serial_port:
            raise Exception("Device not open")
        
        # Set sequence number
        request.seq = self._next_seq()
        
        # Send request
        packet = request.build()
        logger.debug(f"Sending: {packet.hex()}")
        self.serial_port.write(packet)
        
        # Read response
        response = Response()
        raw_buffer = bytearray()
        
        # Wait for response, handling SYN (wait) messages
        max_attempts = 100
        attempts = 0
        
        while attempts < max_attempts:
            try:
                # Read available data
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    raw_buffer.extend(data)
                    logger.debug(f"Received {len(data)} bytes: {data.hex()}")
                    
                    # Check if we have a complete response
                    if len(raw_buffer) >= 6:
                        response.parse(bytes(raw_buffer))
                        
                        # Check if it's a SYN (wait) message
                        if response.get_seq() == SYN:
                            logger.debug("Received SYN, waiting for actual response...")
                            raw_buffer.clear()
                            time.sleep(CMD_PROCESSING_TIME)
                            attempts += 1
                            continue
                        
                        # Valid response
                        if response.status == "OK":
                            return response
                
                time.sleep(0.01)
                attempts += 1
                
            except Exception as e:
                logger.error(f"Error reading response: {e}")
                break
        
        raise Exception("Timeout waiting for device response")
    
    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
