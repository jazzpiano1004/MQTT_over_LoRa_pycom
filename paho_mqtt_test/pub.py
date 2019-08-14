import paho.mqtt.client as mqtt
import time

broker_url = "soldier.cloudmqtt.com"
broker_port = 17431

client = mqtt.Client()
client.username_pw_set(username="aqgomkbt",password="spiYePWJhT2D")
client.connect(broker_url, broker_port, keepalive=60)


topic = "ictscada"
msg = "helloworld"

print("Publishing for every 3 seconds")
while True:
    client.publish(topic=topic, payload=msg, qos=1, retain=False)
    print("Publish")
    time.sleep(3)
