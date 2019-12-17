import pycom
import utime
import ubinascii
from machine import Pin
from machine import UART

# AT command list
MC60_CMD_AT      = "AT"
MC60_CMD_ATI     = "ATI"
MC60_CMD_ATE     = "ATE0"
MC60_CMD_IFC     = "AT+IFC=0,0"
MC60_CMD_CMGF    = "AT+CMGF=1"
MC60_CMD_QGNSSC  = "AT+QGNSSC=1"
MC60_CMD_QGNSSC_RD  = "AT+QGNSSC?"
MC60_CMD_QGNSSRD_RD = "AT+QGNSSRD?"
MC60_CMD_CGATT   = "AT+CGATT=1"

class MC60():

     # create AT command list as class variables
    AT_command_list = []
    AT_command_list.append(MC60_CMD_AT)
    AT_command_list.append(MC60_CMD_ATI)
    AT_command_list.append(MC60_CMD_ATE)
    AT_command_list.append(MC60_CMD_IFC)
    AT_command_list.append(MC60_CMD_CMGF)
    AT_command_list.append(MC60_CMD_QGNSSC)
    AT_command_list.append(MC60_CMD_QGNSSC_RD)
    AT_command_list.append(MC60_CMD_QGNSSRD_RD)

    def __init__(self, uart_bus=1):
        # Initialize UART periphiral for mc60
        # this init uses the UART_1 default pins for TXD and RXD (``P3`` and ``P4``)
        self.uart = UART(uart_bus)

    def config(self, baud=9600, bits=8, parity=None, stop=1, power_on_pin='P21'):
        self.baud = baud
        self.bits = bits
        self.parity = parity
        self.stop = stop
        self.power_on_pin = power_on_pin

        # Config UART with a given parameters
        self.uart.init(self.baud, bits=self.bits, parity=self.parity, stop=self.stop)

        # Config GPIO for power on pin
        self.pwr_on = Pin(self.power_on_pin, mode=Pin.OUT)
        self.pwr_on.value(0)
    
    def power_on_module(self):
        # Power on the module by using pulse signal (4-5 second)
        self.pwr_on.value(1)
        utime.sleep(5)
        self.pwr_on.value(0)
        utime.sleep(3)
    
    def send_command(self, command=MC60_CMD_AT):
        # Send AT command to the module, if command is correct
        if command in MC60.AT_command_list:
            self.uart.write(command + "\r\n")
            #self._wait_for_ack()

    def wait_for_ack(self, timeout=1000):
        cnt_timeout = 0
        ack_complete = 0
        ack_message = ""
        # Wait for module to acknowlege with message "OK\r\n"
        while ack_complete == 0 and cnt_timeout < timeout:
            if self.uart.any() > 0:
                utime.sleep(0.1)
                cnt_timeout = 0

                # UART readline
                line_bytearray = self.uart.readline()

                if line_bytearray != None:
                    line_str = line_bytearray.decode('utf-8')
                else:
                    line_str = None
                
                if line_str == "OK\r\n":
                    ack_complete = 1
                    print("ACK OK")

                if line_str != None and ack_complete == 0:
                    ack_message = ack_message + line_str + '\n'

            else:
                utime.sleep(0.001)
                cnt_timeout = cnt_timeout + 1

        if cnt_timeout == timeout:
            print("timeout")
            return None
        else:
            return ack_message
    
    def send_AT_command(self, command=MC60_CMD_AT, timeout=2000):
        self.send_command(command=command)
        ack_message = self.wait_for_ack(timeout=timeout)

        return ack_message

    def turn_on_gps(self):
        """
            This function is used to turn on power of gnss (gps) chip in mc60 module
        """
        # Set power supply enable for gps 
        ack_message = self.send_AT_command(command=MC60_CMD_QGNSSC, timeout=2000)
        # Read power supply enable status
        ack_message = self.send_AT_command(command=MC60_CMD_QGNSSC_RD, timeout=2000)
        print(ack_message)

    def get_coordinate(self):
        """
            This function is used to get gps coordinate : latitude, longtitude
            @return : latitude, longtitude
        """
        # Request GPS-NMEA sentence information from gps module
        gnss_message = self.send_AT_command(command=MC60_CMD_QGNSSRD_RD, timeout=2000)

        # Decode NMEA message into latitude & longtitude
        try:
            # Find where is the start index of "gpgll".
            gpgll_startindex = gnss_message.find("$GNGLL,")

            # Crop NMEA message at "gpgll" and split with ','
            gpgll_section = gnss_message[gpgll_startindex : -1]
            gpgll_section = gpgll_section[len("$GNGLL,"): -1]
            gpgll_section_split = gpgll_section.split(',')
            #print(gpgll_section_split)

            # Calculate latitude, longtitude
            latitude_pos  =  float(gpgll_section_split[0])
            longtitude_pos = float(gpgll_section_split[2])
            latitude_sec   = latitude_pos - int(latitude_pos/100)*100
            latitude       = int(latitude_pos/100) + latitude_sec/60
            longtitude_sec = longtitude_pos - int(longtitude_pos/100)*100
            longtitude     = int(longtitude_pos/100) + longtitude_sec/60

            return latitude, longtitude

        except Exception as e:
            print(e)
            print("Maybe GPS is still fixing the position, not ready. Please try again")
            return None, None

    @classmethod
    def add_at_command(cls, new_at_command="AT"):
        """
            This class method is used to add more AT command list by the user.
            Recommend to use with self-aware. (User must know that an added AT command is working)
        """
        cls.AT_command_list.append(new_at_command)