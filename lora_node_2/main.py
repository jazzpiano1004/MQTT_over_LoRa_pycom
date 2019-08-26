import os
import socket
import time
import struct
from network import LoRa
import pycom
import _thread
from pytrack  import Pytrack
from lib.L76GNSS  import L76GNSS
from lib.LIS2HH12 import LIS2HH12



# Node use Yellow LED
pycom.heartbeat(False)

# Pytrack & GPS (GNSS) + Accelerometer object
py = Pytrack()
acc = LIS2HH12()
gps = L76GNSS(py, timeout=30)
# accelerometer from PyTrack
acc_x = 0
acc_y = 0
acc_z = 0
acc_x_delay1 = 0
acc_y_delay1 = 0
acc_z_delay1 = 0
# Smoothing function for accelerometer value
def smoothing_filter_iir(x=0, y_delay=0):
    a = 0.8 # smoothing factor
    y = a*x + (1 - a)*y_delay
    return y

# GPS coordinate from PyTrack
gps_latitude = None
gps_longtitude = None

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
DEVICE_ID = 0x02
   
# Initialize for multi-threading
lock = _thread.allocate_lock()

def thread_lora_send_package():
    global acc_pitch
    global acc_roll
    global gps_latitude
    global gps_longtitude

    time.sleep(5)
    while True:
        # Package send containing a simple string
        msg = ""
        msg = msg + "acc_x:{}".format(acc_x) + ","
        msg = msg + "acc_y:{}".format(acc_y) + ","
        msg = msg + "acc_z:{}".format(acc_z) + ","
        msg = msg + "gps_latitude:{}".format(gps_latitude) + ","
        msg = msg + "gps_longtitude:{}".format(gps_longtitude)
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
        for i in range(2):
            pycom.rgbled(0x7F7F00) # Yellow LED
            time.sleep(0.1)
            pycom.rgbled(0x000000) # Yellow LED
            time.sleep(0.1)
        
        time.sleep(0.6)

def thread_read_accelerometer():
    global acc_x
    global acc_y
    global acc_z
    global acc_x_delay1
    global acc_y_delay1
    global acc_z_delay1

    while True:
        # Read acceleration of x, y, z axis
        acc_x, acc_y, acc_z = acc.acceleration()

        # Low-pass filter using IIR filter
        acc_x = smoothing_filter_iir(x=acc_x, y_delay=acc_x_delay1)
        acc_x_delay1 = acc_x
        acc_y = smoothing_filter_iir(x=acc_y, y_delay=acc_y_delay1)
        acc_y_delay1 = acc_y
        acc_z = smoothing_filter_iir(x=acc_z, y_delay=acc_z_delay1)
        acc_z_delay1 = acc_z

        lock.acquire()
        print("x={}, y={}, z={}".format(acc_x, acc_y, acc_z))
        lock.release()
        time.sleep(0.1)

def thread_read_gps():
    while True:
        lock.acquire()
        gps_latitude, gps_longtitude = gps.coordinates()
        print(gps_latitude, gps_longtitude)
        lock.release()
        time.sleep(5)

# Start all threads
_thread.start_new_thread(thread_blinking_led, ())
_thread.start_new_thread(thread_read_accelerometer, ())
_thread.start_new_thread(thread_read_gps, ())
_thread.start_new_thread(thread_lora_send_package, ())