from kafka import KafkaConsumer
from kafka import KafkaProducer
import time
import json
import pandas as pd
from datetime import datetime

topic_name = 'BTCUSDT-1m-raw'
consumer = KafkaConsumer(topic_name, bootstrap_servers="localhost:9092",
                         value_deserializer=lambda m: json.loads(m.decode('utf-8')))
producer = KafkaProducer(bootstrap_servers="localhost:9092", 
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

cols = ['open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'nb_trades',
    'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']

for message in consumer:
    res = json.loads(json.dumps(message.value))
    df = pd.DataFrame(res, columns=cols)
    df = df.astype(float)
    df['open_time'] = df['open_time'].apply(lambda x: datetime.utcfromtimestamp(x/1000).strftime('%Y-%m-%d %H:%M:%S'))
    df_d = df.to_dict()
    producer.send('BTCUSDT-1m-clean', df_d)
    print("Sending message {} to topic: {}".format(df_d, 'BTCUSDT-1m-clean'))
