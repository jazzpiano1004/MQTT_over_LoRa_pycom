import paho.mqtt.client as mqtt
from random import randint
import time

broker_url = "localhost"
broker_port = 1883

client = mqtt.Client()
client.connect(broker_url, broker_port)

x = "001,ABCDEFGHIJKLMNO,3,H,20181122,095030,01,0000000,0000000,55.48,30.13,75.54,0,E,15.5,25,18.5,OK,#"
temp = randint(2400,2600)/100
hummi = randint(45,60)
dust = randint(2400,2600)/100
while True:#for i in range(100):
    current = randint(1000,2500)/100
    volt = randint(2000,5000)/100
    power = current*volt*0.1
    temp += randint(-100,100)/100
    hummi += randint(-1,1)
    dust += randint(-100,100)/100
    x = "001,ABCDEFGHIJKLMNO,3,H,20181122,095030,01,0000000,0000000,"
    x += format(current, '02f') + ","
    x += format(volt, '02f') + ","
    x += format(power, '02f') + ","
    x += "0,E,"
    x += format(temp, '02f') + ","
    x += str(hummi) + ","
    x += format(dust, '02f') + ","
    x += "OK,#"


    client.publish(topic="AbotRobot_1", payload=x, qos=1, retain=False)

    time.sleep(3)
