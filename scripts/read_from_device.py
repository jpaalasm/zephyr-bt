
import serial
import platform

import zephyr
from zephyr.testing import simulation_workflow


def callback(value_name, value):
    print value_name, value

def main():
    zephyr.configure_root_logger()
    
    serial_port_dict = {"Darwin": "/dev/cu.BHBHT001931-iSerialPort1",
                        "Windows": 23}
    
    serial_port = serial_port_dict[platform.system()]
    ser = serial.Serial(serial_port)
    
    simulation_workflow([callback], ser)


if __name__ == "__main__":
    main()
