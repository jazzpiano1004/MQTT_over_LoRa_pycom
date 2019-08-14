import paho.mqtt.client as mqtt

broker_url = "soldier.cloudmqtt.com"
broker_port = 17431

def on_connect(client, userdata, flags, rc):
   print("Connected With Result Code "+str(rc))

# Callback function after received the mqtt message 
def on_message(mqttc, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    print("\n")

# Callback function after subscribed the mqtt topic 
def sub_callback(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

client = mqtt.Client()
client.username_pw_set(username="aqgomkbt",password="spiYePWJhT2D")
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = sub_callback
client.connect(broker_url, broker_port, keepalive=60)

topic = "ictscada"
client.subscribe(topic, qos=1)
client.loop_forever()

# client.loop_start()
# client.loop_stop()
