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

def train_model(df, n):
    x = df.iloc[:,:n-1]
    y = df.iloc[:,n-1]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)
    algo = linear_model.LinearRegression()
    model = algo.fit(x_train, y_train)
    return model, model.score(x_test, y_test)

def simulate(df, model, m=100, threshold=100):
    """
    Iterate over m first rows and simulate trades.
    Trades only if price move more than the threshold.

    """
    df = df.loc[:m]
    prix_achats = list()
    prix_ventes = list()
    diffs = list()
    for index, row in df.iterrows():
        x = row.head(df.shape[1]-1)
        prediction = model.predict([x])[0]
        x_decision = row.tail(1).to_list()[0]
        if abs(prediction - x_decision) > threshold:
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

def main(n=14, k=500):
    """
    Create row of n days.
    Train and test k models.
    """
    df = pandas.read_csv("bitcoin-price-all.csv", sep=';')
    # df = df.loc[:99]
    df = df[['Close**']]
    df = df.applymap(raw_data_to_numeric)
    new_df_list = list()
    # create rows with n close price, i.e. n days
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

    tot_pnl = int() # total profit and loss
    tot_score = int()
    # train several models
    for i in range(k):
        model, score = train_model(new_df, n)
        tot_pnl += simulate(new_df, model, n)
        tot_score += score
    print(tot_pnl / k) # 5.262569795325347
    print(tot_score / k) # 0.9835991372642395


if __name__ == '__main__':
    main()
