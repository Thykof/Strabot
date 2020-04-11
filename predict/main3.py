from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn import preprocessing
import pandas
import numpy
import math
import random
import statistics

def raw_data_to_numeric(raw_data):
    data = raw_data.replace(' ', '')
    data = data.replace(',', '.')
    return float(data)

def train(df, n):
    x = df.iloc[:,:n-1]
    y = df.iloc[:,n-1]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)
    algo = linear_model.LinearRegression()
    model = algo.fit(x_train, y_train)
    return model


def simulate(df, model, n):
    df = df.loc[:100]
    prix_achats = list()
    prix_ventes = list()
    diffs = list()
    for index, row in df.iterrows():
        x = row.head(n-1)
        prediction = model.predict([x])[0] # on predit le prix au jour n+1 à 23 h 59
        x_decision = row.tail(1).to_list()[0]
        if abs(prediction - x_decision) > 100:
            if prediction > x_decision:
                # buy
                prix_achats.append(x_decision)
                prix_ventes.append(prediction)
            else:
                prix_achats.append(prediction)
                prix_ventes.append(x_decision)
    if len(prix_achats) and len(prix_ventes):
        prix_achat_moy = statistics.mean(prix_achats)
        prix_vente_moy = statistics.mean(prix_ventes)
        return (((prix_vente_moy / prix_achat_moy) - 1) * 100)

if __name__ == '__main__':
    df = pandas.read_csv("bitcoin-price-all.csv", sep=';')
    # df = df.loc[:99]
    df = df[['Close**']]
    df = df.applymap(raw_data_to_numeric)
    new_df_list = list()
    n = 14
    for label, content in df.items():
        row = list()
        i = 0
        for item in content:
            row.append(item)
            i += 1
            if i >= n:
                new_df_list.append(row)
                row = list()
                i = 0
    new_df = pandas.DataFrame(new_df_list)
    print(new_df)

    tot = int()
    for i in range(100):
        model = train(new_df, n)
        tot += simulate(new_df, model, n)
    print(tot / 100) # 5.985384977627953
