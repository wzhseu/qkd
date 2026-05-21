import json
from enum import IntEnum

class MessageType(IntEnum):
    MT_GUARD_LO = 0
    MT_INVALID  = 1
    MT_PING     = 2
    MT_CONF     = 3
    MT_WORK     = 4
    MT_GUARD_HI = 5

class Message:
    def __init__(self, message_id=0, message_type=MessageType.MT_INVALID,
                 message_payload=[]):
        self._message_id = message_id
        self._message_type = message_type
        self._message_payload = message_payload

    def from_json(json_str):
        parsed_json = json.loads(json_str)
        message_id = parsed_json["id"]
        message_type = parsed_json["type"]
        message_payload = parsed_json["payload"]
        return Message(message_id, message_type, message_payload)

    def to_json(self):
        message_dict = {
            "id": self._message_id,
            "type": self._message_type,
            "payload": self._message_payload,
        }
        return json.dumps(message_dict, separators=(",", ":"))

    def to_bytes(self):
        encoded = self.to_json().encode("utf-8")
        return bytearray(encoded)

PingMessage = Message(1, MessageType.MT_PING, [])
LoadConfigMessage = lambda msg_id, fields : \
    Message(msg_id, MessageType.MT_CONF, [{"key" : x, "val" : ""} for x in fields])
UpdateConfigMessage = lambda msg_id, fields : \
    Message(msg_id, MessageType.MT_CONF, [{"key" : k, "val" : fields[k]} for k in fields])
TaskMessage = lambda msg_id, args : \
    Message(msg_id, MessageType.MT_WORK, [{"key" : k, "val" : args[k]} for k in args])

if __name__ == "__main__":
    invalid_msg = Message(message_type=MessageType.MT_INVALID)
    assert(invalid_msg.to_json() == '{"id":0,"type":1,"payload":[]}')
    ping_msg_json = '{"id":1,"type":2,"payload":[]}'
    ping_msg = Message.from_json(ping_msg_json)
    assert(ping_msg.to_json() == ping_msg_json)
    conf_msg_json = '{"id":1,"type":3,"payload":[{"key":"tx_rate","val":"25000000.000000"},{"key":"rx_rate","val":"25000000.000000"},{"key":"tx_bandwidth","val":"25000000.000000"},{"key":"rx_bandwidth","val":"25000000.000000"},{"key":"tx_freq","val":"2500000000.000000"},{"key":"rx_freq","val":"2500000000.000000"},{"key":"tx_antenna","val":"TX/RX"},{"key":"rx_antenna","val":"RX2"},{"key":"rx_sample_per_buffer","val":"300000"},{"key":"tx_sample_per_buffer","val":"300000"},{"key":"clock_source","val":"internal"},{"key":"tx_prefix_wave","val":"1,20,SINE,20"},{"key":"rx_maximum_samples","val":"5200"}]}'
    conf_msg = Message.from_json(conf_msg_json)
    assert(conf_msg.to_json() == conf_msg_json)
