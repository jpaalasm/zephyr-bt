
import time
import csv
import logging

import zephyr.util


class MessageDataLogger:
    def __init__(self, log_file_basepath):
        self.data_file = file(log_file_basepath + ".dat", "wb")
        self.timing_file = file(log_file_basepath + "-timing.csv", "wb")
        self.timing_file_csv_writer = csv.writer(self.timing_file)
        
        self.start_time = None
        self.time_before = None
    
    def __call__(self, stream_bytes):
        if self.start_time is None:
            now = time.time()
            self.start_time = now
            self.time_before = now
        
        delay = time.time() - self.time_before
        
        relative_previous_chunk_time = self.time_before - self.start_time
        
        data_file_position = self.data_file.tell()
        
        if delay > 0.01 and data_file_position:
            self.timing_file_csv_writer.writerow((relative_previous_chunk_time, data_file_position))
            print relative_previous_chunk_time, data_file_position
        
        self.data_file.write(stream_bytes)
        
        self.time_before = time.time()


class Protocol:
    def __init__(self, connection, callback, log_file_basepath=None):
        self.connection = connection
        self.message_parser = MessageFrameParser(callback)
        
        if log_file_basepath is not None:
            self.message_logger = MessageDataLogger(log_file_basepath)
        else:
            self.message_logger = lambda x: None
    
    def send_message(self, message_id, payload):
        message_frame = create_message_frame(message_id, payload)
        self.connection.write(message_frame)
    
    def read_and_handle_bytes(self, num_bytes):
        data_string = self.connection.read(num_bytes)
        self.message_parser.parse_data(data_string)
        self.message_logger(data_string)
        return data_string
    
    def read_and_handle_forever(self):
        try:
            while True:
                self.read_and_handle_bytes(1)
        except KeyboardInterrupt:
            logging.info("Received Ctrl-C, exiting")


class BioHarnessProtocol(Protocol):
    def enable_ecg_waveform(self):
        self.send_message(0x16, [1])
    
    def enable_breathing_waveform(self):
        self.send_message(0x15, [1])
    
    def enable_rr_data(self):
        self.send_message(0x19, [1])
    
    def enable_accelerometer_waveform(self):
        self.send_message(0x1E, [1])
    
    def set_summary_packet_transmit_interval_to_one_second(self):
        self.send_message(0xBD, [1, 0])
    
    def enable_periodic_packets(self):
        self.enable_ecg_waveform()
        self.enable_breathing_waveform()
        self.enable_rr_data()
        self.enable_accelerometer_waveform()
        self.set_summary_packet_transmit_interval_to_one_second()


def create_message_frame(message_id, payload):
    dlc = len(payload)
    assert 0 <= dlc <= 128
    
    crc_byte = zephyr.util.crc_8_digest(payload)
    
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
        calculated_crc = zephyr.util.crc_8_digest(self.payload)
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
                logging.warning("ProtocolError: %s", e)
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
