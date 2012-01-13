
import serial

import zephyr.message
import zephyr.connection


def callback(message):
    print "Message: type %02x, payload %s, eom %s" % (message.message_id, message.payload, message.eom)

def main():
    ser = serial.Serial(23, timeout=0.1)
    
    connection = zephyr.connection.Connection(ser, callback)
    
    connection.send_message(0x15, [1])
    connection.send_message(0x19, [1])
    connection.send_message(0x1E, [1])
    
    while True:
        connection.read_and_handle_bytes(1)


if __name__ == "__main__":
    main()
