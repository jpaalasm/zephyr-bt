
class SignalReceiver:
    def __init__(self):
        pass
    
    def handle_message(self, message):
        print "Message: %02x" % message.message_id
        
        if message.message_id == 0x21:
            self.handle_breathing_payload(message.payload)
    
    def handle_breathing_payload(self, payload):
        assert len(payload) == 32
        
        header = payload[:9]
        signal_bytes = payload[9:]
        
        print "Breathing data:", payload
