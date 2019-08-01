import socket
import struct
import ubinascii
import time
from network import LoRa
import pycom
import _thread
from lib.umqtt import MQTTClient



# Dictionary of value for all LoRa devices
dict_node1 = {}
dict_node2 = {}

def lora_dictionary_update(lora_message="", lora_dict={}):
    # Split comma as for each value field in LoRa message
    # split_comma = [( : ), ( : ), ...]
    split_comma = lora_message.split(",")
    for i in range(len(split_comma)):
        try:
            # Split colon as for dictionary format within LoRa message
            # split_colon = [key, value]
            split_colon = split_comma[i].split(":")
            key   = split_colon[0]
            value = split_colon[1]

            # Update dictionary of LoRa device
            lora_dict.update({key:value})
        except Exception as e:
            print(e)

            

# Initialise LoRa in LORAWAN mode.
# Asia = LoRa.AS923
# Carrier frequency = 923.8 MHz
# BW = 125kHz
lora = LoRa(mode=LoRa.LORA, region=LoRa.AS923, frequency=923800000, sf=7, bandwidth=LoRa.BW_125KHZ, rx_iq=True)

# Create a raw LoRa socket
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

# LORA package format initialize
# A basic package header, B: 1 byte for the deviceId, B: 1 byte for the pkg size, %ds: Formatted string for string
_LORA_PKG_FORMAT = "!BB%ds"
# A basic ack package, B: 1 byte for the deviceId, B: 1 byte for the pkg size, B: 1 byte for the Ok (200) or error messages
_LORA_PKG_ACK_FORMAT = "BBB"



# MQTT Initialize
MQTT_SERVER = "192.168.1.136"
MQTT_PORT = 1883
MQTT_LORAGATEWAY_ID = str(machine.rng())

def sub_cb(topic, msg):          # sub_cb means "callback subroutine"
    print((topic, msg))          # Outputs the message that was received. Debugging use.

client = MQTTClient(client_id=MQTT_LORAGATEWAY_ID, server=MQTT_SERVER, port=MQTT_PORT, ssl=False)
client.set_callback(sub_cb)
client.connect()
client.subscribe(topic="LoRa_ICTLab", qos=1)

def mqtt_publish_from_dictionary(dict_object, dict_name):
    # message per second for mqtt server that can handle
    mqtt_message_rate = 0.5

    # publish all keys in dictionary
    for key, value in dict_object.items():
        mqtt_topic = "{}/".format(dict_name) + key
        mqtt_msg = value 
        print(mqtt_topic + ": " + mqtt_msg)
        client.publish(topic=mqtt_topic, msg=mqtt_msg, qos=1, retain=False)
        client.check_msg()
        time.sleep(mqtt_message_rate)



# Initialize lock object for multi-threading
lock = _thread.allocate_lock()

# Threads
def thread_lora_read_package():
    while True:
        recv_pkg = lora_sock.recv(512)
        if (len(recv_pkg) > 2):
            # Extract information from lora message
            recv_pkg_len = recv_pkg[1]
            device_id, pkg_len, msg = struct.unpack(_LORA_PKG_FORMAT % recv_pkg_len, recv_pkg)
            msg = msg.decode('utf-8')
            
            # Check whoose package was? By using device ID
            if device_id == 0x01:
                lora_dictionary_update(lora_message=msg, lora_dict=dict_node1)
            elif device_id == 0x02:
                lora_dictionary_update(lora_message=msg, lora_dict=dict_node2)

            # Send ACK
            ack_pkg = struct.pack(_LORA_PKG_ACK_FORMAT, device_id, 1, 200)
            lora_sock.send(ack_pkg)

def thread_blinking_led():
    while True:
        pycom.rgbled(0x7F007F)
        time.sleep(0.1)
        pycom.rgbled(0x000000)
        time.sleep(0.4)

def thread_mqtt_publish():
    try:
        while True:
            print("Publishing...")
            mqtt_publish_from_dictionary(dict_node1, "node1")
            mqtt_publish_from_dictionary(dict_node2, "node2")
            print("DONE")
            #client.check_msg()
            time.sleep(5)
    finally:
        client.disconnect()
        print("Disconnected from MQTT server.") 



# Start all threads
_thread.start_new_thread(thread_blinking_led, ())
_thread.start_new_thread(thread_lora_read_package, ())
_thread.start_new_thread(thread_mqtt_publish, ())
