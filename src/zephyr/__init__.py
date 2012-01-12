
import serial


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


class MessageHandler:
    def __init__(self, message_type):
        self.type = message_type
        self.length = None
        self.ack = None
        self.bytes = []
    
    def set_length(self, length):
        assert self.length is None
        self.length = length
    
    def set_ack(self, ack):
        assert self.ack is None
        self.ack = ack
    
    def byte_accepted(self):
        return len(self.bytes) < self.length
    
    def handle_byte(self, byte):
        self.bytes.append(byte)
    
    def get_crc(self):
        calculated_crc = crc_8_digest(self.bytes)
        return calculated_crc


class ProtocolError(Exception):
    pass


class Protocol:
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
        if byte == 0x02:
            self.handler = self.handle_msgid
    
    def handle_msgid(self, byte):
        self.message = MessageHandler(byte)
        self.handler = self.handle_dlc
    
    def handle_dlc(self, byte):
        payload_length = byte
        
        if not 0 <= payload_length <= 128:
            raise ProtocolError("Incorrect data length")
        
        self.message.set_length(payload_length)
        
        self.handler = self.handle_payload
    
    def handle_ack(self, byte):
        status_dict = {0x03: "ETX", 0x06: "ACK", 0x15: "NAK"}
        status = status_dict.get(byte)
        
        if status is None:
            raise ProtocolError("Invalid ACK byte")
        
        self.message.set_ack(status)
        self.callback(self.message)
        self.message = None
        
        self.handler = self.handle_stx
    
    def handle_payload(self, byte):
        if self.message.byte_accepted():
            self.message.handle_byte(byte)
        else:
            calculated_crc = self.message.get_crc()
            
            if byte != calculated_crc:
                raise ProtocolError("Error in CRC")
            
            self.handler = self.handle_ack


def callback(message):
    print "Message: type %02x, payload %s, ack %s" % (message.type, message.bytes, message.ack)


def main():
    ser = serial.Serial(23, timeout=1.0)
    
    protocol = Protocol(callback)
    
    while True:
        data_string = ser.read(1)
        protocol.parse_data(data_string)


if __name__ == "__main__":
    main()
