from kafka import KafkaConsumer
from kafka import KafkaProducer
import sys
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime

import river
import sys
from sklearn.metrics import mean_absolute_percentage_error
from river import preprocessing, tree, metrics



import river
from river.stream import iter_pandas
from river import metrics
from river import utils

from river import compose
from river import linear_model
from river import time_series
from river import optim
from river import preprocessing

def print_progress(y, y_pred, date, sample_id, training_time, testing_time):
    print(f'Samples processed: {sample_id}')
    print(f'Prevision at {date}')
    print(f'Predicted value : {y_pred:.2f}')
    print(f'Real value : {y}')
    print("total train time:" , training_time)
    print("total testing time:",testing_time)

def evaluate_SNARIMAX(model, h, Y_t, n_iter):
    preds = []
    metric = river.metrics.MAE()
    metric_mape = river.metrics.SMAPE()
    for i in range(n_iter):
        
        y_pred = model.forecast(horizon=10)
        preds.append(y_pred[h-1])
        
        model = model.learn_one(Y_t[i])
        if i > 10:
            m = metric.update(y_pred[h-1], Y_t[i + h]).get()
            m2 = metric_mape.update(y_pred[h-1], Y_t[i + h]).get()

    return metric, metric_mape, preds

topic_name = 'BTCUSDT-1m-clean'

consumer = KafkaConsumer(topic_name, bootstrap_servers="localhost:9092",
                         value_deserializer=lambda m: json.loads(m.decode('utf-8')))
producer = KafkaProducer(bootstrap_servers="localhost:9092", 
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

model = (
    time_series.SNARIMAX(
        p=0,
        d=0,
        q=0,
        m=100,
        sp=100,
        sq=100,
        regressor=(
            preprocessing.StandardScaler() |
            linear_model.LinearRegression(
                intercept_init=110,
                optimizer=optim.SGD(0.01),
                intercept_lr=0.3
            )
        )
    
))
    
# Iteration over the Consumer
for message in consumer:
    list_y = []
    list_ypred = []
    res = json.loads(json.dumps(message.value))
    df = pd.DataFrame(res)
    df = df.set_index('open_time')

    Y_t = df['close'].values
    lst_h_niter = [1, 349, 5, 345, 10, 340]
    lst_h_niter = np.array(lst_h_niter).reshape((3,2))

    for h, n_iter in lst_h_niter:
        m, m2, list_ypred = evaluate_SNARIMAX(model, h, Y_t, n_iter)
        output = {'model': 'SNARIMAX',
                   'yt': Y_t,
                   'y_pred': list_ypred,
                   'm': m,
                   'm2': m2
                  }
        producer.send('model-SNARIMAX-BTCUSDT', output)
        print("Sending message {} to topic: {}".format(output, 'model-SNARIMAX-BTCUSDT'))