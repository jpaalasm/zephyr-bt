
def crc_8_digest(bytes):
    crc = 0
    
    for byte in bytes:
        crc ^= byte
        for i in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc = (crc >> 1)
    
    return crc


def create_message_frame(message_id, payload):
    dlc = len(payload)
    assert 0 <= dlc <= 128
    
    crc_byte = crc_8_digest(payload)
    
    message_bytes = [0x02, message_id, dlc] + payload + [crc_byte, 0x03]
    
    message_frame = "".join(chr(byte) for byte in message_bytes)
    return message_frame
    


class MessageFrame:
    def __init__(self, message_id):
        self.message_id = message_id
        self.length = None
        self.eom = None
        self.payload = []
    
    def set_length(self, length):
        assert self.length is None
        self.length = length
    
    def set_ack(self, eom):
        assert self.eom is None
        self.eom = eom
    
    def byte_accepted(self):
        return len(self.payload) < self.length
    
    def handle_byte(self, byte):
        self.payload.append(byte)
    
    def get_crc(self):
        calculated_crc = crc_8_digest(self.payload)
        return calculated_crc


class ProtocolError(Exception):
    pass


class MessageFrameParser:
    def __init__(self, callback):
        self.callback = callback
        self.handler = self.handle_stx
        self.message = None
    
    def parse_data(self, data_string):
        for char in data_string:
            byte = ord(char)
            try:
                self.handler(byte)
            except ProtocolError, e:
                print e
                self.handler = self.handle_stx
                self.message = None
    
    def handle_stx(self, byte):
        """Handle the start of message byte. Continue to handling the message id
        if the byte is found."""
        if byte == 0x02:
            self.handler = self.handle_msgid
    
    def handle_msgid(self, byte):
        """Handle the message id. Continue to handling the payload length byte."""
        self.message = MessageFrame(byte)
        self.handler = self.handle_dlc
    
    def handle_dlc(self, byte):
        """Handle the payload length. Continue to handling the payload."""
        payload_length = byte
        
        if not 0 <= payload_length <= 128:
            raise ProtocolError("Incorrect data length")
        
        self.message.set_length(payload_length)
        
        self.handler = self.handle_payload
    
    def handle_payload(self, byte):
        """Handle a payload byte of the CRC byte. Continue to handling the end
        of message byte of another payload byte."""
        if self.message.byte_accepted():
            self.message.handle_byte(byte)
        else:
            calculated_crc = self.message.get_crc()
            
            if byte != calculated_crc:
                raise ProtocolError("CRC does not match")
            
            self.handler = self.handle_eom
    
    def handle_eom(self, byte):
        """Handle the end of message byte. Continue to handling the start
        of message byte."""
        status_dict = {0x03: "ETX", 0x06: "ACK", 0x15: "NAK"}
        status = status_dict.get(byte)
        
        if status is None:
            raise ProtocolError("Invalid ACK byte")
        
        self.message.set_ack(status)
        self.callback(self.message)
        self.message = None
        
        self.handler = self.handle_stx
    
