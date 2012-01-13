
import zephyr.message


class Connection:
    def __init__(self, serial_file_object, callback):
        self.ser = serial_file_object
        self.protocol = zephyr.message.MessageFrameParser(callback)
    
    def send_message(self, message_id, payload):
        message_frame = zephyr.message.create_message_frame(message_id, payload)
        self.ser.write(message_frame)
    
    def read_and_handle_bytes(self, num_bytes):
        data_string = self.ser.read(num_bytes)
        self.protocol.parse_data(data_string)
