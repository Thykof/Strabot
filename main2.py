from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn import preprocessing
import pandas
import math
import random
import statistics

X_columns = ['Open*', 'High', 'Low', 'Volume', 'Close**']

def raw_data_to_numeric(raw_data):
    data = raw_data.replace(' ', '')
    data = data.replace(',', '.')
    return float(data)

def main(df, n=500):
    # start = random.randint(0, 1000)
    start = 0
    end = 1000+random.randint(0, 1000)
    end = 500
    df = df.loc[start:end]
    # print('df main')
    # print(df)

    # Ready
    score_total_test = int()
    errors = float()
    for i in range(n):
        Y = df['High']
        Y = Y.drop(index=start)
        X = df[X_columns]
        X = X.drop(index=len(df)-1)
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2)
        algo = linear_model.LinearRegression()
        model = algo.fit(X_train, y_train)
        score_total_test += model.score(X_test, y_test)
        error = float()
        for index, row in df.iterrows():
            p = model.predict([row[X_columns]])
            e = row['High'] - p
            error += float(abs(e))
        errors += error / len(df)

    # print("score")
    print(score_total_test / n) # test
    print('erreur absolue moyenne')
    print(errors / n) # test

    # manual testing:
    # test = {
    #     'Open*': [6161.9, 6127.9, 6675.17],
    #     'High': [6245, 6228.1, 6735.46],
    #     'Low': [5963.8, 5974.7, 6590.96],
    #     'Volume': [16580, 14600, 35319797642],
    #     'Market Cap': [122088327519, 122088327519, 122834375216],
    # } # 26/03 and 27/03
    # # close[]:  6127.9   5748.8   6716.44
    # df_test = pandas.DataFrame(test, columns=X_columns)
    # print(model.predict(df_test))
    return model

def simulate(df, model):
    df = df.loc[:100]
    print('df simulate')
    print(df)
    prix_achats = list()
    prix_ventes = list()
    diffs = list()
    for index, row in df.iterrows():
        # on est au jour n à 23 h 59
        x = row[X_columns]
        # on est au jour n+1 à 00 h 01, donc on a toutes les infos pour prédire
        p = model.predict([x]) # on predit le prix au jour n+1 à 23 h 59
        # on veut prendre une décision au jour n+1 à 00 h 02
        x_decision = row['Close**']
        diff = p - x_decision
        diffs.append(diff)
        if abs(diff) > 10:
            # si le prix evolue de 100 € minimum
            if p < x_decision:
                # vendre
                prix_ventes.append(x_decision)
            else:
                # acheter
                prix_achats.append(x_decision)
    print("nombre d'opérations : " + str(len(prix_achats)) + " " + str(len(prix_ventes)))
    if len(prix_achats) and len(prix_ventes):
        prix_achat_moy = statistics.mean(prix_achats)
        prix_vente_moy = statistics.mean(prix_ventes)
        print('bilan')
        print(prix_achat_moy)
        print(prix_vente_moy)
        print(((prix_vente_moy / prix_achat_moy) - 1) * 100)


if __name__ == '__main__':
    df = pandas.read_csv("bitcoin-price-all.csv", sep=';')
    df = df[['Open*', 'High', 'Low', 'Close**', 'Volume', 'Market Cap']]
    df = df.applymap(raw_data_to_numeric)
    model = main(df, 100)
    """
    0.9919901629881122
    erreur absolue moyenne
    131.29567924891825
"""
    # simulate(df, model)
