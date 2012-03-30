
import zephyr.testing
import zephyr.hxm


def callback(message):
    print message


def main():
    zephyr.configure_root_logger()
    
    hxm_handler = zephyr.hxm.HxMMessageParser(callback)
    
    data_dir = zephyr.testing.test_data_dir
    
    try:
        zephyr.testing.simulate_packets_from_file(data_dir + "/120-second-bt-stream-hxm.dat",
                                                  data_dir + "/120-second-bt-stream-hxm-timing.csv",
                                                  hxm_handler.handle_message)
    finally:
        stream_thread.terminate()
        stream_thread.join()


if __name__ == "__main__":
    main()
