import socket
import struct
import ubinascii
import ujson
import time
from network import LoRa
import pycom
import machine
import _thread
from lib.umqtt import MQTTClient



# Dictionary of value for all LoRa devices
dict_node1 = {}
dict_node2 = {}



def lora_dictionary_update(lora_message="", lora_dict={}):
    """ This function is used to update all tags of LoRa node device by using dictionary
        @argument : lora_message (LoRa messgae from node device)
                  : lora_dict (dictionary of node device)
    """
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
MQTT_BROKER_URL = "soldier.cloudmqtt.com"
MQTT_BROKER_PORT = 17487
MQTT_BROKER_USER = "kdkusjvw"
MQTT_BROKER_PWD = "WnrrajsbXpJY"
MQTT_LORAGATEWAY_ID = str(machine.rng())
 
subscribe_complete = 0           # flag for subcribe callback complete
def sub_cb(topic, msg):          # sub_cb means "callback subroutine"
    global subscribe_complete
    print((topic, msg))          # Outputs the message that was received. Debugging use.
    subscribe_complete = 1

client = MQTTClient(client_id=MQTT_LORAGATEWAY_ID, server=MQTT_BROKER_URL, port=MQTT_BROKER_PORT, ssl=False, user=MQTT_BROKER_USER, password=MQTT_BROKER_PWD, keepalive=60)
client.set_callback(sub_cb)
client.connect()



def mqtt_publish_encoding(device_dict, topic_name):
    """ This function is used to publish MQTT message as JSON string by using LoRa node device's dictionary
        @argument : device_dict (dictionary of node device)
                  : topic_name (topic name for mqtt publishing)
    """

    # publish all keys in dictionary with 1 string
    mqtt_topic = "{}".format(topic_name)
    mqtt_msg = ujson.dumps(device_dict)
    
    client.publish(topic=mqtt_topic, msg=mqtt_msg, qos=1, retain=False)
    client.check_msg()



# Initialize lock object for multi-threading
lock = _thread.allocate_lock()


################################################################################################################
# All Threads

def thread_lora_read_package():
    """
        This thread is used for reading a LoRa package from sensor node
    """
    try:
        while True:
            lock.acquire()
            recv_pkg = lora_sock.recv(512)
            lock.release()
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
    finally:
        lock.acquire()
        for i in range(4):
            pycom.rgbled(0x7F0000)
            time.sleep(0.25)
            pycom.rgbled(0x000000)
            time.sleep(0.25)
        lock.release()

def thread_blinking_led():
    """
        This thread is used for blinking LED
    """
    while True:
        pycom.rgbled(0x7F007F)
        time.sleep(0.1)
        pycom.rgbled(0x000000)
        time.sleep(0.4)

def thread_mqtt_publish():
    """
        This thread is used for publishing all LoRa device's Tags via MQTT to MQTT broker
    """
    try:
        while True:
            print("Publishing...")
            mqtt_publish_encoding(dict_node1, "ICTLab_LoRa/node1")
            time.sleep(1)
            mqtt_publish_encoding(dict_node2, "ICTLab_LoRa/node2")
            time.sleep(1)
            print("Publish : DONE")
            time.sleep(3)

    finally:
        client.disconnect()
        print("Disconnected from MQTT server.")

def thread_mqtt_subscribe():
    """
        This thread is used for subscribe all LoRa device's Tags via MQTT to MQTT broker
    """
    global subscribe_complete
    try:
        while True:
            print("Subscribe...")
            # Subscribe
            sub_topic = "ICTLab_LoRa/gateway"
            client.subscribe(sub_topic)
            # Wait until MQTT broker has already sent the subcribed message
            while subscribe_complete == 0:
                time.sleep(0.1)
            subscribe_complete = 0
            print("Subscribe : DONE")
            time.sleep(5)
    
    finally:
        client.disconnect()
        print("Disconnected from MQTT server.")
        
################################################################################################################



# Start all threads
_thread.start_new_thread(thread_blinking_led, ())
_thread.start_new_thread(thread_lora_read_package, ())
_thread.start_new_thread(thread_mqtt_publish, ())
#_thread.start_new_thread(thread_mqtt_subscribe, ())
