import zmq
import time
import json

context = zmq.Context()

socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

socket.send(b"""{"id":1,"type":2,"payload":[]}""")
message = socket.recv()
print(str(message.decode()), flush=True)

socket.send(b"""
{
  "id" : 1,
  "type" : 3,
  "payload" : [
     {"key" : "tx_rate", "val": "25000000"},
     {"key" : "rx_rate", "val": "25000000"},
     {"key" : "tx_bandwidth", "val": "25000000"},
     {"key" : "rx_bandwidth", "val": "25000000"},
     {"key" : "tx_freq", "val": "2500000000"},
     {"key" : "rx_freq", "val": "2500000000"},
     {"key" : "tx_antenna", "val": "TX/RX"},
     {"key" : "rx_antenna", "val": "RX2"},
     {"key" : "rx_sample_per_buffer", "val":  "300000"},
     {"key" : "tx_sample_per_buffer", "val" : "300000"},
     {"key" : "clock_source", "val": "internal"},
     {"key" : "tx_prefix_wave", "val" : "1,20,SINE,20"},
     {"key" : "rx_maximum_samples", "val" : "5200"}
   ]
}""")

# Get the reply.
message = socket.recv()
print(str(message.decode()), flush=True)

for i in range(10):
    socket.send(b"""{
      "id": 2,
      "type": 4,
      "payload": [
        {"key": "task", "val" : "sample_to_file"},
        {"key": "filename", "val" : "/tmp/mysine%d.data"}
       ]
    }""" % (i))

    # Get the reply.
    message = socket.recv()
    print(str(message.decode()), flush=True)

    time.sleep(0.07)

    socket.send(b"""
    {
     "id": 3,
      "type": 4,
      "payload": [
        {"key": "task", "val" : "sample_from_file"},
        {"key": "filename", "val" : "/tmp/mseq.data"}
       ]
    }""")

    # Get the reply.
    message = socket.recv()
    print(str(message.decode()), flush=True)

    time.sleep(0.03)

    socket.send(b"""
    {
      "id": 4,
      "type": 4,
      "payload": [
        {"key": "task", "val" : "shutdown_sample_to_file"}
       ]
    }""")

    # Get the reply.
    message = socket.recv()
    print(str(message.decode()), flush=True)
