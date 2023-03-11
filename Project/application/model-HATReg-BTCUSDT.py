from kafka import KafkaConsumer
from kafka import KafkaProducer
import sys
import time
import json
import pandas as pd
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
from river import optim
from river import preprocessing

def print_progress(y, y_pred, date, sample_id, training_time, testing_time):
    print(f'Samples processed: {sample_id}')
    print(f'Prevision at {date}')
    print(f'Predicted value : {y_pred:.2f}')
    print(f'Real value : {y}')
    print("total train time:" , training_time)
    print("total testing time:",testing_time)

def evaluate(stream, model, verbose = False):

    list_of_trainings = []
    list_of_testings = []
    list_y = []
    list_ypred = []

    training_time = 0
    testing_time = 0
    metric = river.metrics.MAE()    
    metric_mape = river.metrics.SMAPE()

    for i, (x, y) in enumerate(stream):
        # Predict
        start = time.time()
        y_pred = model.predict_one(x)
        end = time.time()
        testing_time = end-start
        list_of_testings.append(testing_time)
        
        # Learn (train)
        start = time.time()
        list_y.append(y)
        list_ypred.append(y_pred)
        m = metric.update(y_pred, y).get()
        m2 = metric_mape.update(y_pred, y).get()
        model.learn_one(x, y)
        end = time.time()
        training_time =  end-start
        list_of_trainings.append(training_time)
        
    # Update metrics and results
    if verbose:
        print_progress(y, y_pred, df.iloc[-1].name,i,sum(list_of_trainings),sum(list_of_testings))
    return y, y_pred, m, m2


topic_name = 'BTCUSDT-1m-clean'

consumer = KafkaConsumer(topic_name, bootstrap_servers="localhost:9092",
                         value_deserializer=lambda m: json.loads(m.decode('utf-8')))
producer = KafkaProducer(bootstrap_servers="localhost:9092", 
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

grace_periods = [10, 100, 200]
model_selector_decays = [0.1, 0.5, 0.9]

for grace_period in grace_periods:
    for model_selector_decay in model_selector_decays:
        
        model = (
            river.preprocessing.StandardScaler() |
            river.tree.HoeffdingAdaptiveTreeRegressor(
                grace_period=grace_period,
                leaf_prediction='adaptive',
                model_selector_decay=model_selector_decay,
                seed=0
            )
        )
        
        list_y = []
        list_ypred = []
    
        # Iteration over the Consumer
        for message in consumer:
            list_y = []
            list_ypred = []
            res = json.loads(json.dumps(message.value))
            df = pd.DataFrame(res)
            df = df.set_index('open_time')
            # Get the 'close' column as the target variable
            for i in range(250):
                y = df[i:100+i].close
                # Get the rest of the columns as the feature variables
                X = df[i:100+i].drop(columns = 'close')

                # Get the predicted and actual values
                y, y_pred, m, m2 = evaluate(stream=iter_pandas(X=X, y=y),
                                  model=model)
                output = {'model': 'HATReg',
                          'grace_period' : grace_period,
                          'model_selector_decay': model_selector_decay,
                           'y': y,
                           'y_pred': y_pred,
                           'm': m,
                           'm2': m2
                          }
                producer.send('model-HATReg-BTCUSDT', output)
                print("Sending message {} to topic: {}".format(output, 'model-HATReg-BTCUSDT'))
                list_y.append(y)
                list_ypred.append(y_pred)
                print(y_pred)