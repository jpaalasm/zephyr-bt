
import serial

import zephyr.message
import zephyr.connection


class SignalReceiver:
    def __init__(self):
        pass
    
    def handle_message(self, message):
        print "Message: %02x" % message.message_id
        
        if message.message_id == 0x21:
            self.handle_breathing_payload(message.payload)
    
    def handle_breathing_payload(self, payload):
        assert len(payload) == 32
        
        header = payload[:9]
        signal_bytes = payload[9:]
        
        print "Breathing data:", payload


def callback(message):
    print "Message: type %02x, payload %s, eom %s" % (message.message_id, message.payload, message.eom)

def main():
    signal_receiver = SignalReceiver()
    
    ser = serial.Serial(23, timeout=0.1)
    connection = zephyr.connection.Connection(ser, signal_receiver.handle_message)
    
    connection.send_message(0x15, [1])
    connection.send_message(0x16, [1])
    connection.send_message(0x19, [1])
    connection.send_message(0x1E, [1])
    
    while True:
        connection.read_and_handle_bytes(1)


if __name__ == "__main__":
    main()
