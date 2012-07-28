
import zephyr

from zephyr.message import MessagePayloadParser
from zephyr.testing import TimedVirtualSerial, test_data_dir
from zephyr.hxm import HxMPacketAnalysis
from zephyr.protocol import Protocol


def callback(event_name, event):
    print event_name, event


def main():
    zephyr.configure_root_logger()
    
    ser = TimedVirtualSerial(test_data_dir + "/120-second-bt-stream-hxm.dat",
                             test_data_dir + "/120-second-bt-stream-hxm-timing.csv")
    
    analysis = HxMPacketAnalysis([callback])
    hxm_handler = MessagePayloadParser(analysis.handle_packet)
    protocol = Protocol(ser, hxm_handler.handle_message)
    
    try:
        protocol.run()
    except EOFError:
        pass


if __name__ == "__main__":
    main()
