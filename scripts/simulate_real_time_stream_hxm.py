
import zephyr

from zephyr.message import MessagePayloadParser
from zephyr.testing import FilePacketSimulator, test_data_dir
from zephyr.hxm import HxMPacketAnalysis


def callback(event_name, event):
    print event_name, event


def main():
    zephyr.configure_root_logger()
    
    analysis = HxMPacketAnalysis([callback])
    
    hxm_handler = MessagePayloadParser(analysis.handle_packet)
    
    simulation_thread = FilePacketSimulator(test_data_dir + "/120-second-bt-stream-hxm.dat",
                                            test_data_dir + "/120-second-bt-stream-hxm-timing.csv",
                                            hxm_handler.handle_message)
    
    simulation_thread.start()
    simulation_thread.join()


if __name__ == "__main__":
    main()
