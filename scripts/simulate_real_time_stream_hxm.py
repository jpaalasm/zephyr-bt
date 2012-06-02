
import zephyr

from zephyr.message import MessagePayloadParser
from zephyr.testing import FilePacketSimulator, test_data_dir


def callback(message):
    print message


def main():
    zephyr.configure_root_logger()
    
    hxm_handler = MessagePayloadParser(callback)
    
    simulation_thread = FilePacketSimulator(test_data_dir + "/120-second-bt-stream-hxm.dat",
                                            test_data_dir + "/120-second-bt-stream-hxm-timing.csv",
                                            hxm_handler.handle_message)
    
    simulation_thread.start()
    simulation_thread.join()
    
    stream_thread.terminate()
    stream_thread.join()


if __name__ == "__main__":
    main()
