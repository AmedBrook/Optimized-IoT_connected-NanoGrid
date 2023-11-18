import paho.mqtt.client as mqtt #importing the client 
import time #importing time 
import access_key
from datetime import datetime
from queue import Queue
import json
import heo

# Getting the current date and time
q=Queue()
####

username= access_key.username
password= access_key.password

sub_topic = 'open/meteoria/airTemp'
meseaure = 'Temperature'
unit = 'Deg C'

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(sub_topic)


data_stream, strg = [], []
def on_message(client, userdata, message): 
    
    global data_stream, strg

    
    if len(data_stream) < 4:    
       i=0
       while i < 1 : 
            log = json.loads(message.payload.decode("utf-8"))
            data_stream.append(log) 
            i=i+1 
            if len(data_stream) == 4: 
                strg=data_stream
                print('returned list', strg)
                heo.Optim.solve()
    else : 
        data_stream = []
        i=0
        while i < 1 : 
            log = json.loads(message.payload.decode("utf-8"))
            data_stream.append(log) 
            i=i+1 
            if len(data_stream) == 4: 
                strg=data_stream
                print('returned list:', strg)
                heo.Optim.solve()

    print('#######', meseaure, ':',str(message.payload.decode('utf-8')),unit,'#######')
    print('=======', str(datetime.now()), '=======')
    print('message topic is : ',message.topic)
    print('message qos is : ', message.qos)
    print('mesaage retain flag = ', message.retain)
    q.put(message)
    print('data_stream:',data_stream)


def on_log(client, userdata, level, buf):
    print("log: ",buf)


while not q.empty():
   message = q.get()
   if message is None:
       continue
   print("received from queue",str(message.payload.decode("utf-8")))


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
print("Subscribing to topic", sub_topic)
client.subscribe(sub_topic)
print('returned list:', strg)


def publish(client):
    msg = 0
    pub_topic = 'meteoria/optimizer/gensetControl'
    while True:
        time.sleep(1)
        result = client.publish(pub_topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{pub_topic}`")
        else:
            print(f"Failed to send message to topic {pub_topic}")



def run():
    publish(client)


if __name__ == '__main__':
    run()