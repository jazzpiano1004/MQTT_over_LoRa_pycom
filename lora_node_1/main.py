import os
import socket
import time
import struct
from network import LoRa
import pycom
import _thread

# Node use Yellow LED
pycom.heartbeat(False)

# User global variable
sensor1_value = 0
sensor2_value = 0
sensor3_value = 0

# Initialise LoRa in LORAWAN mode.
# Open a Lora Socket, use tx_iq to avoid listening to our own messages
# Asia = LoRa.AS923
# Carrier frequency = 923.8 MHz
# BW = 125kHz
lora = LoRa(mode=LoRa.LORA, region=LoRa.AS923, frequency=923800000, bandwidth=LoRa.BW_125KHZ, tx_iq=True)
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

# LORA Package Initialize
# A basic package header, B: 1 byte for the deviceId, B: 1 byte for the pkg size
_LORA_PKG_FORMAT = "BB%ds"
_LORA_PKG_ACK_FORMAT = "BBB"
DEVICE_ID = 0x01
   
# Initialize for multi-threading
lock = _thread.allocate_lock()

def thread_lora_send_package():
    global sensor1_value
    global sensor2_value
    global sensor3_value
    while True:
        # Package send containing a simple string
        msg = ""
        msg = msg + "sensor1:{}".format(sensor1_value) + ","
        msg = msg + "sensor2:{}".format(sensor2_value) + ","
        msg = msg + "sensor3:{}".format(sensor3_value)  
        pkg = struct.pack(_LORA_PKG_FORMAT % len(msg), DEVICE_ID, len(msg), msg)
        lock.acquire()
        lora_sock.send(pkg)
        lock.release()

        # Wait for the response from the gateway. NOTE: For this demo the device does an infinite loop for while waiting the response. Introduce a max_time_waiting for you application
        waiting_ack = True
        timeout_tick = 0
        while(waiting_ack):
            lock.acquire()
            recv_ack = lora_sock.recv(256)
            lock.release()
            if (len(recv_ack) > 0):
                device_id, pkg_len, ack = struct.unpack(_LORA_PKG_ACK_FORMAT, recv_ack)
                if (device_id == DEVICE_ID):
                    if (ack == 200):
                        waiting_ack = False
                        # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                        lock.acquire()
                        print("ACK")
                        lock.release()
                    else:
                        waiting_ack = False
                        # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                        lock.acquire()
                        print("Message Failed")
                        lock.release()

            # tick for timeout 
            timeout_tick = timeout_tick + 1
            time.sleep(0.1)

            if timeout_tick > 50:
                lock.acquire()
                print("Timeout for ACK, No response from station")
                lock.release()
                waiting_ack = False
        # thread delay
        time.sleep(1)

def thread_blinking_led():
    while True:
        pycom.rgbled(0x7F7F00) # Yellow LED
        time.sleep(0.1)
        pycom.rgbled(0x000000) # Yellow LED
        time.sleep(0.9)



def thread_read_sensor():
    global sensor1_value
    global sensor2_value
    global sensor3_value
    while True:
        # Read sensor value
        # This is not the actual sensor, the value is simulated by number generator.
        sensor1_value = 1
        time.sleep(0.01)
        sensor2_value = 2
        time.sleep(0.01)
        sensor3_value = 3
        time.sleep(1)



# Start all threads
_thread.start_new_thread(thread_blinking_led, ())
_thread.start_new_thread(thread_lora_send_package, ())
_thread.start_new_thread(thread_read_sensor, ())
