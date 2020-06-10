import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn import neural_network
from sklearn import metrics

TIME = 'time'
OPEN = 'open'
HIGH = 'high'
LOW = 'low'
CLOSE = 'close'
VWAP = 'vwap'
VOLUME = 'volume'
COUNT = 'count'

# Open the dataset
df = pd.read_csv("ohlc-btc-eur-day.csv")

# Select columns
df_num = df[[OPEN, HIGH, LOW, CLOSE, VOLUME]]

# Scale data
scaler = preprocessing.StandardScaler()
df_norm = pd.DataFrame(scaler.fit_transform(df_num.values), columns=df_num.columns, index=df_num.index)
#print((df_num[OPEN] - np.mean(df_num[OPEN])) / np.std(df_num[OPEN]))
#print(df_norm)

# Unscale data
a_close_price = 0.95
the_unsacled_close_prices = a_close_price * np.std(df_num[CLOSE]) + np.mean(df_num[OPEN])
#print(the_unsacled_close_prices)

# Define variables
delta = 7
X = df_norm.iloc[:-delta,:]
y = df_norm[CLOSE].iloc[delta:]

# Evaluate model
model = neural_network.MLPRegressor(hidden_layer_sizes=(100,),
                                    activation='relu',
                                    solver='lbfgs',
                                    alpha=1
                                   )
cross = cross_val_score(model, X, y, cv=10, scoring='neg_mean_absolute_error')
print(cross, np.mean(cross), np.median(cross))

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y)
model.fit(X_train, y_train)
print(metrics.mean_absolute_error(y_test, model.predict(X_test)))
