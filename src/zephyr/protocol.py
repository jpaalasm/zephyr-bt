
import csv
import time
import logging
import threading

import zephyr.util


class MessageDataLogger:
    def __init__(self, log_file_basepath):
        self.data_file = file(log_file_basepath + ".dat", "wb")
        self.timing_file = file(log_file_basepath + "-timing.csv", "wb")
        self.timing_file_csv_writer = csv.writer(self.timing_file)
        
        self.time_before = None
    
    def __call__(self, stream_bytes):
        if self.time_before is None:
            self.time_before = zephyr.time()
        
        delay = zephyr.time() - self.time_before
        
        data_file_position = self.data_file.tell()
        
        if delay > 0.01 and data_file_position:
            self.timing_file_csv_writer.writerow((self.time_before, data_file_position))
            print self.time_before, data_file_position
        
        self.data_file.write(stream_bytes)
        
        self.time_before = zephyr.time()


class Protocol(threading.Thread):
    def __init__(self, connection, callbacks):
        super(Protocol, self).__init__()
        self.connection = connection
        self.callbacks = callbacks
        
        self.initialization_messages = []
        self.terminated = False
    
    def terminate(self):
        self.terminated = True
    
    def add_initilization_message(self, message_id, payload):
        message_frame = create_message_frame(message_id, payload)
        
        try:
            self.connection.write(message_frame)
        except ValueError:
            self.initialization_messages.append(message_frame)
    
    def read_and_handle_byte(self):
        data_string = self.connection.read(1)
        
        timeout_occurred = hasattr(self.connection, "timeout") and not len(data_string)
        
        if timeout_occurred:
            logging.info("Timeout occurred, closing port")
            self.connection.close()
            
            retries = 100
            for retry_i in range(retries):
                if self.terminated:
                    break
                
                try:
                    self.connection.open()
                except Exception as e:
                    logging.info("Re-opening port failed, retry %d (%s)", retry_i, e)
                    time.sleep(1.0)
                    continue
                
                logging.info("Re-opening port successful")
                break
            else:
                raise OSError("Unable to re-open")
        
        for callback in self.callbacks:
            callback(data_string)
        
        return data_string
    
    def run(self):
        for message_frame in self.initialization_messages:
            self.connection.write(message_frame)
        
        while not self.terminated:
            self.read_and_handle_byte()


class BioHarnessProtocol(Protocol):
    def enable_ecg_waveform(self):
        self.add_initilization_message(0x16, [1])
    
    def enable_breathing_waveform(self):
        self.add_initilization_message(0x15, [1])
    
    def enable_rr_data(self):
        self.add_initilization_message(0x19, [1])
    
    def enable_accelerometer_waveform(self):
        self.add_initilization_message(0x1E, [1])
    
    def set_summary_packet_transmit_interval_to_one_second(self):
        self.add_initilization_message(0xBD, [1, 0])
    
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
