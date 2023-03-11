import time
import json 
import requests

from kafka import KafkaProducer


producer = KafkaProducer(bootstrap_servers="localhost:9092", value_serializer=lambda v: json.dumps(v).encode('utf-8'))
topic_name = "BTCUSDT-1m-raw"

request = 'https://api.binance.com/api/v3/klines'
params = dict({
    'symbol':'BTCUSDT',
    'interval':'1m',
    'limit':'600'
})

while True:
    response = requests.get(request, params=params)
    data = response.json()
    print("Sending message {} to topic: {}".format(data, topic_name))
    producer.send(topic_name, data)
    time.sleep(60)
