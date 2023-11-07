import paho.mqtt.client as mqtt #importing the client 
import time #importing time 
import access_key

####

username= access_key.username
password= access_key.password


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("open/meteoria/solarRadiation")

def on_message(client, userdata, message): 
    print('message received', str(message.payload.decode('utf-8')))
    print('message topic is : ',message.topic)
    print('message qos is : ', message.qos)
    print('mesaage retain flag = ', message.retain)

def on_log(client, userdata, level, buf):
    print("log: ",buf)

###

broker_address='iot.novia.fi'
print('Creating new instance of the client')
client=mqtt.Client() 
client.on_message=on_message #attach function to callback
print("connecting to broker")

client.on_connect = on_connect
client.username_pw_set(username, password)
client.connect(broker_address, 1883, 60)
time.sleep(4) # wait
client.loop_stop() #stop the loop

client.loop_start() #start the loop
client.on_log=on_log #printing log information
print("Subscribing to topic","open/meteoria/solarRadiation")
client.subscribe("open/meteoria/solarRadiation")





