
import serial

import zephyr.message


def callback(message):
    print "Message: type %02x, payload %s, eom %s" % (message.type, message.bytes, message.eom)

def main():
    ser = serial.Serial(23, timeout=0.1)
    
    protocol = zephyr.message.MessageFrameParser(callback)
    
    while True:
        data_string = ser.read(1)
        protocol.parse_data(data_string)


if __name__ == "__main__":
    main()
