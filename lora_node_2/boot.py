import machine
import uos


uart = machine.UART(0, 115200)
uos.dupterm(uart)



