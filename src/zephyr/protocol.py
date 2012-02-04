
import zephyr.message


class Protocol:
    def __init__(self, connection, callback):
        self.connection = connection
        self.message_parser = zephyr.message.MessageFrameParser(callback)
    
    def send_message(self, message_id, payload):
        message_frame = zephyr.message.create_message_frame(message_id, payload)
        self.connection.write(message_frame)
    
    def read_and_handle_bytes(self, num_bytes):
        data_string = self.connection.read(num_bytes)
        self.message_parser.parse_data(data_string)
        
        nbytes_read = len(data_string)
        return nbytes_read
    
    def read_and_handle_forever(self):
        try:
            while True:
                self.read_and_handle_bytes(1)
        except KeyboardInterrupt:
            print "Received Ctrl-C, exiting"
    
    def enable_signals(self):
        self.send_message(0x15, [1])
        self.send_message(0x16, [1])
        self.send_message(0x19, [1])
        self.send_message(0x1E, [1])
