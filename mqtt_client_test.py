
import paho.mqtt.client as mqtt
import time

#####################################################################################
# MQTT Initialize 
mqtt_client = mqtt.Client()
MQTT_SERVER = "192.168.1.11"
MQTT_PORT = 1883

# Callback function after received the mqtt message 
def on_message(mqttc, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    mqtt_sub_msg = msg.payload.decode('ascii')
    topic_dict = mqtt_subscribe_decoding(mqtt_sub_msg)
    print(topic_dict)
    print("\n")
mqtt_client.on_message = on_message

# Callback function after subscribed the mqtt topic 
def sub_callback(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
mqtt_client.on_subscribe = sub_callback
topic = "ICTLab_LoRa/node2"
#####################################################################################


def mqtt_subscribe_decoding(mqtt_sub_message):
    """ This function is used to decode a subscribed message into topic's dictionary which contain all tags of lora device.
        @argument : mqtt_sub_message (mqtt subscribe message)
        @return : topic_dict (dictionary of a given subscribed topic)
    """
    topic_dict = {}
    # Split comma as for each value field in LoRa message
    # split_comma = [( : ), ( : ), ...]
    split_comma = mqtt_sub_message.split(",")
    for i in range(len(split_comma)):
        try:
            # Split colon as for dictionary format within LoRa message
            # split_colon = [key, value]
            split_colon = split_comma[i].split(":")
            key   = split_colon[0]
            value = split_colon[1]

            # Update dictionary of LoRa device
            topic_dict.update({key:value})
        except Exception as e:
            print(e)

    return topic_dict



mqtt_client.connect(host=MQTT_SERVER, port=MQTT_PORT, keepalive=60)
mqtt_client.subscribe(topic=topic, qos=1)
mqtt_client.loop_forever()
