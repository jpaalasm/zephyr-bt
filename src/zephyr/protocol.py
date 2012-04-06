
import os
import time
import csv
import logging

import zephyr.message


class MessageDataLogger:
    def __init__(self, log_file_basepath):
        self.data_file = file(log_file_basepath + ".dat", "wb")
        self.timing_file = file(log_file_basepath + "-timing.csv", "wb")
        self.timing_file_csv_writer = csv.writer(self.timing_file)
        
        self.start_time = None
        self.time_before = None
    
    def __call__(self, bytes):
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
        
        self.data_file.write(bytes)
        
        self.time_before = time.time()


class Protocol:
    def __init__(self, connection, callback, log_file_basepath=None):
        self.connection = connection
        self.message_parser = zephyr.message.MessageFrameParser(callback)
        
        if log_file_basepath is not None:
            self.message_logger = MessageDataLogger(log_file_basepath)
        else:
            self.message_logger = lambda x: None
    
    def send_message(self, message_id, payload):
        message_frame = zephyr.message.create_message_frame(message_id, payload)
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
