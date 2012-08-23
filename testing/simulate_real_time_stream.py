
import zephyr
from zephyr.testing import test_data_dir, TimedVirtualSerial, simulation_workflow


def callback(value_name, value):
    print value_name, value

def main():
    zephyr.configure_root_logger()
    
    ser = TimedVirtualSerial(test_data_dir + "/120-second-bt-stream.dat",
                             test_data_dir + "/120-second-bt-stream-timing.csv")
    
    simulation_workflow([callback], ser)


if __name__ == "__main__":
    main()
